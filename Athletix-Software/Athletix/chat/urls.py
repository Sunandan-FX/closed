from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversations_list, name='conversations_list'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:conversation_id>/messages/', views.conversation_messages, name='conversation_messages'),
    path('start/', views.start_conversation, name='start_conversation'),
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
]
