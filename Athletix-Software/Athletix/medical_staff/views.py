from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from user.models import User
from .forms import AthleteHealthRecordForm, MedicalFeedbackForm
from .models import AthleteHealthRecord, MedicalFeedback


def medical_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'medical':
            messages.error(request, 'Access denied. Medical staff only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@medical_required
def dashboard(request):
    athletes = User.objects.filter(role='athlete', is_active=True).order_by('name')
    latest_health_records = AthleteHealthRecord.objects.select_related('athlete').order_by('-created_at')[:12]
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
        'health_form': AthleteHealthRecordForm(),
        'feedback_form': MedicalFeedbackForm(),
    }
    return render(request, 'medical_staff/dashboard.html', context)


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
