import os
import re

from django import forms
from django.core.exceptions import ValidationError

CATEGORIES = [
    ('Python', 'Python'),
    ('Django', 'Django'),
    ('Database', 'Database'),
    ('Assignment', 'Assignment'),
    ('Other', 'Other'),
]

SEVERITIES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),
    ('Critical', 'Critical'),
]

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
MAX_SCREENSHOT_SIZE = 2 * 1024 * 1024  # 2 MB
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
JPEG_SIGNATURE = b'\xff\xd8\xff'
EMAIL_PATTERN = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')


class TicketForm(forms.Form):
    trainee_name = forms.CharField(
        max_length=100,
        label='Trainee Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your name',
        }),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
        }),
    )
    category = forms.ChoiceField(
        choices=CATEGORIES,
        label='Category',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    severity = forms.ChoiceField(
        choices=SEVERITIES,
        label='Severity',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    description = forms.CharField(
        label='Description',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe your issue (minimum 20 characters)',
        }),
    )
    screenshot = forms.FileField(
        required=False,
        label='Screenshot (optional, PNG/JPG, max 2 MB)',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    def clean_trainee_name(self):
        name = self.cleaned_data['trainee_name'].strip()
        if len(name) < 2:
            raise ValidationError('Name must contain at least 2 characters.')
        return name

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise ValidationError('Enter a valid email address.')
        return email

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if len(description) < 20:
            raise ValidationError(
                'Description must contain at least 20 characters.'
            )
        return description

    def clean_screenshot(self):
        screenshot = self.cleaned_data.get('screenshot')
        if not screenshot:          # optional field
            return None

        ext = os.path.splitext(screenshot.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError('Only PNG, JPG and JPEG files are allowed.')

        if screenshot.size > MAX_SCREENSHOT_SIZE:
            raise ValidationError('Screenshot must not exceed 2 MB.')

        # Check the real file signature, not just the extension.
        header = screenshot.read(8)
        screenshot.seek(0)
        is_png = header.startswith(PNG_SIGNATURE)
        is_jpeg = header.startswith(JPEG_SIGNATURE)
        if ext == '.png' and not is_png:
            raise ValidationError('File content is not a valid PNG image.')
        if ext in ('.jpg', '.jpeg') and not is_jpeg:
            raise ValidationError('File content is not a valid JPEG image.')

        return screenshot
