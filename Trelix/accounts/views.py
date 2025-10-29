from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .forms import SignUpForm, ProfileCompletionForm, TOTPVerificationForm, BackupCodeForm
from .models import Profile, TrustedDevice
from .utils import (
    setup_2fa, generate_totp_secret, get_totp_uri, verify_totp_token,
    validate_backup_code, reset_backup_codes, disable_2fa,
    generate_device_key, is_device_trusted, trust_device, download_backup_codes,
    generate_backup_codes
)
import requests
import os
import secrets
import pyotp
import qrcode
import io
from urllib.parse import urlencode

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Redirect to profile completion page
            return redirect('accounts:profile_completion')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def signin_view(request):
    if request.user.is_authenticated:
        # If already authenticated but has 2FA session data, clear it
        if '2fa_user_id' in request.session:
            request.session.pop('2fa_user_id', None)
        return redirect('home')
    
    # Check if user is in 2FA step
    if '2fa_user_id' in request.session:
        return redirect('accounts:verify_2fa')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Check if "remember me" was selected
            remember_me = request.POST.get('remember', False)
            
            # Check if user has 2FA enabled
            try:
                profile = user.profile
                if profile.two_step_verification:
                    # Generate device key for trusted device check
                    device_key = generate_device_key(
                        request.META.get('HTTP_USER_AGENT', ''),
                        request.META.get('REMOTE_ADDR', '')
                    )
                    
                    # Check if device is already trusted - if so, skip 2FA
                    if is_device_trusted(user, device_key):
                        login(request, user)
                        messages.success(request, 'Logged in successfully from trusted device')
                        return redirect('home')
                    
                    # Device not trusted, require 2FA verification first
                    # Store remember_me preference - device will only be trusted AFTER successful verification
                    request.session['2fa_user_id'] = user.id
                    request.session['remember_device'] = remember_me
                    return redirect('accounts:verify_2fa')
            except Profile.DoesNotExist:
                pass
            
            # No 2FA, log in directly
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/signin.html', {'form': form})


def verify_2fa_view(request):
    """Handle 2FA verification after initial login"""
    # If user is already authenticated, clear any stale 2FA data and go to home
    if request.user.is_authenticated:
        request.session.pop('2fa_user_id', None)
        return redirect('home')
    
    # Check if user is in 2FA flow
    if '2fa_user_id' not in request.session:
        return redirect('accounts:signin')
    
    try:
        user = User.objects.get(id=request.session['2fa_user_id'])
        profile = user.profile
    except (User.DoesNotExist, Profile.DoesNotExist):
        request.session.pop('2fa_user_id', None)
        return redirect('accounts:signin')
    
    use_backup_code = request.GET.get('backup_code', 'false') == 'true'
    
    if request.method == 'POST':
        if use_backup_code:
            form = BackupCodeForm(request.POST)
            if form.is_valid():
                code = form.cleaned_data['code']
                if validate_backup_code(profile, code):
                    # Backup code valid, log in
                    request.session.pop('2fa_user_id', None)
                    
                    # Trust device ONLY after successful verification
                    # If remember_me was checked, add device as trusted
                    if request.session.get('remember_device'):
                        device_key = generate_device_key(
                            request.META.get('HTTP_USER_AGENT', ''),
                            request.META.get('REMOTE_ADDR', '')
                        )
                        trust_device(user, device_key, request.META.get('HTTP_USER_AGENT', ''))
                    
                    request.session.pop('remember_device', None)
                    login(request, user)
                    messages.success(request, 'Logged in successfully using backup code')
                    return redirect('home')
                else:
                    form.add_error('code', 'Invalid or already used backup code')
        else:
            form = TOTPVerificationForm(request.POST)
            if form.is_valid():
                token = form.cleaned_data['token']
                if verify_totp_token(profile.otp_secret, token):
                    # TOTP valid, log in
                    request.session.pop('2fa_user_id', None)
                    
                    # Trust device ONLY after successful verification
                    # If remember_me was checked, add device as trusted
                    if request.session.get('remember_device'):
                        device_key = generate_device_key(
                            request.META.get('HTTP_USER_AGENT', ''),
                            request.META.get('REMOTE_ADDR', '')
                        )
                        trust_device(user, device_key, request.META.get('HTTP_USER_AGENT', ''))
                    
                    request.session.pop('remember_device', None)
                    login(request, user)
                    messages.success(request, 'Logged in successfully')
                    return redirect('home')
                else:
                    form.add_error('token', 'Invalid authentication code')
    else:
        form = BackupCodeForm() if use_backup_code else TOTPVerificationForm()
    
    context = {
        'form': form,
        'use_backup_code': use_backup_code,
    }
    return render(request, 'accounts/verify_2fa.html', context)

