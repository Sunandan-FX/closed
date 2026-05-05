from django.urls import path
from . import views

app_name = 'coach'

urlpatterns = [
    path('dashboard/', views.coach_dashboard, name='dashboard'),
    path('performance/', views.performance_search, name='performance'),
    path('profile/', views.coach_profile, name='profile'),
    path('requests/', views.athlete_requests, name='athlete_requests'),
    path('requests/<int:request_id>/<str:action>/', views.handle_request, name='handle_request'),
    path('athletes/', views.my_athletes, name='my_athletes'),
    path('athletes/<int:athlete_id>/', views.athlete_detail, name='athlete_detail'),
    path('routine/create/', views.create_routine_select, name='create_routine_select'),
    path('athletes/<int:athlete_id>/routine/create/', views.create_routine, name='create_routine'),
    path('routine/<int:routine_id>/edit/', views.edit_routine, name='edit_routine'),
    path('routine/<int:routine_id>/delete/', views.delete_routine, name='delete_routine'),
    path('routine/<int:routine_id>/approve-completion/', views.approve_routine_completion, name='approve_routine_completion'),
]
