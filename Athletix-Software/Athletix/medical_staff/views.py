from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from user.models import User
from .forms import AthleteHealthRecordForm, AthleteSelfHealthRecordForm, MedicalFeedbackForm
from .models import AthleteHealthRecord, MedicalFeedback


def medical_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not (request.user.role == 'medical' or request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Access denied. Medical staff only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def athlete_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'athlete':
            messages.error(request, 'Access denied. Athletes only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@medical_required
def dashboard(request):
    athletes = User.objects.filter(role='athlete', is_active=True).order_by('name')
    latest_health_records = AthleteHealthRecord.objects.select_related('athlete', 'medical_staff').order_by('-created_at')
    latest_feedbacks = MedicalFeedback.objects.select_related('athlete').order_by('-created_at')[:12]

    injury_summary = AthleteHealthRecord.objects.values('injury_status').annotate(
        total=Count('id')
    ).order_by('-total')
    recovery_watch_count = AthleteHealthRecord.objects.filter(
        Q(recovery_status='watch') | Q(recovery_status='critical')
    ).count()

    context = {
        'athletes_count': athletes.count(),
        'records_count': AthleteHealthRecord.objects.count(),
        'feedback_count': MedicalFeedback.objects.count(),
        'recovery_watch_count': recovery_watch_count,
        'latest_health_records': latest_health_records,
        'latest_feedbacks': latest_feedbacks,
        'injury_summary': injury_summary,
        'feedback_form': MedicalFeedbackForm(),
    }
    return render(request, 'medical_staff/dashboard.html', context)


@login_required
@athlete_required
def add_self_health_record(request):
    if request.method != 'POST':
        return redirect('profile')

    form = AthleteSelfHealthRecordForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.athlete = request.user
        # Athlete submits own metrics; medical staff can review these and respond with feedback.
        # `medical_staff` comes from the bound form (optional).
        # If athlete asked explicitly for a medical review, mark the record
        record.review_requested = bool(request.POST.get('request_review'))
        record.save()
        if record.review_requested:
            messages.success(request, 'Your health metrics were saved and a review was requested from medical staff.')
        else:
            messages.success(request, 'Your health metrics were saved. Medical staff can now review and provide feedback.')
    else:
        messages.error(request, 'Please fix errors in your health metrics form.')
    return redirect('profile')


@login_required
@medical_required
def add_health_record(request):
    if request.method != 'POST':
        return redirect('medical_staff:dashboard')

    form = AthleteHealthRecordForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.medical_staff = request.user
        record.save()
        messages.success(request, 'Health and injury metrics saved successfully.')
    else:
        messages.error(request, 'Please fix errors in health record form.')
    return redirect('medical_staff:dashboard')


@login_required
@medical_required
def add_feedback(request):
    if request.method != 'POST':
        return redirect('medical_staff:dashboard')

    form = MedicalFeedbackForm(request.POST)
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.medical_staff = request.user
        feedback.save()
        messages.success(request, 'Medical feedback submitted successfully.')
    else:
        messages.error(request, 'Please fix errors in feedback form.')
    return redirect('medical_staff:dashboard')


@login_required
@medical_required
def athlete_health_detail(request, athlete_id):
    """Display full health condition history for an athlete"""
    from django.shortcuts import get_object_or_404
    
    athlete = get_object_or_404(User, id=athlete_id, role='athlete', is_active=True)
    
    # Get all health records for this athlete
    health_records = AthleteHealthRecord.objects.filter(athlete=athlete).select_related('medical_staff').order_by('-created_at')
    
    # Get all feedback for this athlete
    feedback_records = MedicalFeedback.objects.filter(athlete=athlete).select_related('medical_staff').order_by('-created_at')
    
    # Get latest health record for quick stats
    latest_record = health_records.first()
    
    context = {
        'athlete': athlete,
        'health_records': health_records,
        'feedback_records': feedback_records,
        'latest_record': latest_record,
    }
    return render(request, 'medical_staff/athlete_health_detail.html', context)
