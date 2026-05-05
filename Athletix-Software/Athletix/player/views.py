from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Sport, CoachRequest, AthleteCoach, DailyRoutine, AthleteSport
from .performance_utils import build_routine_performance_data
from user.models import User, CoachProfile


def athlete_required(view_func):
    """Decorator to ensure user is an athlete"""
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'athlete':
            messages.error(request, 'Access denied. Athletes only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@athlete_required
def player_dashboard(request):
    """Main dashboard for athlete/player"""
    user = request.user
    
    # Get athlete's selected sports
    selected_sports = AthleteSport.objects.filter(athlete=user)
    
    # Get active coaches
    active_coaches = AthleteCoach.objects.filter(athlete=user, is_active=True)
    
    # Get pending requests
    pending_requests = CoachRequest.objects.filter(athlete=user, status='pending')
    
    # Get today's routines
    from datetime import datetime
    today = datetime.now().strftime('%A').lower()
    todays_routines = DailyRoutine.objects.filter(athlete=user, day=today)

    from medical_staff.forms import AthleteSelfHealthRecordForm
    from medical_staff.models import AthleteHealthRecord
    recent_health_records = AthleteHealthRecord.objects.filter(athlete=user).order_by('-created_at')[:5]
    from medical_staff.models import MedicalFeedback
    recent_feedbacks = MedicalFeedback.objects.filter(athlete=user).order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'selected_sports': selected_sports,
        'active_coaches': active_coaches,
        'pending_requests': pending_requests,
        'todays_routines': todays_routines,
        'athlete_health_form': AthleteSelfHealthRecordForm(),
        'recent_health_records': recent_health_records,
        'recent_feedbacks': recent_feedbacks,
    }
    return render(request, 'player/dashboard.html', context)


@login_required
@athlete_required
def player_profile(request):
    """View and edit athlete profile"""
    user = request.user
    try:
        profile = user.athlete_profile
    except:
        profile = None
    
    selected_sports = AthleteSport.objects.filter(athlete=user).select_related('sport')
    active_coaches = AthleteCoach.objects.filter(athlete=user, is_active=True).select_related('coach', 'sport')
    
    context = {
        'user': user,
        'profile': profile,
        'selected_sports': selected_sports,
        'active_coaches': active_coaches,
    }
    return render(request, 'profile.html', context)


@login_required
@athlete_required
def health_report(request):
    """View health metrics and medical feedback for the athlete"""
    user = request.user
    from medical_staff.models import AthleteHealthRecord, MedicalFeedback

    health_records = AthleteHealthRecord.objects.filter(athlete=user).select_related('medical_staff')
    feedbacks = MedicalFeedback.objects.filter(athlete=user).select_related('medical_staff')

    context = {
        'user': user,
        'health_records': health_records,
        'feedbacks': feedbacks,
        'health_record_count': health_records.count(),
        'feedback_count': feedbacks.count(),
    }
    return render(request, 'player/health_report.html', context)


@login_required
@athlete_required
def select_sports(request):
    """Select sports for training"""
    user = request.user
    sports = Sport.objects.all()
    selected_sports = AthleteSport.objects.filter(athlete=user)
    selected_sport_ids = list(selected_sports.values_list('sport_id', flat=True))
    
    if request.method == 'POST':
        # Get list of selected sports from form
        selected_ids = request.POST.getlist('sports')
        
        # Remove deselected sports
        AthleteSport.objects.filter(athlete=user).exclude(sport_id__in=selected_ids).delete()
        
        # Add newly selected sports
        for sport_id in selected_ids:
            sport = get_object_or_404(Sport, id=sport_id)
            AthleteSport.objects.get_or_create(
                athlete=user,
                sport=sport,
                defaults={'skill_level': 'beginner'}
            )
        
        messages.success(request, 'Sports selection updated!')
        return redirect('player:select_sports')
    
    context = {
        'sports': sports,
        'selected_sports': selected_sports,
        'selected_sport_ids': selected_sport_ids,
    }
    return render(request, 'player/select_sports.html', context)


