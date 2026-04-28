from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from user.models import AthleteProfile, CoachProfile, User


def admin_app_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Access denied. Admin team only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
@admin_app_required
def dashboard_view(request):
    pending_coaches = User.objects.filter(role='coach', is_approved=False).select_related('coach_profile')
    pending_medicals = User.objects.filter(role='medical', is_approved=False).select_related('medical_profile')
    players = User.objects.filter(role='athlete').order_by('-date_joined')
    coaches = User.objects.filter(role='coach').order_by('-date_joined')
    medicals = User.objects.filter(role='medical').order_by('-date_joined')

    context = {
        'pending_coaches': pending_coaches,
        'pending_medicals': pending_medicals,
        'players': players,
        'coaches': coaches,
        'medicals': medicals,
    }
    return render(request, 'Admin/dashboard.html', context)


@login_required
@admin_app_required
def users_view(request):
    users = User.objects.select_related('athlete_profile', 'coach_profile', 'medical_profile').order_by('-date_joined')
    context = {
        'title': 'All Users',
        'users': users,
        'show_pending_coach': True,
        'show_pending_medical': True,
    }
    return render(request, 'Admin/users.html', context)


@login_required
@admin_app_required
def players_view(request):
    users = User.objects.filter(role='athlete').select_related('athlete_profile').order_by('-date_joined')
    context = {
        'title': 'Players',
        'users': users,
        'show_pending_coach': False,
        'show_pending_medical': False,
    }
    return render(request, 'Admin/users.html', context)


@login_required
@admin_app_required
def coaches_view(request):
    users = User.objects.filter(role='coach').select_related('coach_profile').order_by('-date_joined')
    context = {
        'title': 'Coaches',
        'users': users,
        'show_pending_coach': True,
        'show_pending_medical': False,
    }
    return render(request, 'Admin/users.html', context)


@login_required
@admin_app_required
def medicals_view(request):
    users = User.objects.filter(role='medical').select_related('medical_profile').order_by('-date_joined')
    context = {
        'title': 'Medical Staff',
        'users': users,
        'show_pending_coach': False,
        'show_pending_medical': True,
    }
    return render(request, 'Admin/users.html', context)


@login_required
@admin_app_required
def edit_user_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user_obj.name = request.POST.get('name', user_obj.name)
        user_obj.email = request.POST.get('email', user_obj.email)
        user_obj.phone = request.POST.get('phone', '')
        user_obj.address = request.POST.get('address', '')
        user_obj.blood_group = request.POST.get('blood_group', '')
        user_obj.is_active = request.POST.get('is_active') == 'on'

        if user_obj.role == 'coach':
            user_obj.is_approved = request.POST.get('is_approved') == 'on'
            coach_profile, _ = CoachProfile.objects.get_or_create(user=user_obj)
            coach_profile.specialization = request.POST.get('specialization', '')
            coach_profile.experience_years = int(request.POST.get('experience_years') or 0)
            coach_profile.certification = request.POST.get('certification', '')
            coach_profile.bio = request.POST.get('bio', '')
            sport_id = request.POST.get('sport')
            if sport_id:
                from player.models import Sport
                coach_profile.sport = Sport.objects.filter(id=sport_id).first()
            else:
                coach_profile.sport = None
            coach_profile.save()

        if user_obj.role == 'athlete':
            athlete_profile, _ = AthleteProfile.objects.get_or_create(user=user_obj)
            athlete_profile.age = request.POST.get('age') or None
            athlete_profile.height = request.POST.get('height', '')
            athlete_profile.weight = request.POST.get('weight', '')
            athlete_profile.fitness_level = request.POST.get('fitness_level', 'medium')
            athlete_profile.save()

        if user_obj.role == 'medical':
            from user.models import MedicalProfile
            medical_profile, _ = MedicalProfile.objects.get_or_create(user=user_obj)
            medical_profile.license_no = request.POST.get('license_no', '')
            medical_profile.specialty = request.POST.get('specialty', '')
            medical_profile.save()

        user_obj.save()
        messages.success(request, f'User {user_obj.name} updated successfully.')
        return redirect('admin_app:users')

    context = {'user_obj': user_obj}
    if user_obj.role == 'coach':
        from player.models import Sport
        context['sports'] = Sport.objects.all()
    return render(request, 'Admin/edit_user.html', context)


@login_required
@admin_app_required
def delete_user_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        name = user_obj.name
        user_obj.delete()
        messages.success(request, f'User {name} deleted successfully.')
        return redirect('admin_app:users')

    return render(request, 'Admin/delete_confirm.html', {'user_obj': user_obj})


@login_required
@admin_app_required
def toggle_user_status_view(request, user_id):
    if request.method != 'POST':
        return redirect('admin_app:users')

    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=['is_active'])
    messages.success(
        request,
        f'User {user_obj.name} {"activated" if user_obj.is_active else "deactivated"}.'
    )
    return redirect('admin_app:users')


@login_required
@admin_app_required
def approve_coach_view(request, user_id):
    if request.method != 'POST':
        return redirect('admin_app:users')

    coach_user = get_object_or_404(User, id=user_id, role='coach')
    coach_user.is_approved = True
    coach_user.is_active = True
    coach_user.save(update_fields=['is_approved', 'is_active'])

    messages.success(request, f'Coach {coach_user.name} approved successfully.')
    return redirect('admin_app:users')


@login_required
@admin_app_required
def approve_medical_view(request, user_id):
    if request.method != 'POST':
        return redirect('admin_app:users')

    medical_user = get_object_or_404(User, id=user_id, role='medical')
    medical_user.is_approved = True
    medical_user.is_active = True
    medical_user.save(update_fields=['is_approved', 'is_active'])

    messages.success(request, f'Medical staff {medical_user.name} approved successfully.')
    return redirect('admin_app:users')
