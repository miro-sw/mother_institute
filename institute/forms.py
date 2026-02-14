from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import * 

class UserRegistrationForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, required=True)
    # uid is now auto-generated, so remove from form
    
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'user_type']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove help text ONLY for username field
        self.fields['username'].help_text = ''
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    


class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'academics_accommodation': forms.Textarea(attrs={'rows': 3}),
            'student_image': forms.FileInput(attrs={'accept': 'image/*'}),
            'admission_id': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for student_image field
        self.fields['student_image'].help_text = 'Accepted formats: JPG, PNG, GIF (Max 5MB)'
        self.fields['student_image'].required = False
        
        # Mark optional fields as not required
        optional_fields = [
            'enrolled_for', 'hostel_fees', 'admitted_college_fees',
            'installment1', 'installment2', 'installment3', 
            'installment4', 'installment5', 'installment6',
            'tms_fees', 'sams_login_id', 'sams_password',
            'pen_number', 'apaar_id', 'college_dress', 'books',
            'college_transportation', 'tms_dress', 'academics_accommodation',
            'visitor1_name', 'visitor1_relation', 'visitor1_contact',
            'visitor2_name', 'visitor2_relation', 'visitor2_contact',
            'guardian_signature', 'student_signature', 'tms_signature'
        ]
        
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False
        
        
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['date', 'payment_method', 'payment_type', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
        
class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'logo', 'address', 'mobile', 'email', 
                    'registration_number', 'registration_date',
                    'contact_person', 'organization_type', 'remarks', 'status']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'logo': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['logo'].help_text = 'Recommended size: 200x200px, Max size: 2MB'