from django import forms
from .models import Message, Conversation


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Type your message here...',
                'style': 'resize: vertical;'
            })
        }


class StartConversationForm(forms.Form):
    recipient = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter recipient name or email'
        })
    )
