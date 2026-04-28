from django.urls import path
from . import views

app_name = 'player'

urlpatterns = [
    path('dashboard/', views.player_dashboard, name='dashboard'),
    path('performance/', views.player_performance, name='performance'),
    path('profile/', views.player_profile, name='profile'),
    path('sports/', views.select_sports, name='select_sports'),
    path('coaches/', views.find_coaches, name='find_coaches'),
    path('coaches/request/<int:coach_id>/', views.request_coach, name='request_coach'),
    path('my-coaches/', views.my_coaches, name='my_coaches'),
    path('routine/', views.daily_routine, name='daily_routine'),
    path('routine/<int:routine_id>/', views.routine_detail, name='routine_detail'),
]
