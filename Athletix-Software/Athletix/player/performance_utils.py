import json
from collections import Counter
from datetime import datetime, time


def _routine_duration_minutes(routine):
    start = datetime.combine(datetime.today(), routine.start_time)
    end = datetime.combine(datetime.today(), routine.end_time)
    return max(int((end - start).total_seconds() / 60), 0)


def _performance_level(completion_rate):
    if completion_rate >= 90:
        return 'Elite'
    if completion_rate >= 75:
        return 'Strong'
    if completion_rate >= 50:
        return 'Developing'
    return 'Needs Focus'


def build_routine_performance_data(routines_queryset):
    routines = list(routines_queryset.select_related('sport', 'coach'))
    routine_rows = []
    date_totals = Counter()
    completed_by_date = Counter()
    sport_totals = Counter()
    date_labels = {}

    total_minutes = 0
    completed_count = 0

    for routine in routines:
        duration_minutes = _routine_duration_minutes(routine)
        routine.duration_minutes = duration_minutes
        routine_rows.append(routine)
        if routine.created_at:
            date_key = routine.created_at.date().isoformat()
            date_totals[date_key] += 1
            date_labels[date_key] = routine.created_at.strftime('%d %b %Y')
        else:
            date_key = 'unknown'
            date_totals[date_key] += 1
            date_labels[date_key] = 'Unknown date'
        sport_totals[routine.sport.name] += 1
        total_minutes += duration_minutes
        if routine.coach_approved_completion:
            completed_count += 1
            completed_by_date[date_key] += 1

    total_routines = len(routine_rows)
    completion_rate = round((completed_count / total_routines) * 100) if total_routines else 0
    incomplete_count = total_routines - completed_count
    total_hours = round(total_minutes / 60, 1)
    performance_level = _performance_level(completion_rate)

    sorted_dates = sorted(date_totals.keys())
    date_based_labels = [date_labels[date_key] for date_key in sorted_dates]
    date_based_total = [date_totals.get(date_key, 0) for date_key in sorted_dates]
    date_based_completed = [completed_by_date.get(date_key, 0) for date_key in sorted_dates]

    sport_labels = list(sport_totals.keys())
    sport_values = list(sport_totals.values())

    return {
        'routines': routine_rows,
        'recent_routines': sorted(routine_rows, key=lambda item: item.created_at, reverse=True)[:8],
        'total_routines': total_routines,
        'completed_count': completed_count,
        'incomplete_count': incomplete_count,
        'completion_rate': completion_rate,
        'total_hours': total_hours,
        'performance_level': performance_level,
        'weekly_chart_json': json.dumps({
            'labels': date_based_labels,
            'total': date_based_total,
            'completed': date_based_completed,
        }),
        'completion_chart_json': json.dumps({
            'labels': ['Completed', 'Incomplete'],
            'values': [completed_count, incomplete_count],
        }),
        'sport_chart_json': json.dumps({
            'labels': sport_labels,
            'values': sport_values,
        }),
    }
