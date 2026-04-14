# Generated migration to add initial sports data

from django.db import migrations


def create_initial_sports(apps, schema_editor):
    Sport = apps.get_model('player', 'Sport')
    
    sports = [
        {'name': 'Football', 'description': 'Team sport played with a spherical ball', 'icon': '⚽'},
        {'name': 'Cricket', 'description': 'Bat and ball game played between two teams', 'icon': '🏏'},
        {'name': 'Basketball', 'description': 'Team sport played on a rectangular court', 'icon': '🏀'},
        {'name': 'Volleyball', 'description': 'Team sport with a ball over a net', 'icon': '🏐'},
        {'name': 'Badminton', 'description': 'Racket sport using a shuttlecock', 'icon': '🏸'},
        {'name': 'Table Tennis', 'description': 'Racket sport played on a table (T-T Table)', 'icon': '🏓'},
        {'name': 'Athletics', 'description': 'Track and field events', 'icon': '🏃'},
        {'name': 'Chess', 'description': 'Strategic board game for two players', 'icon': '♟️'},
        {'name': 'Karate', 'description': 'Japanese martial art focusing on striking techniques', 'icon': '🥋'},
    ]
    
    for sport_data in sports:
        Sport.objects.get_or_create(name=sport_data['name'], defaults=sport_data)


def remove_initial_sports(apps, schema_editor):
    Sport = apps.get_model('player', 'Sport')
    Sport.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_sports, remove_initial_sports),
    ]
