# models.py - COMPLETE UPDATED FILE
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
        ('student', 'Student'),
    )
    
    uid = models.CharField(max_length=50, unique=True, blank=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Generate uid if not already set
        if not self.uid:
            # Generate a unique uid, e.g., using username or a random string
            import uuid
            self.uid = str(uuid.uuid4())[:8].upper()  # Example: first 8 chars of UUID, uppercase
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} - {self.user_type}"

class Admission(models.Model):
    # Custom Admission ID Field
    admission_id = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Admission ID")
    
    # Student Image Field
    student_image = models.ImageField(upload_to='student_images/', blank=True, null=True, verbose_name="Student Photo")
    
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    mobile_number = models.CharField(max_length=15)
    address = models.TextField()
    adhaar_number = models.CharField(max_length=20)
    whatsapp_number = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=5)
    category = models.CharField(max_length=50)
    
    # College details
    college_name = models.CharField(max_length=200)
    board_name = models.CharField(max_length=100)
    college_roll_no = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    eleventh_year = models.CharField(max_length=10)
    twelfth_year = models.CharField(max_length=10)
    course = models.CharField(max_length=100)
    
    # Enrollment
    enrolled_for = models.CharField(max_length=100, blank=True, null=True)
    sams_login_id = models.CharField(max_length=100, blank=True)
    sams_password = models.CharField(max_length=100, blank=True)
    pen_number = models.CharField(max_length=100, blank=True)
    apaar_id = models.CharField(max_length=100, blank=True)
    
    # Visitors
    visitor1_name = models.CharField(max_length=100, blank=True)
    visitor1_relation = models.CharField(max_length=100, blank=True)
    visitor1_contact = models.CharField(max_length=15, blank=True)
    visitor2_name = models.CharField(max_length=100, blank=True)
    visitor2_relation = models.CharField(max_length=100, blank=True)
    visitor2_contact = models.CharField(max_length=15, blank=True)
    
    # Fees and facilities
    hostel_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    academics_accommodation = models.TextField(blank=True)
    admitted_college_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    college_dress = models.CharField(max_length=100, blank=True)
    books = models.CharField(max_length=100, blank=True)
    college_transportation = models.CharField(max_length=100, blank=True)
    tms_dress = models.CharField(max_length=100, blank=True)
    
    # Installments
    installment1 = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    installment2 = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    installment3 = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    installment4 = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    installment5 = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    installment6 = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    
    tms_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    
    # Signatures (in real app, these would be FileFields)
    guardian_signature = models.CharField(max_length=100, blank=True)
    student_signature = models.CharField(max_length=100, blank=True)
    tms_signature = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    # New fields to separate registration vs actual admission
    is_admitted = models.BooleanField(default=False, verbose_name="Admitted")
    admission_date = models.DateField(null=True, blank=True)
    admitted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='admitted_students')
    
    def save(self, *args, **kwargs):
        # Generate custom admission ID if not already set (only for new records)
        if not self.admission_id and not self.pk:
            # Get the last admission to determine next number (only for new records)
            last_admission = Admission.objects.order_by('-id').first()
            if last_admission and last_admission.admission_id:
                try:
                    # Extract number from existing ID
                    last_number = int(last_admission.admission_id[4:])  # Extract after "TMIS"
                    next_number = last_number + 1
                except:
                    next_number = 1
            else:
                next_number = 1
            
            # Format: TMIS0001, TMIS0002, etc.
            self.admission_id = f"TMIS{next_number:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        admission_id_display = self.admission_id if self.admission_id else f"ID:{self.id}"
        return f"{admission_id_display} - {self.student_name} - {self.enrolled_for}"
    
    
    
class Expense(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='expenses')
    date=models.DateField()
    category = models.CharField(max_length=100, choices =[
        ('food', 'Fooding'),
        ('transport', 'Transportation'),
        ('hostel', 'Hostel Fee'),
        ('academic', 'Academic Material'),
        ('other', 'Other'),
    ])
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admission.admission_id} - {self.category} - ₹{self.amount}"


class Payment(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Transfer'),
        ('card', 'Card')
    ])
    payment_type = models.CharField(max_length=50, choices=[
        ('tuition', 'Tuition Fee'),
        ('food', 'Fooding'),
        ('hostel', 'Hostel Fee'),
        ('transport', 'Transportation'),
        ('library', 'Library'),
        ('other', 'Other')
    ])
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    received_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Generate receipt number if not provided
        if not self.receipt_number:
            # Get the last payment to determine next number
            last_payment = Payment.objects.order_by('-id').first()
            if last_payment and last_payment.receipt_number:
                try:
                    # Extract number from existing receipt number
                    last_number = int(last_payment.receipt_number[5:])  # Extract after "RECPT"
                    next_number = last_number + 1
                except:
                    next_number = 1
            else:
                next_number = 1
            
            # Format: RECPT0001, RECPT0002, etc.
            self.receipt_number = f"RECPT{next_number:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.admission.admission_id} - ₹{self.amount} - {self.payment_type}"
    
