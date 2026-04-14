from django import forms
from .models import User


class SignUpForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password',
            'id': 'password'
        }),
        min_length=8,
        help_text='Password must be at least 8 characters.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'id': 'confirm_password'
        })
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'role']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name',
                'id': 'name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your email address',
                'id': 'email'
            }),
            'role': forms.Select(attrs={
                'class': 'form-input',
                'id': 'role'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if user.role == 'coach':
            user.is_approved = False
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'id': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'id': 'password'
        })
    )


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your registered email',
            'id': 'email'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter new password',
            'id': 'new_password'
        }),
        min_length=8,
        help_text='Password must be at least 8 characters.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm new password',
            'id': 'confirm_password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter new password',
            'id': 'new_password'
        }),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm new password',
            'id': 'confirm_password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'date_of_birth', 'blood_group', 'address', 'profile_photo']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name',
                'id': 'name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your email',
                'id': 'email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your phone number',
                'id': 'phone'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
                'id': 'date_of_birth'
            }),
            'blood_group': forms.Select(attrs={
                'class': 'form-input',
                'id': 'blood_group'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your address',
                'id': 'address',
                'rows': 3
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-input',
                'id': 'profile_photo',
                'accept': 'image/*'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class AthleteProfileForm(forms.Form):
    age = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your age',
            'id': 'age',
            'min': 5,
            'max': 100
        })
    )
    height = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': "e.g., 5'10\" or 178 cm",
            'id': 'height'
        })
    )
    weight = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 70 kg',
            'id': 'weight'
        })
    )
    fitness_level = forms.ChoiceField(
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'fitness_level'
        })
    )


class CoachProfileForm(forms.Form):
    specialization = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., Football, Cricket',
            'id': 'specialization'
        })
    )
    experience_years = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Years of experience',
            'id': 'experience_years',
            'min': 0
        })
    )
    certification = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your certifications',
            'id': 'certification'
        })
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Tell us about yourself...',
            'id': 'bio',
            'rows': 3
        })
    )
