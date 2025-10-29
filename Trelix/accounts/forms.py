from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile  # import the Profile model

USER_TYPE_CHOICES = (
    ('student', 'Student'),
    ('instructor', 'Instructor'),
)

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, required=True, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_type')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create profile with user_type
            Profile.objects.create(user=user, user_type=self.cleaned_data['user_type'])
        return user


class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'phone_number', 'two_step_verification']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (optional)'}),
            'two_step_verification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TOTPVerificationForm(forms.Form):
    """Form for TOTP verification during login"""
    token = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autocomplete': 'off',
            'autofocus': True
        }),
        label='Authentication Code',
        help_text='Enter the 6-digit code from your authenticator app'
    )


class BackupCodeForm(forms.Form):
    """Form for backup code verification during login"""
    code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXXX-XXXX',
            'autocomplete': 'off',
            'autofocus': True
        }),
        label='Backup Code',
        help_text='Enter one of your backup codes'
    )