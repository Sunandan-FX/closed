from django.urls import path

from . import views

app_name = 'admin_app'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('users/', views.users_view, name='users'),
    path('players/', views.players_view, name='players'),
    path('coaches/', views.coaches_view, name='coaches'),
    path('users/<int:user_id>/edit/', views.edit_user_view, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status_view, name='toggle_user_status'),
    path('approve-coach/<int:user_id>/', views.approve_coach_view, name='approve_coach'),
]

