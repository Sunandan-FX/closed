from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """Model to represent a conversation between two users"""
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_initiated'
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_received'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_conversation'
        ordering = ['-updated_at']
        unique_together = ('participant1', 'participant2')

    def __str__(self):
        return f"{self.participant1.name} - {self.participant2.name}"

    @property
    def last_message(self):
        """Get the last message in the conversation"""
        return self.messages.order_by('-created_at').first()

    @property
    def unread_count(self, user):
        """Count unread messages for a user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """Model to represent individual messages in a conversation"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.name}: {self.content[:50]}"
