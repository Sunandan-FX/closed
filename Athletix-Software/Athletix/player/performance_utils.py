import json
from collections import Counter
from datetime import datetime, time

DAY_ORDER = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
]

DAY_LABELS = {
    'monday': 'Mon',
    'tuesday': 'Tue',
    'wednesday': 'Wed',
    'thursday': 'Thu',
    'friday': 'Fri',
    'saturday': 'Sat',
    'sunday': 'Sun',
}


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
    day_totals = Counter()
    completed_by_day = Counter()
    sport_totals = Counter()

    total_minutes = 0
    completed_count = 0

    for routine in routines:
        duration_minutes = _routine_duration_minutes(routine)
        routine.duration_minutes = duration_minutes
        routine_rows.append(routine)
        day_totals[routine.day] += 1
        sport_totals[routine.sport.name] += 1
        total_minutes += duration_minutes
        if routine.coach_approved_completion:
            completed_count += 1
            completed_by_day[routine.day] += 1

    total_routines = len(routine_rows)
    completion_rate = round((completed_count / total_routines) * 100) if total_routines else 0
    incomplete_count = total_routines - completed_count
    total_hours = round(total_minutes / 60, 1)
    performance_level = _performance_level(completion_rate)

    weekly_labels = [DAY_LABELS[day] for day in DAY_ORDER]
    weekly_total = [day_totals.get(day, 0) for day in DAY_ORDER]
    weekly_completed = [completed_by_day.get(day, 0) for day in DAY_ORDER]

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
            'labels': weekly_labels,
            'total': weekly_total,
            'completed': weekly_completed,
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
