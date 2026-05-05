from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from player.models import Sport, CoachRequest, AthleteCoach, DailyRoutine, AthleteSport
from player.performance_utils import build_routine_performance_data
from user.models import User


def coach_required(view_func):
    """Decorator to ensure user is a coach"""
    def wrapper(request, *args, **kwargs):
        if not (request.user.role == 'coach' or request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Access denied. Coaches only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@coach_required
def coach_dashboard(request):
    """Main dashboard for coach"""
    user = request.user
    
    # Get pending requests - need to get athlete profile for each
    pending_requests = CoachRequest.objects.filter(coach=user, status='pending').select_related('athlete', 'sport')
    for req in pending_requests:
        try:
            req.athlete_profile = req.athlete.athlete_profile
        except:
            pass
    
    # Get active athletes
    my_athletes = AthleteCoach.objects.filter(coach=user, is_active=True).select_related('athlete', 'sport')
    for ac in my_athletes:
        try:
            ac.athlete_profile = ac.athlete.athlete_profile
        except:
            pass
    
    # Get total routines created
    total_routines = DailyRoutine.objects.filter(coach=user).count()
    
    # Get sports count
    sports_count = Sport.objects.count()
    
    context = {
        'user': user,
        'pending_requests': pending_requests,
        'my_athletes': my_athletes,
        'total_routines': total_routines,
        'sports_count': sports_count,
    }
    return render(request, 'coach/dashboard.html', context)


@login_required
@coach_required
def coach_profile(request):
    """View coach profile - uses unified profile template"""
    user = request.user
    try:
        profile = user.coach_profile
    except:
        profile = None
    
    # Get active athletes
    my_athletes = AthleteCoach.objects.filter(coach=user, is_active=True).select_related('athlete', 'sport')
    
    # Get stats
    athlete_count = my_athletes.count()
    routine_count = DailyRoutine.objects.filter(coach=user).count()
    pending_count = CoachRequest.objects.filter(coach=user, status='pending').count()
    
    context = {
        'user': user,
        'profile': profile,
        'my_athletes': my_athletes,
        'athlete_count': athlete_count,
        'routine_count': routine_count,
        'pending_count': pending_count,
    }
    return render(request, 'profile.html', context)


@login_required
@coach_required
def athlete_requests(request):
    """View and manage athlete requests"""
    user = request.user
    
    pending_requests = CoachRequest.objects.filter(coach=user, status='pending').select_related('athlete', 'sport')
    past_requests = CoachRequest.objects.filter(coach=user).exclude(status='pending').select_related('athlete', 'sport')
    
    # Attach athlete profile
    for req in pending_requests:
        try:
            req.athlete_profile = req.athlete.athlete_profile
        except:
            pass
    
    for req in past_requests:
        try:
            req.athlete_profile = req.athlete.athlete_profile
        except:
            pass
    
    context = {
        'pending_requests': pending_requests,
        'past_requests': past_requests,
    }
    return render(request, 'coach/athlete_requests.html', context)


@login_required
@coach_required
def handle_request(request, request_id, action):
    """Accept or reject athlete request"""
    if request.method != 'POST':
        return redirect('coach:athlete_requests')
        
    coach_request = get_object_or_404(CoachRequest, id=request_id, coach=request.user)
    from user.models import CoachProfile
    coach_profile = request.user.coach_profile
    
    if action == 'accept':
        # Verify coach has a sport assigned
        if not coach_profile.sport:
            messages.error(request, 'You must assign a sport to your profile before accepting requests.')
            return redirect('coach:athlete_requests')
        
        # Verify the coach's sport matches the request sport
        if coach_profile.sport_id != coach_request.sport_id:
            messages.error(request, f'You can only accept requests for your assigned sport ({coach_profile.sport.name}).')
            return redirect('coach:athlete_requests')
        
        coach_request.status = 'accepted'
        coach_request.save()
        
        # Create AthleteCoach relationship
        AthleteCoach.objects.get_or_create(
            athlete=coach_request.athlete,
            coach=coach_request.coach,
            sport=coach_request.sport,
            defaults={'is_active': True}
        )
        
        messages.success(request, f'Accepted {coach_request.athlete.first_name} for {coach_request.sport.name} training!')
    
    elif action == 'reject':
        coach_request.status = 'rejected'
        coach_request.save()
        messages.info(request, f'Rejected request from {coach_request.athlete.first_name}.')
    
    return redirect('coach:athlete_requests')


@login_required
@coach_required
def my_athletes(request):
    """View all athletes under this coach"""
    user = request.user
    athletes = AthleteCoach.objects.filter(coach=user, is_active=True).select_related('athlete', 'sport')
    
    # Get routine count for each athlete
    for ac in athletes:
        ac.routine_count = DailyRoutine.objects.filter(athlete=ac.athlete, coach=user).count()
    
    context = {
        'athletes': athletes,
    }
    return render(request, 'coach/my_athletes.html', context)


@login_required
@coach_required
def athlete_detail(request, athlete_id):
    """View specific athlete details"""
    # Get athlete profile
    from user.models import AthleteProfile
    athlete_profile = get_object_or_404(AthleteProfile, id=athlete_id)
    athlete = athlete_profile.user
    
    # Verify coach relationship
    athlete_coach = AthleteCoach.objects.filter(athlete=athlete, coach=request.user, is_active=True).first()
    if not athlete_coach:
        messages.error(request, 'You are not coaching this athlete.')
        return redirect('coach:my_athletes')
    
    # Get routines for this athlete from this coach
    routines = DailyRoutine.objects.filter(
        athlete=athlete,
        coach=request.user
    ).select_related('sport')
    
    # Add day_of_week attribute for template compatibility
    for routine in routines:
        routine.day_of_week = routine.day
    
    # Get athlete's selected sports
    athlete_sports = AthleteSport.objects.filter(athlete=athlete).select_related('sport')
    
    context = {
        'athlete': athlete_profile,
        'routines': routines,
        'athlete_sports': athlete_sports,
    }
    return render(request, 'coach/athlete_detail.html', context)


def _get_active_coach_athlete(request, athlete_profile_id):
    from user.models import AthleteProfile
    athlete_profile = get_object_or_404(AthleteProfile, id=athlete_profile_id)
    athlete = athlete_profile.user
    athlete_coach = AthleteCoach.objects.filter(athlete=athlete, coach=request.user, is_active=True).first()
    if not athlete_coach:
        messages.error(request, 'You are not coaching this athlete.')
        return None, None
    return athlete_profile, athlete


@login_required
@coach_required
def create_routine_select(request):
    """Create a routine by selecting an athlete first"""
    my_athletes = AthleteCoach.objects.filter(
        coach=request.user,
        is_active=True
    ).select_related('athlete', 'sport')

    for ac in my_athletes:
        try:
            ac.athlete_profile = ac.athlete.athlete_profile
        except:
            ac.athlete_profile = None

    if request.method == 'POST':
        athlete_id = request.POST.get('athlete_id')
        athlete_profile, athlete = _get_active_coach_athlete(request, athlete_id)
        if not athlete_profile:
            return redirect('coach:create_routine_select')

        day = request.POST.get('day_of_week')
        workout_date = request.POST.get('workout_date')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        exercises = request.POST.get('exercises', '')
        notes = request.POST.get('notes', '')
        sport_id = request.POST.get('sport')

        if all([day, workout_date, title, start_time, end_time, sport_id]):
            sport = get_object_or_404(Sport, id=sport_id)
            DailyRoutine.objects.create(
                athlete=athlete,
                coach=request.user,
                sport=sport,
                day=day,
                workout_date=workout_date,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                exercises=exercises,
                notes=notes,
                athlete_marked_complete=False,
                coach_approved_completion=False,
                completion_message='Not complete'
            )
            messages.success(request, f'Routine created for {athlete.first_name} on {day.title()}!')
            return redirect('coach:athlete_detail', athlete_id=athlete_profile.id)

        messages.error(request, 'Please fill in all required fields.')

    sports = Sport.objects.all()
    context = {
        'my_athletes': my_athletes,
        'sports': sports,
    }
    return render(request, 'coach/create_routine.html', context)


@login_required
@coach_required
def create_routine(request, athlete_id):
    """Create daily routine for an athlete"""
    from user.models import AthleteProfile
    athlete_profile = get_object_or_404(AthleteProfile, id=athlete_id)
    athlete = athlete_profile.user
    
    # Verify coach relationship
    athlete_coach = AthleteCoach.objects.filter(athlete=athlete, coach=request.user, is_active=True).first()
    if not athlete_coach:
        messages.error(request, 'You are not coaching this athlete.')
        return redirect('coach:my_athletes')
    
    if request.method == 'POST':
        day = request.POST.get('day_of_week')
        workout_date = request.POST.get('workout_date')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        exercises = request.POST.get('exercises', '')
        notes = request.POST.get('notes', '')
        sport_id = request.POST.get('sport')
        
        if all([day, workout_date, title, start_time, end_time, sport_id]):
            sport = get_object_or_404(Sport, id=sport_id)
            DailyRoutine.objects.create(
                athlete=athlete,
                coach=request.user,
                sport=sport,
                day=day,
                workout_date=workout_date,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                exercises=exercises,
                notes=notes,
                athlete_marked_complete=False,
                coach_approved_completion=False,
                completion_message='Not complete'
            )
            messages.success(request, f'Routine created for {athlete.first_name} on {day.title()}!')
            return redirect('coach:athlete_detail', athlete_id=athlete_id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    sports = Sport.objects.all()
    
    context = {
        'athlete': athlete_profile,
        'sports': sports,
    }
    return render(request, 'coach/create_routine.html', context)


@login_required
@coach_required
def edit_routine(request, routine_id):
    """Edit existing routine"""
    routine = get_object_or_404(DailyRoutine, id=routine_id, coach=request.user)
    
    if request.method == 'POST':
        routine.day = request.POST.get('day_of_week', routine.day)
        routine.workout_date = request.POST.get('workout_date') or None
        routine.title = request.POST.get('title', routine.title)
        routine.description = request.POST.get('description', '')
        routine.start_time = request.POST.get('start_time', routine.start_time)
        routine.end_time = request.POST.get('end_time', routine.end_time)
        routine.exercises = request.POST.get('exercises', routine.exercises)
        routine.notes = request.POST.get('notes', '')
        routine.coach_approved_completion = False
        routine.athlete_marked_complete = False
        routine.completion_message = 'Not complete'
        sport_id = request.POST.get('sport')
        if sport_id:
            routine.sport = get_object_or_404(Sport, id=sport_id)
        routine.save()
        
        messages.success(request, 'Routine updated successfully!')
        
        # Find the athlete_profile
        try:
            athlete_profile = routine.athlete.athlete_profile
            return redirect('coach:athlete_detail', athlete_id=athlete_profile.id)
        except:
            return redirect('coach:my_athletes')
    
    # Add day_of_week for template
    routine.day_of_week = routine.day
    sports = Sport.objects.all()
    
    context = {
        'routine': routine,
        'sports': sports,
    }
    return render(request, 'coach/edit_routine.html', context)


@login_required
@coach_required
def delete_routine(request, routine_id):
    """Delete a routine"""
    if request.method != 'POST':
        return redirect('coach:my_athletes')
        
    routine = get_object_or_404(DailyRoutine, id=routine_id, coach=request.user)
    
    # Get athlete profile before deleting
    try:
        athlete_profile = routine.athlete.athlete_profile
        athlete_id = athlete_profile.id
    except:
        athlete_id = None
    
    routine.delete()
    messages.success(request, 'Routine deleted successfully!')
    
    if athlete_id:
        return redirect('coach:athlete_detail', athlete_id=athlete_id)
    return redirect('coach:my_athletes')


@login_required
@coach_required
def approve_routine_completion(request, routine_id):
    if request.method != 'POST':
        return redirect('coach:my_athletes')

    routine = get_object_or_404(DailyRoutine, id=routine_id, coach=request.user)
    routine.athlete_marked_complete = True
    routine.coach_approved_completion = True
    routine.completion_message = 'Approved by coach.'
    routine.save(update_fields=['athlete_marked_complete', 'coach_approved_completion', 'completion_message'])
    messages.success(request, 'Routine completion approved.')
    from user.models import AthleteProfile
    athlete_profile = AthleteProfile.objects.filter(user=routine.athlete).first()
    if athlete_profile:
        return redirect('coach:athlete_detail', athlete_id=athlete_profile.id)
    return redirect('coach:my_athletes')


@login_required
@coach_required
def performance_search(request):
    """Search coached athletes by name and inspect their performance charts."""
    user = request.user
    query = request.GET.get('q', '').strip()
    selected_relation_id = request.GET.get('athlete', '').strip()

    relations = AthleteCoach.objects.filter(coach=user, is_active=True).select_related('athlete', 'sport')
    if query:
        relations = relations.filter(
            Q(athlete__first_name__icontains=query) |
            Q(athlete__last_name__icontains=query) |
            Q(athlete__email__icontains=query)
        )

    search_results = []
    for relation in relations:
        summary = build_routine_performance_data(
            DailyRoutine.objects.filter(athlete=relation.athlete, coach=user)
        )
        athlete_profile = getattr(relation.athlete, 'athlete_profile', None)
        summary.update({
            'relation_id': relation.id,
            'athlete': relation.athlete,
            'athlete_profile': athlete_profile,
            'sport': relation.sport,
        })
        search_results.append(summary)

    selected_relation = None
    selected_summary = None
    if selected_relation_id.isdigit():
        selected_relation = relations.filter(id=int(selected_relation_id)).first()
        if selected_relation:
            selected_summary = build_routine_performance_data(
                DailyRoutine.objects.filter(athlete=selected_relation.athlete, coach=user)
            )
            selected_summary.update({
                'relation_id': selected_relation.id,
                'athlete': selected_relation.athlete,
                'athlete_profile': getattr(selected_relation.athlete, 'athlete_profile', None),
                'sport': selected_relation.sport,
            })
    elif search_results:
        selected_summary = search_results[0]
        selected_relation = relations.filter(id=selected_summary['relation_id']).first()

    context = {
        'search_query': query,
        'search_results': search_results,
        'selected_summary': selected_summary,
        'selected_relation': selected_relation,
        'total_results': len(search_results),
    }
    return render(request, 'coach/performance_search.html', context)

