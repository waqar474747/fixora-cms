from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, Button, HTML
from .models import Complaint, ComplaintFeedback, Category, Department, STATUS_CHOICES, PRIORITY_CHOICES
from app.accounts.models import UserProfile


class ComplaintForm(forms.ModelForm):
    """Form for submitting a new complaint"""
    
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'department', 'priority', 'is_anonymous',
                  'attachment', 'photo', 'document']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter complaint title',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your complaint in detail',
                'rows': 5
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.gif,.doc,.docx'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/webp'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Fieldset(
                'Submit Your Complaint',
                Row(
                    Column('title', css_class='col-md-12'),
                ),
                Row(
                    Column('category', css_class='col-md-6'),
                    Column('department', css_class='col-md-6'),
                ),
                Row(
                    Column('priority', css_class='col-md-6'),
                    Column('is_anonymous', css_class='col-md-6 d-flex align-items-center'),
                ),
                Row(
                    Column('description', css_class='col-md-12'),
                ),
                Row(
                    Column('photo', css_class='col-md-6'),
                    Column('document', css_class='col-md-6'),
                ),
                Row(
                    Column('attachment', css_class='col-md-12'),
                ),
                css_class='mb-3'
            ),
            Submit('submit', 'Submit Complaint', css_class='btn btn-primary btn-lg'),
            HTML('<a href="/dashboard/" class="btn btn-secondary btn-lg ms-2">Cancel</a>')
        )


class ComplaintFilterForm(forms.Form):
    """Form for filtering complaints"""
    FILTER_STATUS_CHOICES = [('', 'All Status')] + STATUS_CHOICES
    FILTER_PRIORITY_CHOICES = [('', 'All Priority')] + [c for c in PRIORITY_CHOICES]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by ID, title, or category'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=FILTER_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        required=False,
        choices=FILTER_PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Categories'
    )
    department = forms.ModelChoiceField(
        required=False,
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Departments'
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class ComplaintStatusUpdateForm(forms.ModelForm):
    """Form for updating complaint status (Admin only)"""
    
    class Meta:
        model = Complaint
        fields = ['status', 'admin_remarks', 'assigned_to']
        help_texts = {
            'status': 'SUBMITTED → PENDING → UNDER_REVIEW → IN_PROGRESS → RESOLVED / REJECTED',
        }
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add remarks about this complaint'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter assigned_to to show only staff members
        self.fields['assigned_to'].queryset = User.objects.filter(
            profile__role__in=['STAFF', 'ADMIN']
        )


class ComplaintEditForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'priority', 'attachment', 'photo', 'document']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter complaint title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your complaint'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp'}),
            'document': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'


class ComplaintFeedbackForm(forms.ModelForm):
    """Form for complaint feedback/rating"""
    
    class Meta:
        model = ComplaintFeedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=ComplaintFeedback.RATING_CHOICES, attrs={
                'class': 'form-check-input'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your feedback about the resolution'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Rate Your Experience',
                'rating',
                'comment',
            ),
            Submit('submit', 'Submit Feedback', css_class='btn btn-primary'),
        )





