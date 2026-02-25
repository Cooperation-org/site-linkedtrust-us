from django import forms
from .models import ContactInquiry


SUBJECT_CHOICES = [
    ('consulting', 'Consulting'),
    ('cloud_exit', 'Get Off the Cloud'),
    ('intern_placement', 'Intern Placement'),
    ('site_issue', 'Site Issue'),
    ('developer', 'Developer question'),
    ('other', 'Other'),
]


class ContactForm(forms.ModelForm):
    subject = forms.ChoiceField(choices=SUBJECT_CHOICES)

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
            'message': forms.Textarea(attrs={
                'placeholder': 'Tell us about your project, question, or idea...',
                'rows': 5,
            }),
        }
