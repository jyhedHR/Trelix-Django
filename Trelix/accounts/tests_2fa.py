from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Profile
from .utils import (
    generate_backup_codes, validate_backup_code, generate_totp_secret,
    get_totp_uri, verify_totp_token, setup_2fa, reset_backup_codes, disable_2fa
)
import pyotp


class TOTPUtilitiesTestCase(TestCase):
    """Test TOTP utility functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.profile = Profile.objects.create(user=self.user, user_type='student')
    
    def test_generate_backup_codes(self):
        """Test backup code generation"""
        codes = generate_backup_codes(8)
        self.assertEqual(len(codes), 8)
        self.assertTrue(all(isinstance(code, str) for code in codes))
        self.assertTrue(all(len(code) > 0 for code in codes))
    
    def test_validate_backup_code(self):
        """Test backup code validation"""
        codes = generate_backup_codes(3)
        self.profile.backup_codes = codes
        self.profile.save()
        
        # Valid code
        valid_code = codes[0]
        self.assertTrue(validate_backup_code(self.profile, valid_code))
        
        # Check code was removed
        self.profile.refresh_from_db()
        self.assertNotIn(valid_code, self.profile.backup_codes)
        
        # Invalid code
        self.assertFalse(validate_backup_code(self.profile, 'INVALID'))
    
    def test_generate_totp_secret(self):
        """Test TOTP secret generation"""
        secret = generate_totp_secret()
        self.assertIsInstance(secret, str)
        self.assertGreater(len(secret), 0)
    
    def test_get_totp_uri(self):
        """Test TOTP URI generation"""
        secret = generate_totp_secret()
        uri = get_totp_uri(self.user, secret)
        self.assertIn('otpauth', uri)
        self.assertIn(self.user.email, uri)
    
    def test_verify_totp_token(self):
        """Test TOTP token verification"""
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        current_token = totp.now()
        
        self.assertTrue(verify_totp_token(secret, current_token))
        self.assertFalse(verify_totp_token(secret, '000000'))
        self.assertFalse(verify_totp_token('', current_token))
    
    def test_setup_2fa(self):
        """Test 2FA setup"""
        secret, backup_codes = setup_2fa(self.profile)
        
        self.assertIsNotNone(secret)
        self.assertEqual(len(backup_codes), 8)
        self.assertTrue(self.profile.two_step_verification)
        self.assertEqual(self.profile.otp_secret, secret)
        self.assertEqual(self.profile.backup_codes, backup_codes)
    
    def test_reset_backup_codes(self):
        """Test backup codes reset"""
        self.profile.backup_codes = generate_backup_codes(8)
        self.profile.save()
        
        old_codes = self.profile.backup_codes.copy()
        new_codes = reset_backup_codes(self.profile)
        
        self.assertNotEqual(old_codes, new_codes)
        self.assertEqual(self.profile.backup_codes, new_codes)
    
    def test_disable_2fa(self):
        """Test 2FA disable"""
        setup_2fa(self.profile)
        self.assertTrue(self.profile.two_step_verification)
        
        disable_2fa(self.profile)
        
        self.assertFalse(self.profile.two_step_verification)
        self.assertIsNone(self.profile.otp_secret)
        self.assertEqual(self.profile.backup_codes, [])


class TwoFactorAuthenticationFlowTestCase(TestCase):
    """Test complete 2FA login flow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.profile = Profile.objects.create(user=self.user, user_type='student')
    
    def test_signin_without_2fa(self):
        """Test signin without 2FA enabled"""
        response = self.client.post('/accounts/signin/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to home
        self.assertIn('_auth_user_id', self.client.session)
    
    def test_signin_with_2fa_redirect(self):
        """Test signin with 2FA enabled redirects to verification"""
        setup_2fa(self.profile)
        
        response = self.client.post('/accounts/signin/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should redirect to verification page
        self.assertEqual(response.status_code, 302)
        self.assertIn('2fa_user_id', self.client.session)
    
    def test_signin_with_valid_totp(self):
        """Test signin with valid TOTP token"""
        secret, _ = setup_2fa(self.profile)
        
        # Login first to get to 2FA step
        self.client.post('/accounts/signin/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Generate valid token
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        # Verify with token
        response = self.client.post('/accounts/verify-2fa/', {
            'token': token
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to home
        self.assertNotIn('2fa_user_id', self.client.session)
        self.assertIn('_auth_user_id', self.client.session)
    
    def test_signin_with_backup_code(self):
        """Test signin with valid backup code"""
        _, backup_codes = setup_2fa(self.profile)
        
        # Login first to get to 2FA step
        self.client.post('/accounts/signin/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        backup_code = backup_codes[0]
        
        # Verify with backup code
        response = self.client.post('/accounts/verify-2fa/?backup_code=true', {
            'code': backup_code
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to home
        self.assertNotIn('2fa_user_id', self.client.session)
        self.assertIn('_auth_user_id', self.client.session)
        
        # Check backup code was invalidated
        self.profile.refresh_from_db()
        self.assertNotIn(backup_code, self.profile.backup_codes)


class BackupCodeSecurityTestCase(TestCase):
    """Test backup code security features"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.profile = Profile.objects.create(user=self.user, user_type='student')
        setup_2fa(self.profile)
    
    def test_backup_code_single_use(self):
        """Test that backup codes can only be used once"""
        original_codes = self.profile.backup_codes.copy()
        code = original_codes[0]
        
        # Use code first time
        self.assertTrue(validate_backup_code(self.profile, code))
        
        # Try to use same code again
        self.assertFalse(validate_backup_code(self.profile, code))
        
        # Check code count decreased
        self.profile.refresh_from_db()
        self.assertEqual(len(self.profile.backup_codes), len(original_codes) - 1)
    
    def test_backup_code_case_insensitive(self):
        """Test that backup codes are case insensitive"""
        code = self.profile.backup_codes[0]
        
        # Lowercase
        self.assertTrue(validate_backup_code(self.profile, code.lower()))
        
        # Uppercase
        self.profile.backup_codes = [code]
        self.profile.save()
        self.assertTrue(validate_backup_code(self.profile, code.upper()))
    
    def test_backup_code_whitespace_handling(self):
        """Test that backup codes ignore whitespace"""
        code = self.profile.backup_codes[0]
        
        # With spaces
        self.assertTrue(validate_backup_code(self.profile, f'  {code}  '))
        
        # With newlines
        self.profile.backup_codes = [code]
        self.profile.save()
        self.assertTrue(validate_backup_code(self.profile, f'\n{code}\n'))

