from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

from user.models import User
from .models import Conversation, Message
from .forms import MessageForm, StartConversationForm


@login_required
def conversations_list(request):
    """List all conversations for the current user"""
    user = request.user
    
    # Get all conversations where user is either participant
    conversations = Conversation.objects.filter(
        Q(participant1=user) | Q(participant2=user)
    ).select_related('participant1', 'participant2')
    
    context = {
        'conversations': conversations,
        'total_conversations': conversations.count(),
    }
    return render(request, 'chat/conversations_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation and send messages"""
    user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is part of this conversation
    if conversation.participant1 != user and conversation.participant2 != user:
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('chat:conversations_list')
    
    # Get the other participant
    other_participant = conversation.participant2 if conversation.participant1 == user else conversation.participant1
    
    # Mark messages as read
    unread_messages = conversation.messages.filter(is_read=False).exclude(sender=user)
    unread_messages.update(is_read=True)
    
    # Get all messages
    chat_messages = conversation.messages.all().select_related('sender')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = user
            message.save()
            messages.success(request, 'Message sent!')
            return redirect('chat:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'other_participant': other_participant,
        'messages': chat_messages,
        'form': form,
    }
    return render(request, 'chat/conversation_detail.html', context)


@login_required
def conversation_messages(request, conversation_id):
    """Return the rendered message list for live polling."""
    user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if conversation.participant1 != user and conversation.participant2 != user:
        return JsonResponse({'error': 'forbidden'}, status=403)

    chat_messages = conversation.messages.all().select_related('sender')
    html = render_to_string(
        'chat/partials/message_list.html',
        {
            'messages': chat_messages,
            'user': user,
        },
        request=request,
    )
    latest_id = chat_messages.last().id if chat_messages.exists() else None
    return JsonResponse({'html': html, 'latest_message_id': latest_id})


@login_required
def start_conversation(request):
    """Start a new conversation with another user"""
    user = request.user
    
    if request.method == 'POST':
        # Get recipient from POST data
        recipient_id = request.POST.get('recipient_id')
        
        if not recipient_id:
            messages.error(request, 'Invalid recipient.')
            return redirect('chat:start_conversation')
        
        try:
            recipient = User.objects.get(id=recipient_id, is_active=True)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('chat:start_conversation')
        
        # Check if user is trying to message themselves
        if recipient == user:
            messages.error(request, 'You cannot message yourself.')
            return redirect('chat:start_conversation')
        
        # Check if conversation already exists
        conversation = Conversation.objects.filter(
            Q(participant1=user, participant2=recipient) |
            Q(participant1=recipient, participant2=user)
        ).first()
        
        if not conversation:
            # Create new conversation
            conversation = Conversation.objects.create(
                participant1=user,
                participant2=recipient
            )
            messages.success(request, f'Conversation with {recipient.name} started!')
        
        return redirect('chat:conversation_detail', conversation_id=conversation.id)
    
    # Get available recipients based on user role
    if user.role == 'athlete':
        # Athletes can message coaches and medical staff
        available_users = User.objects.filter(
            Q(role='coach') | Q(role='medical'),
            is_active=True
        ).exclude(id=user.id)
    elif user.role == 'coach':
        # Coaches can message athletes and medical staff
        available_users = User.objects.filter(
            Q(role='athlete') | Q(role='medical'),
            is_active=True
        ).exclude(id=user.id)
    elif user.role == 'medical':
        # Medical staff can message athletes and coaches
        available_users = User.objects.filter(
            Q(role='athlete') | Q(role='coach'),
            is_active=True
        ).exclude(id=user.id)
    else:
        available_users = User.objects.none()
    
    context = {
        'available_users': available_users,
    }
    return render(request, 'chat/start_conversation.html', context)


@login_required
def get_unread_count(request):
    """API endpoint to get unread message count for the current user"""
    user = request.user
    
    # Count unread messages for all conversations
    unread_count = Message.objects.filter(
        conversation__in=Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ),
        is_read=False
    ).exclude(sender=user).count()
    
    return JsonResponse({'unread_count': unread_count})
