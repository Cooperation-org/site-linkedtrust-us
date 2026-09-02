from django import forms
from django.db import models
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


from .models import LevelUpRegistration, LevelUpAccessCode


class LevelUpRegistrationForm(forms.ModelForm):
    help_with = forms.MultipleChoiceField(
        choices=LevelUpRegistration.HELP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': 'Pick at least one thing you want help with.'},
    )
    tier = forms.ChoiceField(
        choices=LevelUpRegistration.TIER_CHOICES,
        widget=forms.RadioSelect,
        initial='free_small',
    )
    code = forms.CharField(
        required=False, max_length=40,
        widget=forms.TextInput(attrs={'placeholder': 'Optional', 'autocomplete': 'off', 'autocapitalize': 'characters'}),
    )
    # Honeypot: real people never see or fill this.
    company_fax = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = LevelUpRegistration
        fields = ['name', 'email', 'organization', 'link', 'help_with', 'goal', 'wants_checkin', 'tier']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name', 'autocomplete': 'name', 'required': True}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com', 'autocomplete': 'email', 'required': True}),
            'organization': forms.TextInput(attrs={'placeholder': 'Company, project or idea', 'autocomplete': 'organization', 'required': True}),
            'link': forms.URLInput(attrs={'placeholder': 'https://', 'autocomplete': 'url'}),
            'goal': forms.Textarea(attrs={'rows': 3, 'maxlength': 600, 'required': True,
                                          'placeholder': 'One or two lines. What is stuck, or what do you want live by the end of the month?'}),
        }
        labels = {
            'organization': 'Company or project',
            'link': 'Link to your site, deck or docs',
            'goal': 'What do you want to walk out with?',
            'wants_checkin': 'I would like a 15-minute 1-1 check-in before the workshop',
            'tier': 'Pricing',
        }

    def clean_company_fax(self):
        if self.cleaned_data.get('company_fax'):
            raise forms.ValidationError('Spam check failed.')
        return ''

    def clean_help_with(self):
        return ','.join(self.cleaned_data['help_with'])

    def clean_code(self):
        raw = (self.cleaned_data.get('code') or '').strip().upper()
        if not raw:
            return None
        try:
            code = LevelUpAccessCode.objects.get(code=raw)
        except LevelUpAccessCode.DoesNotExist:
            raise forms.ValidationError('That code is not recognised. Check it, or leave it blank.')
        if not code.usable:
            raise forms.ValidationError('That code is no longer active.')
        return code

    def save(self, commit=True):
        reg = super().save(commit=False)
        code = self.cleaned_data.get('code')
        if code:
            reg.access_code = code
            reg.payment_status = 'free'
        elif reg.tier == 'paid':
            reg.payment_status = 'pending'
        else:
            reg.payment_status = 'free'
        if commit:
            reg.save()
            if code:
                LevelUpAccessCode.objects.filter(pk=code.pk).update(uses=models.F('uses') + 1)
        return reg
