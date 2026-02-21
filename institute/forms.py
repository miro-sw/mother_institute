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
        fields = '__all__'  # Make sure this includes all fields
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'academics_accommodation': forms.Textarea(attrs={'rows': 3}),
            'student_image': forms.FileInput(attrs={'accept': 'image/*'}),
            'admission_id': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'is_admitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),  # Add this
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for student_image field
        self.fields['student_image'].help_text = 'Accepted formats: JPG, PNG, GIF (Max 5MB)'
        self.fields['student_image'].required = False
        
        # Mark optional fields as not required
        optional_fields = [
            'enrolled_for', 'hostel_fees', 'admitted_college_fees',
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
        
        # Make sure is_admitted is not required (it has a default)
        if 'is_admitted' in self.fields:
            self.fields['is_admitted'].required = False
        
        
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
        
        

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'exam_type', 'subject', 'session', 'batch', 'stream', 'year',
                    'exam_date', 'start_time', 'end_time', 'total_marks', 'passing_marks',
                    'room_number', 'invigilator', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'batch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024-2025'}),
            'stream': forms.Select(attrs={'class': 'form-select'}),  # This will now show dropdown
            'year': forms.Select(attrs={'class': 'form-select'}),      # This will now show dropdown
            'exam_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invigilator': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices for stream and year fields
        self.fields['stream'].choices = Exam.STREAM_CHOICES
        self.fields['year'].choices = Exam.YEAR_CHOICES

class StudentResultForm(forms.ModelForm):
    class Meta:
        model = StudentResult
        fields = ['marks_obtained', 'is_absent', 'remarks']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
            }),
            'is_absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional remarks'}),
        }


class BulkResultEntryForm(forms.Form):
    """Form for bulk entry of results for multiple students"""
    exam_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        students = kwargs.pop('students', [])
        exam = kwargs.pop('exam', None)
        super().__init__(*args, **kwargs)
        
        for student in students:
            field_name = f'marks_{student.id}'
            absent_field = f'absent_{student.id}'
            
            # Try to get existing result
            existing_result = None
            if exam:
                existing_result = StudentResult.objects.filter(
                    exam=exam, 
                    student=student
                ).first()
            
            initial_value = existing_result.marks_obtained if existing_result and not existing_result.is_absent else ''
            initial_absent = existing_result.is_absent if existing_result else False
            
            self.fields[field_name] = forms.DecimalField(
                label=f"{student.student_name}",
                required=False,
                min_value=0,
                max_value=exam.total_marks if exam else 100,
                decimal_places=2,
                initial=initial_value,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control form-control-sm marks-input',
                    'placeholder': 'Marks',
                    'data-student-id': student.id
                })
            )
            
            self.fields[absent_field] = forms.BooleanField(
                label="Absent",
                required=False,
                initial=initial_absent,
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input absent-checkbox',
                    'data-student-id': student.id
                })
            )