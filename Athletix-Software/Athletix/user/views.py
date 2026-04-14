from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .forms import SignUpForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, ProfileEditForm
from .models import User, AthleteProfile, CoachProfile, MedicalProfile


def home_view(request):
    return render(request, 'home.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            if user.role == 'athlete':
                AthleteProfile.objects.create(user=user)
            elif user.role == 'coach':
                CoachProfile.objects.create(user=user)
            elif user.role == 'medical':
                MedicalProfile.objects.create(user=user)

            if user.role == 'coach':
                messages.success(request, 'Coach account created. Please wait for admin approval before logging in.')
            else:
                messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()

    return render(request, 'user/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        # Redirect to home page for all users
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    if user.is_active:
                        if user.role == 'coach' and not user.is_approved:
                            messages.error(request, 'Your coach account is pending admin approval.')
                            return render(request, 'user/login.html', {'form': form})
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.first_name}!')
                        # Redirect to home page after login
                        return redirect('home')
                    else:
                        messages.error(request, 'Your account has been deactivated.')
                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'user/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            new_password = form.cleaned_data['new_password']
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully! Please log in with your new password.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    else:
        form = ForgotPasswordForm()

    return render(request, 'user/forget_password.html', {'form': form})


def reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                messages.success(request, 'Password reset successful! Please log in.')
                return redirect('login')
        else:
            form = ResetPasswordForm()

        return render(request, 'user/password_reset_confirm.html', {
            'form': form,
            'uidb64': uidb64,
            'token': token
        })
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('forgot_password')


@login_required
def dashboard_view(request):
    """Redirect to role-specific dashboard or show generic dashboard"""
    user = request.user
    
    # Redirect athletes to player dashboard
    if user.role == 'athlete':
        return redirect('player:dashboard')
    # Redirect coaches to coach dashboard
    elif user.role == 'coach':
        return redirect('coach:dashboard')
    elif user.role == 'medical':
        return redirect('medical_staff:dashboard')
    
    # For others, show generic dashboard
    context = {'user': user}

    return render(request, 'user/dashboard.html', context)


@login_required
def profile_view(request):
    """Unified profile view - redirects to role-specific profiles or shows unified template"""
    user = request.user
    context = {'user': user}

    if user.role == 'athlete':
        try:
            context['profile'] = user.athlete_profile
        except AthleteProfile.DoesNotExist:
            context['profile'] = None
        # Get athlete-specific data
        from player.models import AthleteSport, AthleteCoach
        context['selected_sports'] = AthleteSport.objects.filter(athlete=user).select_related('sport')
        context['active_coaches'] = AthleteCoach.objects.filter(athlete=user, is_active=True).select_related('coach', 'sport')
    elif user.role == 'coach':
        try:
            context['profile'] = user.coach_profile
        except CoachProfile.DoesNotExist:
            context['profile'] = None
        # Get coach-specific data
        from player.models import AthleteCoach, DailyRoutine, CoachRequest
        context['my_athletes'] = AthleteCoach.objects.filter(coach=user, is_active=True).select_related('athlete', 'sport')
        context['athlete_count'] = context['my_athletes'].count()
        context['routine_count'] = DailyRoutine.objects.filter(coach=user).count()
        context['pending_count'] = CoachRequest.objects.filter(coach=user, status='pending').count()
    elif user.role == 'medical':
        try:
            context['profile'] = user.medical_profile
        except MedicalProfile.DoesNotExist:
            context['profile'] = None
        from medical_staff.models import AthleteHealthRecord, MedicalFeedback
        context['latest_health_records'] = AthleteHealthRecord.objects.filter(
            medical_staff=user
        ).select_related('athlete')[:10]
        context['latest_feedbacks'] = MedicalFeedback.objects.filter(
            medical_staff=user
        ).select_related('athlete')[:10]
        context['medical_health_count'] = AthleteHealthRecord.objects.filter(medical_staff=user).count()
        context['medical_feedback_count'] = MedicalFeedback.objects.filter(medical_staff=user).count()

    return render(request, 'profile.html', context)


@login_required
def profile_edit_view(request):
    user = request.user
    
    # Get role-specific profile
    role_profile = None
    if user.role == 'athlete':
        try:
            role_profile = user.athlete_profile
        except AthleteProfile.DoesNotExist:
            role_profile = AthleteProfile.objects.create(user=user)
    elif user.role == 'coach':
        try:
            role_profile = user.coach_profile
        except CoachProfile.DoesNotExist:
            role_profile = CoachProfile.objects.create(user=user)
    elif user.role == 'medical':
        try:
            role_profile = user.medical_profile
        except MedicalProfile.DoesNotExist:
            role_profile = MedicalProfile.objects.create(user=user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            
            # Update role-specific profile
            if user.role == 'athlete' and role_profile:
                role_profile.age = request.POST.get('age') or None
                role_profile.height = request.POST.get('height', '')
                role_profile.weight = request.POST.get('weight', '')
                role_profile.fitness_level = request.POST.get('fitness_level', 'medium')
                role_profile.save()
            elif user.role == 'coach' and role_profile:
                from player.models import Sport
                role_profile.specialization = request.POST.get('specialization', '')
                role_profile.experience_years = request.POST.get('experience_years') or 0
                role_profile.certification = request.POST.get('certification', '')
                role_profile.bio = request.POST.get('bio', '')
                sport_id = request.POST.get('sport')
                role_profile.sport = Sport.objects.filter(id=sport_id).first() if sport_id else None
                role_profile.save()
            elif user.role == 'medical' and role_profile:
                role_profile.license_no = request.POST.get('license_no', '')
                role_profile.specialty = request.POST.get('specialty', '')
                role_profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=user)

    context = {
        'form': form,
        'role_profile': role_profile,
    }
    if user.role == 'coach':
        from player.models import Sport
        context['sports'] = Sport.objects.all()
    return render(request, 'user/profile_edit.html', context)