@login_required(login_url='accounts:signin')
def signout_view(request):
    # Clear 2FA session data
    request.session.pop('2fa_user_id', None)
    request.session.pop('2fa_setup_secret', None)
    request.session.pop('2fa_setup_backup_codes', None)
    logout(request)
    return redirect('accounts:signin')


@login_required(login_url='accounts:signin')
def profile_view(request):
    user_profile = None
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
    
    # Get active section from query parameter or default to 'profile'
    active_section = request.GET.get('section', 'profile')
    
    # Check if user has a password set (important for Google users)
    has_password = request.user.has_usable_password()
    
    context = {
        'user_profile': user_profile,
        'has_backup_codes': user_profile and len(user_profile.backup_codes) > 0,
        'active_section': active_section,
        'has_password': has_password,
    }
    return render(request, 'accounts/profile.html', context)


def google_login(request):
    """Initiates Google OAuth flow"""
    client_id = os.getenv('CLIENT_ID')
    
    # Use the redirect URI from .env or build it dynamically
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    if not redirect_uri:
        redirect_uri = request.build_absolute_uri('/accounts/google/login/callback/')
    
    # Store the next URL in session if provided
    if 'next' in request.GET:
        request.session['google_oauth_next'] = request.GET['next']
    
    # Create the authorization URL
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'prompt': 'select_account',
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(auth_url)


def google_callback(request):
    """Handles Google OAuth callback"""
    code = request.GET.get('code')
    
    if not code:
        return redirect('accounts:signin')
    
    # Exchange code for access token
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    
    # Use the redirect URI from .env or build it dynamically
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    if not redirect_uri:
        redirect_uri = request.build_absolute_uri('/accounts/google/login/callback/')
    
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_response = response.json()
        access_token = token_response.get('access_token')
        
        # Get user info from Google
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        # Extract user information
        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        google_id = user_info.get('id')
        picture = user_info.get('picture', '')
        
        if not email:
            return redirect('accounts:signin')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            # User exists, log them in
            login(request, user)
            # Clear the next URL from session
            next_url = request.session.pop('google_oauth_next', None)
            return redirect(next_url if next_url else 'home')
        except User.DoesNotExist:
            # Store Google user info in session for role selection
            request.session['google_user_info'] = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'google_id': google_id,
                'picture': picture,
            }
            # Redirect to role selection
            return redirect('accounts:google_role_selection')
    
    except requests.RequestException as e:
        # Handle error
        print(f"Error during Google OAuth: {e}")
        return redirect('accounts:signin')


def google_role_selection(request):
    """Allow user to select their role after Google authentication"""
    # Check if Google user info exists in session
    if 'google_user_info' not in request.session:
        return redirect('accounts:signin')
    
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        if user_type in ['student', 'instructor']:
            request.session['google_user_type'] = user_type
            return redirect('accounts:google_create_account')
    
    google_user_info = request.session.get('google_user_info', {})
    context = {
        'google_user_info': google_user_info,
        'user_type_choices': Profile.USER_TYPE_CHOICES,
    }
    return render(request, 'accounts/google_role_selection.html', context)


