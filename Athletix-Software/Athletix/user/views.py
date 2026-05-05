from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .forms import SignUpForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, ProfileEditForm
from .models import User, AthleteProfile, CoachProfile, MedicalProfile


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
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
            elif user.role == 'medical':
                messages.success(request, 'Medical staff account created. Please wait for admin approval before logging in.')
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
        return redirect('dashboard')

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
                        if user.role == 'medical' and not user.is_approved:
                            messages.error(request, 'Your medical staff account is pending admin approval.')
                            return render(request, 'user/login.html', {'form': form})
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.first_name}!')
                        if user.is_staff or user.is_superuser:
                            return redirect('admin_app:dashboard')
                        return redirect('dashboard')
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

    if user.is_staff or user.is_superuser:
        return redirect('admin_app:dashboard')
    
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
        from medical_staff.forms import AthleteSelfHealthRecordForm
        from medical_staff.models import AthleteHealthRecord, MedicalFeedback
        context['selected_sports'] = AthleteSport.objects.filter(athlete=user).select_related('sport')
        context['active_coaches'] = AthleteCoach.objects.filter(athlete=user, is_active=True).select_related('coach', 'sport')
        context['athlete_health_form'] = AthleteSelfHealthRecordForm()
        context['latest_self_health_records'] = AthleteHealthRecord.objects.filter(
            athlete=user
        ).select_related('medical_staff')[:8]
        context['medical_feedback_for_athlete'] = MedicalFeedback.objects.filter(
            athlete=user
        ).select_related('medical_staff')[:8]
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
            role_profile, _ = MedicalProfile.objects.get_or_create(user=user)

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


@login_required
def profile_search_view(request):
    """Search all users and open full public profile details."""
    query = request.GET.get('q', '').strip()
    users_qs = User.objects.filter(is_active=True).order_by('name')

    if query:
        users_qs = users_qs.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(role__icontains=query)
        )

    users = list(users_qs)
    medical_user_ids = [user.id for user in users if user.role == 'medical']
    medical_profiles = {
        profile.user_id: profile
        for profile in MedicalProfile.objects.filter(user_id__in=medical_user_ids)
    }

    for user in users:
        if user.role == 'medical':
            specialty = (medical_profiles.get(user.id).specialty if medical_profiles.get(user.id) else '') or 'Specialty Not Set'
            user.profile_role_label = f'Doctor - {specialty}'
        else:
            user.profile_role_label = user.get_role_display()

    context = {
        'search_query': query,
        'results': users,
        'result_count': len(users),
    }
    return render(request, 'user/profile_search.html', context)


@login_required
def public_profile_view(request, user_id):
    """Show full profile details for a selected user."""
    profile_user = get_object_or_404(User, id=user_id, is_active=True)

    context = {
        'profile_user': profile_user,
        'profile_role_label': profile_user.get_role_display(),
    }

    if profile_user.role == 'athlete':
        profile = AthleteProfile.objects.filter(user=profile_user).first()
        from player.models import AthleteSport, AthleteCoach, DailyRoutine

        selected_sports = AthleteSport.objects.filter(athlete=profile_user).select_related('sport')
        active_coaches = AthleteCoach.objects.filter(athlete=profile_user, is_active=True).select_related('coach', 'sport')
        routines = DailyRoutine.objects.filter(athlete=profile_user)

        context.update({
            'role_profile': profile,
            'selected_sports': selected_sports,
            'active_coaches': active_coaches,
            'routine_count': routines.count(),
            'completed_routine_count': routines.filter(coach_approved_completion=True).count(),
        })

    elif profile_user.role == 'coach':
        profile = CoachProfile.objects.filter(user=profile_user).first()
        from player.models import AthleteCoach, DailyRoutine

        my_athletes = AthleteCoach.objects.filter(coach=profile_user, is_active=True).select_related('athlete', 'sport')
        context.update({
            'role_profile': profile,
            'my_athletes': my_athletes,
            'athlete_count': my_athletes.count(),
            'routine_count': DailyRoutine.objects.filter(coach=profile_user).count(),
        })

    elif profile_user.role == 'medical':
        profile = MedicalProfile.objects.filter(user=profile_user).first()
        from medical_staff.models import AthleteHealthRecord, MedicalFeedback

        context.update({
            'role_profile': profile,
            'profile_role_label': f"Doctor - {(profile.specialty if profile and profile.specialty else 'Specialty Not Set')}",
            'health_record_count': AthleteHealthRecord.objects.filter(medical_staff=profile_user).count(),
            'feedback_count': MedicalFeedback.objects.filter(medical_staff=profile_user).count(),
        })

    return render(request, 'user/public_profile.html', context)
