from django import forms
from .models import StudentAdmission, Content, Branch, Chapter, ContactMessage

class AdmissionForm(forms.ModelForm):
    class Meta:
        model = StudentAdmission
        fields = ['full_name', 'email', 'phone', 'category', 'year', 'branch']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'year': forms.Select(attrs={'class': 'form-select', 'id': 'id_year'}),
            'branch': forms.Select(attrs={'class': 'form-select', 'id': 'id_branch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].required = False
        self.fields['branch'].queryset = Branch.objects.all().order_by('name')

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['chapter', 'title', 'description', 'content_type', 'file', 'video_url']
        widgets = {
            'chapter': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Content Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description'}),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'YouTube URL'}),
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Topic of Inquiry'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'How can we help you?'}),
        }

class CommonPasswordForm(forms.Form):

    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