def google_create_account(request):
    """Create the user account from Google authentication"""
    # Check if Google user info exists in session
    if 'google_user_info' not in request.session or 'google_user_type' not in request.session:
        return redirect('accounts:signin')
    
    google_user_info = request.session.get('google_user_info')
    user_type = request.session.get('google_user_type')
    
    try:
        email = google_user_info.get('email')
        first_name = google_user_info.get('first_name', '')
        last_name = google_user_info.get('last_name', '')
        
        # Create username from email
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        
        # Create profile with selected user type
        Profile.objects.create(user=user, user_type=user_type)
        
        # Log in the user
        login(request, user)
        
        # Clear session data
        request.session.pop('google_user_info')
        request.session.pop('google_user_type')
        
        # Redirect to profile completion
        return redirect('accounts:profile_completion')
    
    except Exception as e:
        print(f"Error creating Google account: {e}")
        return redirect('accounts:signin')


@login_required(login_url='accounts:signin')
def profile_completion(request):
    """Complete profile with optional fields"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('home')
    
    if request.method == 'POST':
        if 'skip' in request.POST:
            # User wants to skip, redirect to home
            return redirect('home')
        
        # Save old state to check if 2FA was just enabled
        old_2fa_state = profile.two_step_verification
        
        form = ProfileCompletionForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            
            # Refresh profile to get updated state
            profile.refresh_from_db()
            
            # If 2FA was just enabled, redirect to setup
            if profile.two_step_verification and not old_2fa_state:
                messages.info(request, 'Please complete the 2FA setup process.')
                return redirect('accounts:setup_2fa')
            
            return redirect('home')
    else:
        form = ProfileCompletionForm(instance=profile)
    
    return render(request, 'accounts/profile_completion.html', {'form': form})


@login_required(login_url='accounts:signin')
def toggle_2fa(request):
    """Handle 2FA enable/disable"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('accounts:profile')
    
    # If disabling, require password verification
    if profile.two_step_verification:
        if request.method == 'POST':
            password = request.POST.get('password', '')
            user = authenticate(username=request.user.username, password=password)
            if not user:
                messages.error(request, 'Invalid password')
                return redirect('accounts:profile?section=security')
            
            disable_2fa(profile)
            messages.success(request, 'Two-step verification has been disabled')
            return redirect('accounts:profile?section=security')
        else:
            return redirect('accounts:profile?section=security')
    else:
        # Redirect to setup page
        return redirect('accounts:setup_2fa')


@login_required(login_url='accounts:signin')
@require_POST
def get_backup_codes(request):
    """Return backup codes after password verification"""
    password = request.POST.get('password', '')
    
    # Verify password
    user = authenticate(username=request.user.username, password=password)
    if not user:
        return JsonResponse({'success': False, 'error': 'Invalid password'}, status=400)
    
    # Get profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'}, status=404)
    
    return JsonResponse({
        'success': True, 
        'backup_codes': profile.backup_codes
    })


