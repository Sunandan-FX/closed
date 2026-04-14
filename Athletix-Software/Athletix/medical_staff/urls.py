from django.urls import path

from . import views

app_name = 'medical_staff'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('health-records/add/', views.add_health_record, name='add_health_record'),
    path('feedback/add/', views.add_feedback, name='add_feedback'),
]

