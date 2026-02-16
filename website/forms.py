from django import forms
from .models import ContactInquiry


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactInquiry
        fields = ['email', 'name', 'subject', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'you@example.com',
                'required': True,
                'autocomplete': 'email',
            }),
            'name': forms.TextInput(attrs={
                'placeholder': 'Your name',
                'autocomplete': 'name',
            }),
            'subject': forms.Select(attrs={}),
            'message': forms.Textarea(attrs={
                'placeholder': 'Tell us about your project, question, or idea...',
                'rows': 5,
            }),
        }