@login_required(login_url='accounts:signin')
@require_POST
def set_password(request):
    """Set or change password for user"""
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')
    
    # Validation
    if not new_password:
        return JsonResponse({'success': False, 'error': 'Password is required'}, status=400)
    
    if len(new_password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long'}, status=400)
    
    if new_password != confirm_password:
        return JsonResponse({'success': False, 'error': 'Passwords do not match'}, status=400)
    
    # If user already has a password, verify current password
    if request.user.has_usable_password():
        current_password = request.POST.get('current_password', '')
        if not current_password:
            return JsonResponse({'success': False, 'error': 'Current password is required'}, status=400)
        
        user = authenticate(username=request.user.username, password=current_password)
        if not user:
            return JsonResponse({'success': False, 'error': 'Current password is incorrect'}, status=400)
    
    # Set new password
    request.user.set_password(new_password)
    request.user.save()
    
    return JsonResponse({'success': True, 'message': 'Password updated successfully'})


@login_required(login_url='accounts:signin')
def setup_2fa_view(request):
    """Setup 2FA with QR code generation"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('accounts:profile')
    
    if profile.two_step_verification and profile.otp_secret:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        # Generate TOTP secret and backup codes but DON'T enable 2FA yet
        secret, backup_codes = generate_totp_secret(), generate_backup_codes(8)
        request.session['2fa_setup_secret'] = secret
        request.session['2fa_setup_backup_codes'] = backup_codes
        return redirect('accounts:show_qr_code')
    
    return render(request, 'accounts/setup_2fa.html')


@login_required(login_url='accounts:signin')
def show_qr_code(request):
    """Show QR code for TOTP setup and handle verification"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('accounts:profile')
    
    # Check if we're on step 3 (after successful verification)
    current_step = request.GET.get('step', '1')
    if current_step == '3':
        # Get backup codes from session (just enabled)
        backup_codes = request.session.get('2fa_completed_backup_codes', [])
        if not backup_codes:
            # If no backup codes in session, get from profile
            backup_codes = profile.backup_codes or []
        
        context = {
            'qr_code_data': '',  # Not needed for step 3
            'backup_codes': backup_codes,
            'secret': '',
            'current_step': 3,
        }
        # Clear the session backup codes after displaying
        request.session.pop('2fa_completed_backup_codes', None)
        return render(request, 'accounts/show_qr_code.html', context)
    
    # For steps 1 and 2, we need the setup secret
    if '2fa_setup_secret' not in request.session:
        return redirect('accounts:setup_2fa')
    
    secret = request.session.get('2fa_setup_secret')
    backup_codes = request.session.get('2fa_setup_backup_codes', [])
    
    # Initialize step number
    step_num = int(request.GET.get('step', '1'))
    
    # Handle TOTP verification
    if request.method == 'POST':
        token = request.POST.get('token', '')
        if verify_totp_token(secret, token):
            # Token is valid, enable 2FA
            profile.otp_secret = secret
            profile.backup_codes = backup_codes
            profile.two_step_verification = True
            profile.save()
            
            # Store backup codes in session temporarily to show on step 3
            request.session['2fa_completed_backup_codes'] = backup_codes
            
            # Clear setup session but keep backup codes for display
            request.session.pop('2fa_setup_secret', None)
            request.session.pop('2fa_setup_backup_codes', None)
            
            # Redirect to step 3 to show backup codes
            from django.urls import reverse
            return redirect(f"{reverse('accounts:show_qr_code')}?step=3")
        else:
            # Token is invalid - stay on step 2
            messages.error(request, 'Invalid code. Please try again.')
            step_num = 2
    
    # Generate QR code URI
    totp_uri = get_totp_uri(request.user, secret)
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    import base64
    img_data = base64.b64encode(img_buffer.read()).decode()
    
    context = {
        'qr_code_data': f'data:image/png;base64,{img_data}',
        'backup_codes': backup_codes,
        'secret': secret,
        'current_step': step_num,
    }
    
    return render(request, 'accounts/show_qr_code.html', context)


@login_required(login_url='accounts:signin')
def disable_2fa_view(request):
    """Disable 2FA with password verification"""
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        # Verify password
        user = authenticate(username=request.user.username, password=password)
        if not user:
            return JsonResponse({'success': False, 'error': 'Invalid password'}, status=400)
        
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Profile not found'}, status=404)
        
        # Disable 2FA
        disable_2fa(profile)
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)


@login_required(login_url='accounts:signin')
@require_POST
def reset_backup_codes_view(request):
    """Reset backup codes with password verification"""
    password = request.POST.get('password', '')
    
    # Verify password
    user = authenticate(username=request.user.username, password=password)
    if not user:
        return JsonResponse({'success': False, 'error': 'Invalid password'}, status=400)
    
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'}, status=404)
    
    backup_codes = reset_backup_codes(profile)
    return JsonResponse({'success': True, 'backup_codes': backup_codes})


@login_required(login_url='accounts:signin')
def download_backup_codes_view(request):
    """Download backup codes as text file"""
    try:
        profile = request.user.profile
        if not profile.backup_codes:
            messages.error(request, 'No backup codes available')
            return redirect('accounts:profile?section=security')
        
        content, content_type = download_backup_codes(profile.backup_codes)
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="trelix_backup_codes.txt"'
        return response
    except Profile.DoesNotExist:
        messages.error(request, 'Profile not found')
        return redirect('accounts:profile?section=security')


@login_required(login_url='accounts:signin')
@require_POST
def delete_trusted_device_view(request, device_id):
    """Delete a trusted device"""
    try:
        device = TrustedDevice.objects.get(id=device_id, user=request.user)
        device.delete()
        return JsonResponse({'success': True, 'message': 'Trusted device removed successfully'})
    except TrustedDevice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