@login_required
@athlete_required
def find_coaches(request):
    """Find and request coaches"""
    user = request.user
    sport_id = request.GET.get('sport')
    
    athlete_sport_ids = list(
        AthleteSport.objects.filter(athlete=user).values_list('sport_id', flat=True)
    )

    # Get ALL active coach profiles (show every coach)
    from user.models import CoachProfile
    coaches = CoachProfile.objects.filter(
        user__is_active=True,
    ).select_related('user', 'sport')
    
    # Optional filter by specific sport
    if sport_id and sport_id.isdigit():
        sport_id_int = int(sport_id)
        coaches = coaches.filter(sport_id=sport_id_int)
    else:
        sport_id = ''
    
    # Show ALL available sports in the filter dropdown
    all_sports = Sport.objects.all()
    
    # Get existing requests and active coaches
    pending_requests = CoachRequest.objects.filter(athlete=user, status='pending').values_list('coach_id', flat=True)
    active_coach_relations = AthleteCoach.objects.filter(athlete=user, is_active=True).values_list('coach_id', flat=True)
    
    # Get CoachProfile IDs that have pending requests or are active
    requested_coach_ids = list(CoachProfile.objects.filter(user_id__in=pending_requests).values_list('id', flat=True))
    active_coach_ids = list(CoachProfile.objects.filter(user_id__in=active_coach_relations).values_list('id', flat=True))
    
    context = {
        'coaches': coaches,
        'all_sports': all_sports,
        'athlete_sports': athlete_sport_ids,
        'selected_sport': sport_id,
        'requested_coach_ids': requested_coach_ids,
        'active_coach_ids': active_coach_ids,
    }
    return render(request, 'player/find_coaches.html', context)


@login_required
@athlete_required
def request_coach(request, coach_id):
    """Send a training request to a coach"""
    from user.models import CoachProfile
    
    if request.method == 'POST':
        coach_profile = get_object_or_404(CoachProfile.objects.select_related('user', 'sport'), id=coach_id)
        coach = coach_profile.user

        if not coach_profile.sport:
            messages.error(request, 'This coach has no sport assigned yet.')
            return redirect('player:select_sports')

        sport = coach_profile.sport

        athlete_has_sport = AthleteSport.objects.filter(
            athlete=request.user,
            sport=sport
        ).exists()

        if not athlete_has_sport:
            messages.error(request, f'You can only request coaches for your selected sports. Please add {sport.name} first.')
            return redirect('player:select_sports')
        
        # Check if request already exists
        existing = CoachRequest.objects.filter(
            athlete=request.user,
            coach=coach,
            sport=sport
        ).first()
        
        if existing:
            if existing.status == 'rejected':
                existing.status = 'pending'
                existing.save()
                messages.success(request, f'Request re-sent to {coach.first_name} {coach.last_name}!')
            else:
                messages.warning(request, 'You already have a pending or accepted request for this coach.')
        else:
            CoachRequest.objects.create(
                athlete=request.user,
                coach=coach,
                sport=sport
            )
            messages.success(request, f'Request sent to {coach.first_name} {coach.last_name}!')
        
        return redirect('player:find_coaches')
    
    return redirect('player:find_coaches')


@login_required
@athlete_required
def my_coaches(request):
    """View all coaches training the athlete"""
    user = request.user
    active_coaches = AthleteCoach.objects.filter(athlete=user, is_active=True).select_related('coach', 'sport')
    pending_requests = CoachRequest.objects.filter(athlete=user, status='pending').select_related('coach', 'sport')
    
    # Attach coach profile to each relation
    for ac in active_coaches:
        try:
            ac.coach_profile = ac.coach.coach_profile
        except:
            pass
    
    for req in pending_requests:
        try:
            req.coach_profile = req.coach.coach_profile
        except:
            pass
    
    context = {
        'active_coaches': active_coaches,
        'pending_requests': pending_requests,
    }
    return render(request, 'player/my_coaches.html', context)


@login_required
@athlete_required
def daily_routine(request):
    """View daily routine set by coach"""
    user = request.user
    day_filter = request.GET.get('day', '')
    
    routines = DailyRoutine.objects.filter(athlete=user).select_related('sport', 'coach')
    
    if day_filter:
        routines = routines.filter(day=day_filter)
    
    # Add day_of_week attribute for template compatibility
    for routine in routines:
        routine.day_of_week = routine.day
    
    context = {
        'routines': routines,
        'selected_day': day_filter,
    }
    return render(request, 'player/daily_routine.html', context)


@login_required
@athlete_required
def routine_detail(request, routine_id):
    """View detailed routine"""
    routine = get_object_or_404(DailyRoutine, id=routine_id, athlete=request.user)
    
    context = {
        'routine': routine,
    }
    return render(request, 'player/routine_detail.html', context)


@login_required
@athlete_required
def player_performance(request):
    """Show a full performance chart for the athlete based on routines."""
    user = request.user
    routines = DailyRoutine.objects.filter(athlete=user)
    performance_data = build_routine_performance_data(routines)

    context = {
        'user': user,
        **performance_data,
    }
    return render(request, 'player/performance.html', context)