class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Organization Name") 
    logo = models.ImageField(upload_to='organization_logos/', null=True, blank=True, verbose_name="Logo")
    address = models.TextField(verbose_name="Address")
    mobile = models.CharField(max_length=15, verbose_name="Mobile Number")
    email = models.EmailField(verbose_name="Email Address")
    registration_number = models.CharField(max_length=100, unique=True, verbose_name="Registration Number")
    registration_date = models.DateField(null=True, blank=True, verbose_name="Registration Date")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Contact Person")
    organization_type = models.CharField(max_length=100, blank=True, verbose_name="Organization Type")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    status = models.CharField(
        max_length=20, 
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive')
        ], 
        default='active',
        verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self): 
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"


# Remove the entire Subject model class
# Keep only Exam, ExamSchedule, StudentResult, and ExamAttendance models

class Exam(models.Model):
    """Exam model"""
    EXAM_TYPE_CHOICES = [
        ('weekly', 'Weekly Test'),
        ('monthly', 'Monthly Test'),
        ('quarterly', 'Quarterly Exam'),
        ('half_yearly', 'Half Yearly Exam'),
        ('annual', 'Annual Exam'),
        ('pre_board', 'Pre-Board Exam'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    SESSION_CHOICES = [
        ('morning', 'Morning Session (8 AM - 11 AM)'),
        ('afternoon', 'Afternoon Session (12 PM - 3 PM)'),
        ('evening', 'Evening Session (4 PM - 7 PM)'),
    ]
    
    SUBJECT_CHOICES = [
        # 11th Science Subjects
        ('physics_11', 'Physics (11th Science)'),
        ('chemistry_11', 'Chemistry (11th Science)'),
        ('mathematics_11', 'Mathematics (11th Science)'),
        ('biology_11', 'Biology (11th Science)'),
        ('english_11', 'English (11th Science)'),
        
        # 12th Science Subjects
        ('physics_12', 'Physics (12th Science)'),
        ('chemistry_12', 'Chemistry (12th Science)'),
        ('mathematics_12', 'Mathematics (12th Science)'),
        ('biology_12', 'Biology (12th Science)'),
        ('english_12', 'English (12th Science)'),
    ]
    
    STREAM_CHOICES = [
        ('science', 'Science'),
        ('commerce', 'Commerce'),
        ('arts', 'Arts'),
    ]
    
    YEAR_CHOICES = [
        ('11th', '11th Class'),
        ('12th', '12th Class'),
    ]
    
    name = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default='monthly')
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='physics_11')
    session = models.CharField(max_length=20, choices=SESSION_CHOICES, default='morning')
    batch = models.CharField(max_length=50, help_text="Batch year (e.g., 2024-2025)")
    stream = models.CharField(max_length=20, choices=STREAM_CHOICES, default='science')  # Added choices
    year = models.CharField(max_length=10, choices=YEAR_CHOICES, default='11th')  # Added choices
    exam_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=33)
    room_number = models.CharField(max_length=50, blank=True)
    invigilator = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} - {self.batch}"
    
    class Meta:
        ordering = ['-exam_date']


class StudentResult(models.Model):
    """Student marks for each exam"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    student = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='exam_results')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    is_absent = models.BooleanField(default=False)
    remarks = models.CharField(max_length=255, blank=True)
    entered_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        ordering = ['exam__exam_date', 'student__student_name']
    
    def __str__(self):
        status = "Absent" if self.is_absent else f"Marks: {self.marks_obtained}"
        return f"{self.student.student_name} - {self.exam.get_subject_display() if self.exam else 'No Exam'} - {status}"
    
    @property
    def percentage(self):
        if self.exam and self.exam.total_marks > 0 and not self.is_absent:
            return (self.marks_obtained / self.exam.total_marks) * 100
        return 0
    
    @property
    def grade(self):
        if self.is_absent:
            return "AB"
        percentage = self.percentage
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B+"
        elif percentage >= 60:
            return "B"
        elif percentage >= 50:
            return "C"
        elif percentage >= 33:
            return "D"
        else:
            return "F"


class ExamAttendance(models.Model):
    """Track which students appeared for which exam"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attendance')
    student = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='exam_attendance')
    is_present = models.BooleanField(default=True)
    marked_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['exam', 'student']
    
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.student_name} - {self.exam.name} - {status}"