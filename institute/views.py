# views.py - UPDATE THE search_admission VIEW AND ADD HELPER FUNCTIONS

from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from .models import *
from .forms import *
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import  A4, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io
import json
import re
from datetime import datetime,date
from django.utils import timezone


@login_required
def toggle_admit(request, admission_id):
    """Toggle or set admission.is_admitted via AJAX POST.
    Expects JSON body: { "is_admitted": true/false } or will toggle if missing.
    Returns JSON errors (no redirects) so client can handle them.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    # Permission: allow admin user_type or staff flag
    user = request.user
    if not (getattr(user, 'user_type', None) == 'admin' or getattr(user, 'is_staff', False)):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        admission = get_object_or_404(Admission, id=admission_id)

        # parse JSON body
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except Exception:
            payload = {}

        # determine desired state
        if 'is_admitted' in payload:
            desired = bool(payload.get('is_admitted'))
        else:
            desired = not admission.is_admitted

        admission.is_admitted = desired
        if desired:
            admission.admitted_by = request.user
            # set admission_date if not already
            if not admission.admission_date:
                admission.admission_date = timezone.now().date()
        else:
            admission.admitted_by = None
            admission.admission_date = None

        admission.save()

        return JsonResponse({'success': True, 'is_admitted': admission.is_admitted, 'admission_id': admission.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def home(request):
    return render(request, 'institute/index.html')

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = UserLoginForm()
    return render(request, 'institute/login.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # In a real application, you would send a password reset email here
        messages.success(request, 'Password reset link has been sent to your email')
        return redirect('login')
    return render(request, 'institute/forgot_password.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
@staff_member_required
def register_organization(request):
    if request.method == 'POST':
        # Handle form submission
        org_name = request.POST.get('org_name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        regd_no = request.POST.get('regd_no')
        
        # Handle logo upload
        if 'org_logo' in request.FILES:
            logo_file = request.FILES['org_logo']
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/svg+xml']
            if logo_file.content_type not in allowed_types:
                messages.error(request, 'Invalid file type. Please upload an image file.')
                return render(request, 'institute/register_organization.html')
            
            # Validate file size (5MB max)
            if logo_file.size > 5 * 1024 * 1024:
                messages.error(request, 'File size exceeds 5MB limit.')
                return render(request, 'institute/register_organization.html')
            
            # Save the file
            # fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'organization_logos'))
            # filename = fs.save(f"{regd_no.replace('/', '_')}_{logo_file.name}", logo_file)
            # logo_url = fs.url(filename)
            
            # Save logo URL to database or process it
            # Your logic here...
        
        # Save other form data to database
        # Your logic here...
        
        messages.success(request, 'Organization registered successfully!')
        return redirect('admin_dashboard')
    
    return render(request, 'institute/register_organization.html')


@login_required
def account_section(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    
    # IMPORTANT FIX: Only show admitted students (is_admitted = True)
    admissions = Admission.objects.filter(is_admitted=True)
    
    if search_query:
        admissions = admissions.filter(
            Q(student_name__icontains=search_query) |
            Q(admission_id__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    # Calculate totals for each admission
    admission_data = []
    total_payments_sum = 0
    total_expenses_sum = 0
    
    for admission in admissions:
        total_expenses = Expense.objects.filter(admission=admission).aggregate(Sum('amount'))['amount__sum'] or 0
        total_payments = Payment.objects.filter(admission=admission).aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_payments - total_expenses

        # Total fee calculation (tms fees + college fees + hostel fees)
        total_fee = (admission.tms_fees or 0) + (admission.admitted_college_fees or 0) + (admission.hostel_fees or 0)
        due_amount = total_fee - total_payments
        
        total_payments_sum += total_payments
        total_expenses_sum += total_expenses
        
        admission_data.append({
            'admission': admission,
            'total_expenses': total_expenses,
            'total_payments': total_payments,
            'balance': balance,
            'total_fee': total_fee,
            'due_amount': due_amount,
            'expenses_count': Expense.objects.filter(admission=admission).count(),
            'payments_count': Payment.objects.filter(admission=admission).count(),
        })
    
    net_balance = total_payments_sum - total_expenses_sum
    
    # Add count of admitted students
    admitted_count = admissions.count()
    
    context = {
        'admission_data': admission_data,
        'search_query': search_query,
        'total_payments_sum': total_payments_sum,
        'total_expenses_sum': total_expenses_sum,
        'net_balance': net_balance,
        'admitted_count': admitted_count,  # Add this to template
    }
    return render(request, 'institute/account_section.html', context)


@login_required
def account_search_view(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category = request.GET.get('category', '')
    
    # IMPORTANT FIX: Only show admitted students
    admissions = Admission.objects.filter(is_admitted=True)
    
    if search_query:
        admissions = admissions.filter(
            Q(student_name__icontains=search_query) |
            Q(admission_id__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    # Calculate totals for each admission with filters
    admission_data = []
    total_payments_sum = 0
    total_expenses_sum = 0
    
    for admission in admissions:
        expenses = Expense.objects.filter(admission=admission)
        payments = Payment.objects.filter(admission=admission)
        
        # Apply date filters if provided
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                expenses = expenses.filter(date__gte=from_date)
                payments = payments.filter(date__gte=from_date)
            except:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                expenses = expenses.filter(date__lte=to_date)
                payments = payments.filter(date__lte=to_date)
            except:
                pass
        
        # Apply category filter if provided
        if category:
            if category.startswith('expense_'):
                expense_category = category.replace('expense_', '')
                expenses = expenses.filter(category=expense_category)
            elif category.startswith('payment_'):
                payment_category = category.replace('payment_', '')
                payments = payments.filter(payment_type=payment_category)
        
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_payments - total_expenses
        
        total_payments_sum += total_payments
        total_expenses_sum += total_expenses
        
        admission_data.append({
            'admission': admission,
            'total_expenses': total_expenses,
            'total_payments': total_payments,
            'balance': balance,
            'expenses_count': expenses.count(),
            'payments_count': payments.count()
        })
    
    net_balance = total_payments_sum - total_expenses_sum
    
    context = {
        'admission_data': admission_data,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'category': category,
        'total_payments_sum': total_payments_sum,
        'total_expenses_sum': total_expenses_sum,
        'total_balance': net_balance, 
        'net_balance': net_balance,
        'total_admissions': Admission.objects.filter(is_admitted=True).count(),  # Total admitted count
        'expense_categories': Expense._meta.get_field('category').choices,
        'payment_categories': Payment._meta.get_field('payment_type').choices,
    }
    return render(request, 'institute/account_search.html', context)


@login_required
def student_account(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    expenses = Expense.objects.filter(admission=admission).order_by('-date')
    payments = Payment.objects.filter(admission=admission).order_by('-date')
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_payments - total_expenses

    # Total fee and due amount for this student
    total_fee = (admission.tms_fees or 0) + (admission.admitted_college_fees or 0) + (admission.hostel_fees or 0)
    due_amount = total_fee - total_payments
    
    # Expenses by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'admission': admission,
        'expenses': expenses,
        'payments': payments,
        'total_expenses': total_expenses,
        'total_payments': total_payments,
        'balance': balance,
        'total_fee': total_fee,
        'due_amount': due_amount,
        'expenses_by_category': expenses_by_category,
    }
    return render(request, 'institute/student_account.html', context)

@login_required
def add_expense(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.admission = admission
            expense.added_by = request.user
            expense.save()
            messages.success(request, f'Expense of ₹{expense.amount} added successfully!')
            return redirect('student_account', admission_id=admission_id)
    else:
        form = ExpenseForm()
    
    return render(request, 'institute/add_expense.html', {
        'form': form,
        'admission': admission
    })

@login_required
def add_payment(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.admission = admission
            payment.received_by = request.user
            payment.save()
            messages.success(request, f'Payment of ₹{payment.amount} recorded successfully! Receipt: {payment.receipt_number}')
            return redirect('student_account', admission_id=admission_id)
    else:
        form = PaymentForm()
    
    return render(request, 'institute/add_payment.html', {
        'form': form,
        'admission': admission
    })

@login_required
def add_expense_general(request):
    """Add expense with student selection"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = None
    selected_admission_id = request.GET.get('admission_id') or request.POST.get('admission_id')
    
    if selected_admission_id:
        try:
            admission = Admission.objects.get(id=selected_admission_id)
        except Admission.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    if request.method == 'POST' and admission:
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.admission = admission
            expense.added_by = request.user
            expense.save()
            messages.success(request, f'Expense of ₹{expense.amount} added successfully!')
            return redirect('student_account', admission_id=admission.id)
    else:
        form = ExpenseForm()
    
    # Get all students for selection
    students = Admission.objects.all().order_by('student_name')
    
    context = {
        'form': form,
        'admission': admission,
        'students': students,
        'title': 'Add Expense'
    }
    return render(request, 'institute/add_expense_general.html', context)

@login_required
def add_payment_general(request):
    """Add payment with student selection"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = None
    selected_admission_id = request.GET.get('admission_id') or request.POST.get('admission_id')
    
    if selected_admission_id:
        try:
            admission = Admission.objects.get(id=selected_admission_id)
        except Admission.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    if request.method == 'POST' and admission:
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.admission = admission
            payment.received_by = request.user
            payment.save()
            messages.success(request, f'Payment of ₹{payment.amount} recorded successfully! Receipt: {payment.receipt_number}')
            return redirect('student_account', admission_id=admission.id)
    else:
        form = PaymentForm()
    
    # Get all students for selection
    students = Admission.objects.all().order_by('student_name')
    
    context = {
        'form': form,  
        'admission': admission,
        'students': students,
        'title': 'Add Payment'
    }
    return render(request, 'institute/add_payment_general.html', context)

@login_required
def get_student_details(request):
    """API endpoint to get student details by ID - for AJAX requests"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    student_id = request.GET.get('id')
    search_term = request.GET.get('search')
    
    students_query = Admission.objects.all()
    
    # Search by admission ID
    if student_id:
        try:
            students_query = Admission.objects.filter(id=student_id)
        except:
            pass
    
    # Search by various fields
    if search_term:
        students_query = Admission.objects.filter(
            Q(admission_id__icontains=search_term) |
            Q(student_name__icontains=search_term) |
            Q(mobile_number__icontains=search_term)
        )[:5]
    
    results = []
    for student in students_query:
        # Calculate totals
        total_expenses = Expense.objects.filter(admission=student).aggregate(Sum('amount'))['amount__sum'] or 0
        total_payments = Payment.objects.filter(admission=student).aggregate(Sum('amount'))['amount__sum'] or 0
        total_fee = (student.tms_fees or 0) + (student.admitted_college_fees or 0) + (student.hostel_fees or 0)
        due = total_fee - total_payments
        
        results.append({
            'id': student.id,
            'admission_id': student.admission_id or 'N/A',
            'student_name': student.student_name,
            'father_name': student.father_name,
            'mobile': student.mobile_number,
            'course': student.course,
            'image_url': student.student_image.url if student.student_image else None,
            'total_fee': float(total_fee),
            'total_payments': float(total_payments),
            'total_expenses': float(total_expenses),
            'due': float(due),
        })
    
    return JsonResponse({'results': results})

@login_required
def edit_expense(request, expense_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('student_account', admission_id=expense.admission.id)
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, 'institute/edit_expense.html', {
        'form': form,
        'expense': expense
    })

@login_required
def edit_payment(request, payment_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('student_account', admission_id=payment.admission.id)
    else:
        form = PaymentForm(instance=payment)
    
    return render(request, 'institute/edit_payment.html', {
        'form': form,
        'payment': payment
    })

@login_required
def delete_expense(request, expense_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Only admins can delete expenses.')
        return redirect('account_section')
    
    if request.method == 'POST':
        expense = get_object_or_404(Expense, id=expense_id)
        admission_id = expense.admission.id
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('student_account', admission_id=admission_id)
    
    return redirect('account_section')

@login_required
def delete_payment(request, payment_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Only admins can delete payments.')
        return redirect('account_section')
    
    if request.method == 'POST':
        payment = get_object_or_404(Payment, id=payment_id)
        admission_id = payment.admission.id
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('student_account', admission_id=admission_id)
    
    return redirect('account_section')

@login_required
def generate_receipt(request, payment_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Create PDF receipt
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph("THE MOTHER INSTITUTE OF SCIENCE", styles['Title']))
    elements.append(Paragraph("Trilochanpada, Jajpur Town, Near Maa Biraja Temple", styles['Normal']))
    elements.append(Paragraph("Contact: +91 9439387324", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Receipt title
    elements.append(Paragraph("PAYMENT RECEIPT", styles['Heading1']))
    elements.append(Spacer(1, 20))
    
    # Receipt details
    receipt_data = [
        ['Receipt Number:', payment.receipt_number],
        ['Date:', payment.date.strftime('%d/%m/%Y')],
        ['Student Name:', payment.admission.student_name],
        ['Admission ID:', payment.admission.admission_id],
        ['Payment Type:', payment.get_payment_type_display()],
        ['Payment Method:', payment.get_payment_method_display()],
        ['Amount:', f'₹{payment.amount}'],
        ['Description:', payment.description],
        ['Received By:', payment.received_by.username if payment.received_by else ''],
    ]
    
    receipt_table = Table(receipt_data, colWidths=[150, 300])
    receipt_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(receipt_table)
    elements.append(Spacer(1, 30))
    
    # Signature
    elements.append(Paragraph("Authorized Signature", styles['Normal']))
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("_________________________", styles['Normal']))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{payment.receipt_number}.pdf"'
    
    return response


@login_required
def account_report(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    expenses = Expense.objects.filter(admission=admission).order_by('date')
    payments = Payment.objects.filter(admission=admission).order_by('date')
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_payments - total_expenses
    
    # Create ledger data
    ledger_data = []
    running_balance = 0
    
    # Combine and sort all transactions by date
    all_transactions = []
    
    for expense in expenses:
        all_transactions.append({
            'date': expense.date,
            'type': 'Expense',
            'category': expense.get_category_display(),
            'amount': -expense.amount,
            'description': expense.description
        })
    
    for payment in payments:
        all_transactions.append({
            'date': payment.date,
            'type': 'Payment',
            'category': payment.get_payment_type_display(),
            'amount': payment.amount,
            'description': payment.description,
            'receipt_no': payment.receipt_number,
            'method': payment.get_payment_method_display()
        })
    
    # Sort transactions by date
    all_transactions.sort(key=lambda x: x['date'])
    
    # Calculate running balance
    for transaction in all_transactions:
        running_balance += transaction['amount']
        ledger_data.append({
            'date': transaction['date'],
            'type': transaction['type'],
            'category': transaction['category'],
            'amount': abs(transaction['amount']),
            'description': transaction['description'],
            'balance': running_balance,
            'receipt_no': transaction.get('receipt_no', ''),
            'method': transaction.get('method', '')
        })
    
    # Create PDF report with new design
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    
    # Header with logo and institute details
    header_data = [
        ["THE MOTHER INSTITUTE OF SCIENCE"],
        ["Account Ledger Report"],
        ["Generated on: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
    ]
    
    header_table = Table(header_data)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 16),
        ('FONTSIZE', (0, 1), (0, 1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    # Student Information Section
    student_info = [
    ["Student Details", "Contact Information", "Academic Information"],
    [
        Paragraph(
            f"""
            <b>Name:</b> {admission.student_name}<br/>
            <b>Father:</b> {admission.father_name}<br/>
            <b>Admission ID:</b> {admission.admission_id}
            """,
            normal
        ),

        Paragraph(
            f"""
            <b>Mobile:</b> {admission.mobile_number}<br/>
            <b>Address:</b> {admission.address}...
            """,
            normal
        ),

        Paragraph(
            f"""
            <b>Course:</b> {admission.course}
            """,
            normal
        ),
    ]
]

    
    student_table = Table(student_info, colWidths=[180, 180, 180])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(student_table)
    elements.append(Spacer(1, 15))
    
    # Summary Section
    summary_data = [
        ["Total Payments", "Total Expenses", "Current Balance"],
        [f"₹{total_payments:.2f}", f"₹{total_expenses:.2f}", f"₹{balance:.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[180, 180, 180])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Ledger Title
    elements.append(Paragraph("Transaction Ledger", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    # Ledger Table
    if ledger_data:
        ledger_table_data = [
            ["Date", "Type", "Category", "Description", "Amount", "Balance", "Receipt/Method"]
        ]
        
        for entry in ledger_data:
            # Determine amount color and sign
            if entry['type'] == 'Payment':
                amount_display = f"₹{entry['amount']:.2f}"
                amount_color = colors.green
            else:
                amount_display = f"-₹{entry['amount']:.2f}"
                amount_color = colors.red
            
            # Determine balance color
            if entry['balance'] >= 0:
                balance_color = colors.green
            else:
                balance_color = colors.red
            
            # Add receipt info for payments
            if entry['type'] == 'Payment':
                receipt_info = f"Receipt: {entry['receipt_no']}\nMethod: {entry['method']}"
            else:
                receipt_info = "-"
            
            ledger_table_data.append([
                entry['date'].strftime("%d/%m/%Y"),
                entry['type'],
                entry['category'],
                entry['description'][:30],
                amount_display,
                f"₹{entry['balance']:.2f}",
                receipt_info
            ])
        
        # Create ledger table
        ledger_table = Table(ledger_table_data, colWidths=[60, 60, 70, 120, 70, 80, 100])
        ledger_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        
        # Apply conditional formatting for amounts
        row_index = 1
        for entry in ledger_data:
            if entry['type'] == 'Payment':
                ledger_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (4, row_index), (4, row_index), colors.green),
                ]))
            else:
                ledger_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (4, row_index), (4, row_index), colors.red),
                ]))
            
            if entry['balance'] >= 0:
                ledger_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (5, row_index), (5, row_index), colors.green),
                ]))
            else:
                ledger_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (5, row_index), (5, row_index), colors.red),
                ]))
            
            row_index += 1
        
        elements.append(ledger_table)
    else:
        elements.append(Paragraph("No transactions recorded.", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # Footer with signatures
    footer_data = [
        ["Prepared By:", "Checked By:", "Approved By:"],
        ["_________________________", "_________________________", "_________________________"],
        [request.user.username, "Accountant", "Director"]
    ]
    
    footer_table = Table(footer_data, colWidths=[180, 180, 180])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="account_ledger_{admission.admission_id}.pdf"'
    
    return response

    
@login_required
def admin_dashboard(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    # Updated variable names and calculations
    total_registration = Admission.objects.count()  # Total registrations
    total_admission = Admission.objects.filter(is_admitted=True).count()  # Admitted students
    
    # Calculate total revenue (sum of hostel fees + college fees + TMS fees)
    revenue_data = Admission.objects.aggregate(
        hostel=Sum('hostel_fees', default=0),
        college=Sum('admitted_college_fees', default=0),
        tms=Sum('tms_fees', default=0)
    )
    total_revenue = revenue_data['hostel'] + revenue_data['college'] + revenue_data['tms']
    
    # Calculate total collection (sum of all payments)
    total_collection = Payment.objects.aggregate(Sum('amount', default=0))['amount__sum'] or 0
    
    # Calculate total due
    total_due = total_revenue - total_collection
    
    # Get admissions with pagination and search
    admissions_list = Admission.objects.all().order_by('-created_at')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        
        
        
        admissions_list = admissions_list.filter(
            Q(student_name__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(adhaar_number__icontains=search_query) |
            Q(college_roll_no__icontains=search_query) |
            Q(admission_id__icontains=search_query)  
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(admissions_list, 10)  # Show 10 admissions per page
    
    try:
        admissions = paginator.page(page)
    except PageNotAnInteger:
        admissions = paginator.page(1)
    except EmptyPage:
        admissions = paginator.page(paginator.num_pages)
    
    context = {
        'total_registration': total_registration,
        'total_admission': total_admission,
        'total_revenue': total_revenue,
        'total_collection': total_collection,
        'total_due': total_due,
        'admissions': admissions,
        'search_query': search_query,
    }
    return render(request, 'institute/admin_dashboard.html', context)

@login_required
def manage_users(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    users = CustomUser.objects.all().order_by('id')
    return render(request, 'institute/manage_users.html', {'users': users})

@login_required
def edit_user(request, user_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Update user fields
        user.uid = request.POST.get('uid')
        user.username = request.POST.get('username')
        user.user_type = request.POST.get('user_type')
        user.status = request.POST.get('status')
        
        # Update password only if provided
        password = request.POST.get('password')
        if password and password.strip() != '':
            user.set_password(password)
        
        user.save()
        messages.success(request, f'User {user.username} updated successfully!')
    
    return redirect('manage_users')





@login_required
def delete_user(request, user_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Only admins can delete users.')
        return redirect('manage_users')
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            username = user.username
            
            # Prevent deleting yourself
            if user == request.user:
                messages.error(request, 'You cannot delete your own account!')
                return redirect('manage_users')
            
            # Prevent deleting the last admin
            if user.user_type == 'admin':
                admin_count = CustomUser.objects.filter(user_type='admin').count()
                if admin_count <= 1:
                    messages.error(request, 'Cannot delete the last admin account!')
                    return redirect('manage_users')
            
            user.delete()
            messages.success(request, f'User "{username}" has been deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
    
    return redirect('manage_users')


def admission_form(request):
    if request.method == 'POST':
        form = AdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            admission = form.save(commit=False)
            # Link to user if they are logged in
            if request.user.is_authenticated:
                admission.submitted_by = request.user
            admission.save()
            messages.success(request, f'Registration form submitted successfully! Admission ID: {admission.admission_id}')
            return redirect('admission_form')
    else:
        form = AdmissionForm()
    
    return render(request, 'institute/admission_form.html', {'form': form})

# views.py - UPDATE THE search_admission VIEW

@login_required
def search_admission(request):
    if request.user.user_type != 'admin': 
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    admission = None
    search_performed = False
    edit_mode = False
    
    # Check if we're in edit mode (has admission_id parameter)
    admission_id = request.GET.get('admission_id')
    if admission_id:
        edit_mode = True
        try:
            admission = get_object_or_404(Admission, id=admission_id)
            search_query = admission.admission_id or admission.mobile_number
        except:
            pass
    
    # Handle search
    if search_query and not edit_mode:
        search_performed = True
        
        # Check if search is mobile number (10 digits)
        if search_query.isdigit() and len(search_query) == 10:
            admissions = Admission.objects.filter(mobile_number__icontains=search_query)
        # Check if search is admission ID (TMIS followed by numbers)
        elif search_query.upper().startswith('TMIS'):
            admissions = Admission.objects.filter(admission_id__iexact=search_query.upper())
        else:
            # General search
            admissions = Admission.objects.filter(
                Q(student_name__icontains=search_query) |
                Q(father_name__icontains=search_query) |
                Q(mobile_number__icontains=search_query) |
                Q(adhaar_number__icontains=search_query) |
                Q(admission_id__icontains=search_query.upper())
            )
        
        if admissions.exists():
            admission = admissions.first()
            edit_mode = True  # Automatically go to edit mode when found
        else:
            messages.warning(request, f"No admission found for: {search_query}")
    
    # Get recent admissions for the table
    recent_admissions = Admission.objects.all().order_by('-created_at')[:10]
    
    # Handle POST request (both create and update)
    if request.method == 'POST':
        admission_id = request.POST.get('admission_id')
        
        if admission_id:
            # UPDATE EXISTING ADMISSION
            try:
                admission = get_object_or_404(Admission, id=admission_id)
                # Store the original values to protect them
                original_admission_id = admission.admission_id
                original_is_admitted = admission.is_admitted
                original_admission_date = admission.admission_date
                original_admitted_by = admission.admitted_by
                
                form = AdmissionForm(request.POST, request.FILES, instance=admission)
                
                if form.is_valid():
                    admission = form.save(commit=False)
                    # Restore protected fields
                    admission.admission_id = original_admission_id
                    
                    # CRITICAL: Check if is_admitted is in the form data
                    # If not present, restore the original value
                    if 'is_admitted' not in request.POST:
                        admission.is_admitted = original_is_admitted
                        admission.admission_date = original_admission_date
                        admission.admitted_by = original_admitted_by
                    
                    admission.submitted_by = request.user
                    admission.save()
                    
                    messages.success(request, f'Admission {admission.admission_id} for {admission.student_name} updated successfully!')
                    return redirect('search_admission')
                else:
                    # Form has errors - display them
                    error_messages = []
                    for field, errors in form.errors.items():
                        if field == '__all__':
                            for error in errors:
                                error_messages.append(f"Form Error: {error}")
                        else:
                            for error in errors:
                                error_messages.append(f"{field}: {error}")
                    
                    if error_messages:
                        for msg in error_messages:
                            messages.error(request, msg)
                    else:
                        messages.error(request, 'Please correct the errors in the form.')
                    
                    # Don't redirect - re-render with form errors visible
                    edit_mode = True
                    
            except Exception as e:
                messages.error(request, f'Error updating admission: {str(e)}')
                print(f"Update error: {e}")
        else:
            # CREATE NEW ADMISSION
            try:
                form = AdmissionForm(request.POST, request.FILES)
                
                if form.is_valid():
                    admission = form.save(commit=False)
                    admission.submitted_by = request.user
                    admission.save()
                    
                    messages.success(request, f'New admission created successfully! Admission ID: {admission.admission_id}')
                    return redirect('search_admission')
                else:
                    # Form has errors - display them
                    error_messages = []
                    for field, errors in form.errors.items():
                        if field == '__all__':
                            for error in errors:
                                error_messages.append(f"Form Error: {error}")
                        else:
                            for error in errors:
                                error_messages.append(f"{field}: {error}")
                    
                    if error_messages:
                        for msg in error_messages:
                            messages.error(request, msg)
                    else:
                        messages.error(request, 'Please correct the errors in the form.')
                    
                    # Don't redirect - re-render with form errors visible
                    edit_mode = False
                    
            except Exception as e:
                messages.error(request, f'Error creating admission: {str(e)}')
                print(f"Create error: {e}")
    
    # For GET requests, prepare the form
    if admission:
        # If we found an admission, pre-fill the form
        form = AdmissionForm(instance=admission)
    else:
        # Otherwise, show empty form
        form = AdmissionForm()
    
    context = {
        'form': form,
        'admission': admission,
        'search_query': search_query,
        'search_performed': search_performed,
        'recent_admissions': recent_admissions,
        'edit_mode': edit_mode,
    }
    return render(request, 'institute/search_admission.html', context)


def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User registered successfully!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'institute/register.html', {'form': form})

def get_active_organization(request):
    """Get the active organization for the current user/session"""
    # In your case, you might have only one organization
    # You can modify this based on your requirements
    try:
        organization = Organization.objects.filter(status='active').first()
        return organization
    except:
        return None


# Add this function to views.py

def organization_settings(request):
    """View for managing organization settings"""
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        return redirect('login')
    
    # Try to get existing organization
    try:
        organization = Organization.objects.filter(status='active').first()
    except:
        organization = None
    
    if request.method == 'POST':
        if organization:
            form = OrganizationForm(request.POST, request.FILES, instance=organization)
        else:
            form = OrganizationForm(request.POST, request.FILES)
        
        if form.is_valid():
            org = form.save(commit=False)
            org.status = 'active'
            org.save()
            messages.success(request, 'Organization settings updated successfully!')
            return redirect('organization_settings')
    else:
        if organization:
            form = OrganizationForm(instance=organization)
        else:
            form = OrganizationForm()
    
    context = {
        'organization': organization,
        'form': form,
    }
    return render(request, 'institute/organization_settings.html', context)

# Add this context processor function
def organization_context(request):
    """Context processor to add organization data to all templates"""
    try:
        organization = Organization.objects.filter(status='active').first()
    except:
        organization = None
    return {
        'organization': organization,
    }


@login_required
def admissions_list(request):
    # Admin-only view to list admitted students
    if request.user.user_type != 'admin':
        return redirect('home')

    admitted_students = Admission.objects.filter(is_admitted=True).order_by('-admission_date')
    admitted_count = admitted_students.count()

    context = {
        'admitted_students': admitted_students,
        'admitted_count': admitted_count,
    }
    return render(request, 'institute/admissions_list.html', context)


@login_required
def search_students(request):
    """API endpoint for searching students"""
    if request.user.user_type != 'admin':
        return JsonResponse({'results': []})

    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    students_query = Admission.objects.filter(
        Q(student_name__icontains=query) |
        Q(admission_id__icontains=query) |
        Q(mobile_number__icontains=query)
    )[:10]
    
    results = []
    for s in students_query:
        # Calculate totals
        total_payments = Payment.objects.filter(admission=s).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_fee = (s.tms_fees or 0) + (s.admitted_college_fees or 0) + (s.hostel_fees or 0)
        due = total_fee - total_payments

        results.append({
            'id': s.id,
            'admission_id': s.admission_id,
            'student_name': s.student_name,
            'mobile': s.mobile_number,
            'course': s.course,
            'total_fee': float(total_fee),
            'total_payments': float(total_payments),
            'due': float(due)
        })
    
    return JsonResponse({'results': results})

@require_POST
@login_required
def delete_registration(request, admission_id):
    """
    Delete a registration only if the student is not admitted
    """
    try:
        admission = Admission.objects.get(id=admission_id)
        
        # Check if student is admitted
        if admission.is_admitted:
            return JsonResponse({
                'success': False, 
                'error': 'Cannot delete admitted students'
            }, status=400)
        
        # Store student name for response message
        student_name = admission.student_name
        
        # Delete the registration
        admission.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Registration for {student_name} has been deleted successfully'
        })
        
    except Admission.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Registration not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)
        
        
@login_required
def get_student_details_by_id(request, student_id):
    """API endpoint to get student details by ID"""
    if request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        student = Admission.objects.get(id=student_id)
        # Calculate total payments
        total_payments = Payment.objects.filter(admission=student).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Calculate total fee
        total_fee = (student.tms_fees or 0) + (student.admitted_college_fees or 0) + (student.hostel_fees or 0)
        
        data = {
            'id': student.id,
            'admission_id': student.admission_id,
            'student_name': student.student_name,
            'mobile': student.mobile_number,
            'course': student.course,
            'total_fee': float(total_fee),
            'total_payments': float(total_payments),
        }
        
        return JsonResponse({'success': True, 'data': data})
    except Admission.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})
    
    # Add this new view to views.py
@login_required
def view_registrations(request):
    """View-only page for registrations (no edit form)"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    admissions_list = Admission.objects.all().order_by('-created_at')
    
    if search_query:
        admissions_list = admissions_list.filter(
            Q(student_name__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(adhaar_number__icontains=search_query) |
            Q(admission_id__icontains=search_query.upper())
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(admissions_list, 10)
    
    try:
        admissions = paginator.page(page)
    except PageNotAnInteger:
        admissions = paginator.page(1)
    except EmptyPage:
        admissions = paginator.page(paginator.num_pages)
    
    context = {
        'admissions': admissions,
        'search_query': search_query,
    }
    return render(request, 'institute/view_registrations.html', context)

# In views.py - UPDATE the add_expense_general function
@login_required
def add_expense_general(request):
    """Add expense with student selection - FIXED VERSION"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')
    
    admission = None
    selected_admission_id = request.GET.get('admission_id') or request.POST.get('admission_id')
    
    if selected_admission_id:
        try:
            admission = Admission.objects.get(id=selected_admission_id)
        except Admission.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            if not admission:
                messages.error(request, 'Please select a student first.')
                return render(request, 'institute/add_expense_general.html', {
                    'form': form,
                    'students': Admission.objects.all().order_by('student_name'),
                    'title': 'Add Expense'
                })
            
            expense = form.save(commit=False)
            expense.admission = admission
            expense.added_by = request.user
            
            # Save the expense
            try:
                expense.save()
                messages.success(request, f'Expense of ₹{expense.amount} added successfully!')
                return redirect('student_account', admission_id=admission.id)
            except Exception as e:
                messages.error(request, f'Error saving expense: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = ExpenseForm()
    
    # Get all students for selection
    students = Admission.objects.all().order_by('student_name')
    
    context = {
        'form': form,
        'admission': admission,
        'students': students,
        'title': 'Add Expense'
    }
    return render(request, 'institute/add_expense_general.html', context)


# In views.py - UPDATE the add_payment_general function
@login_required
def add_payment_general(request):
    """Add payment with student selection - FIXED VERSION"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')
    
    admission = None
    selected_admission_id = request.GET.get('admission_id') or request.POST.get('admission_id')
    
    if selected_admission_id:
        try:
            admission = Admission.objects.get(id=selected_admission_id)
        except Admission.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            if not admission:
                messages.error(request, 'Please select a student first.')
                return render(request, 'institute/add_payment_general.html', {
                    'form': form,
                    'students': Admission.objects.all().order_by('student_name'),
                    'title': 'Add Payment'
                })
            
            payment = form.save(commit=False)
            payment.admission = admission
            payment.received_by = request.user
            
            # Save the payment (receipt number will be auto-generated)
            try:
                payment.save()
                messages.success(request, f'Payment of ₹{payment.amount} recorded successfully! Receipt: {payment.receipt_number}')
                return redirect('student_account', admission_id=admission.id)
            except Exception as e:
                messages.error(request, f'Error saving payment: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = PaymentForm()
    
    # Get all students for selection
    students = Admission.objects.all().order_by('student_name')
    
    context = {
        'form': form,
        'admission': admission,
        'students': students,
        'title': 'Add Payment'
    }
    return render(request, 'institute/add_payment_general.html', context)

# Add to views.py
@login_required
def get_complete_admission_details(request, student_id):
    """API endpoint to get complete admission details by ID"""
    if request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        admission = Admission.objects.get(id=student_id)
        
        # Serialize admission data
        admission_data = {
            'id': admission.id,
            'admission_id': admission.admission_id,
            'student_name': admission.student_name,
            'father_name': admission.father_name,
            'mother_name': admission.mother_name,
            'date_of_birth': admission.date_of_birth.strftime('%Y-%m-%d') if admission.date_of_birth else None,
            'mobile_number': admission.mobile_number,
            'whatsapp_number': admission.whatsapp_number,
            'blood_group': admission.blood_group,
            'category': admission.category,
            'adhaar_number': admission.adhaar_number,
            'address': admission.address,
            'course': admission.course,
            'college_name': admission.college_name,
            'board_name': admission.board_name,
            'college_roll_no': admission.college_roll_no,
            'batch': admission.batch,
            'eleventh_year': admission.eleventh_year,
            'twelfth_year': admission.twelfth_year,
            'enrolled_for': admission.enrolled_for,
            'sams_login_id': admission.sams_login_id,
            'sams_password': admission.sams_password,
            'apaar_id': admission.apaar_id,
            'hostel_fees': float(admission.hostel_fees) if admission.hostel_fees else 0.0,
            'tms_fees': float(admission.tms_fees) if admission.tms_fees else 0.0,
            'admitted_college_fees': float(admission.admitted_college_fees) if admission.admitted_college_fees else 0.0,
            'college_transportation': admission.college_transportation,
            'is_admitted': admission.is_admitted,
            'created_at': admission.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'visitor1_name': admission.visitor1_name,
            'visitor1_relation': admission.visitor1_relation,
            'visitor1_contact': admission.visitor1_contact,
            'visitor2_name': admission.visitor2_name,
            'visitor2_relation': admission.visitor2_relation,
            'visitor2_contact': admission.visitor2_contact,
            'academics_accommodation': admission.academics_accommodation,
            'subject1': admission.subject1 or '',
            'subject2': admission.subject2 or '',
            'subject3': admission.subject3 or '',
            'subject4': admission.subject4 or '',
            'subject5': admission.subject5 or '',
            'subject6': admission.subject6 or '',
            'college_dress': admission.college_dress,
            'books': admission.books,
            'tms_dress': admission.tms_dress,
            'guardian_signature': admission.guardian_signature,
            'student_signature': admission.student_signature,
            'tms_signature': admission.tms_signature,
        }
        
        return JsonResponse({'success': True, 'admission': admission_data})
    except Admission.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

# Exam Management Views

@login_required
def exam_dashboard(request):
    """Main exam dashboard showing overview"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    # Statistics
    total_exams = Exam.objects.count()
    scheduled_exams = Exam.objects.filter(status='scheduled').count()
    completed_exams = Exam.objects.filter(status='completed').count()
    ongoing_exams = Exam.objects.filter(status='ongoing').count()
    
    # Today's exams
    today_exams = Exam.objects.filter(exam_date=date.today()).order_by('start_time')[:5]
    
    # Upcoming exams
    upcoming_exams = Exam.objects.filter(
        exam_date__gt=date.today()
    ).order_by('exam_date')[:10]
    
    context = {
        'total_exams': total_exams,
        'scheduled_exams': scheduled_exams,
        'completed_exams': completed_exams,
        'ongoing_exams': ongoing_exams,
        'today_exams': today_exams,
        'upcoming_exams': upcoming_exams,
    }
    return render(request, 'institute/exam_dashboard.html', context)


@login_required
def exam_list(request):
    """List all exams"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    exams = Exam.objects.all().order_by('-exam_date')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        exams = exams.filter(status=status)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        exams = exams.filter(
            Q(name__icontains=search_query) |
            Q(batch__icontains=search_query) |
            Q(subject__icontains=search_query)
        )
    
    paginator = Paginator(exams, 10)
    page = request.GET.get('page', 1)
    
    try:
        exams_page = paginator.page(page)
    except:
        exams_page = paginator.page(1)
    
    context = {
        'exams': exams_page,
        'status': status,
        'search_query': search_query,
    }
    return render(request, 'institute/exam_list.html', context)


@login_required
def add_exam(request):
    """Add a new exam"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            
            messages.success(request, f'Exam "{exam.name}" created successfully!')
            return redirect('exam_list')
    else:
        form = ExamForm()
    
    return render(request, 'institute/exam_form.html', {
        'form': form,
        'title': 'Create New Exam'
    })


@login_required
def edit_exam(request, exam_id):
    """Edit an exam"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, f'Exam "{exam.name}" updated successfully!')
            return redirect('exam_list')
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'institute/exam_form.html', {
        'form': form,
        'exam': exam,
        'title': 'Edit Exam'
    })


@login_required
def delete_exam(request, exam_id):
    """Delete an exam"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Permission denied')
        return redirect('exam_list')
    
    if request.method == 'POST':
        exam = get_object_or_404(Exam, id=exam_id)
        name = exam.name
        exam.delete()
        messages.success(request, f'Exam "{name}" deleted successfully!')
    
    return redirect('exam_list')


@login_required
def result_entry(request, exam_id):
    """Enter results for an exam"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Get students eligible for this exam (based on stream, year, and batch)
    students = Admission.objects.filter(
        is_admitted=True,
        course__icontains=exam.stream,
        batch=exam.batch
    ).order_by('student_name')
    
    if request.method == 'POST':
        # Process bulk result entry
        for student in students:
            marks_key = f'marks_{student.id}'
            absent_key = f'absent_{student.id}'
            remarks_key = f'remarks_{student.id}'
            
            marks = request.POST.get(marks_key)
            is_absent = request.POST.get(absent_key) == 'on'
            remarks = request.POST.get(remarks_key, '')
            
            if marks or is_absent:
                # Get or create result
                result, created = StudentResult.objects.update_or_create(
                    exam=exam,
                    student=student,
                    defaults={
                        'marks_obtained': marks if marks and not is_absent else 0,
                        'is_absent': is_absent,
                        'remarks': remarks,
                        'entered_by': request.user
                    }
                )
        
        messages.success(request, f'Results for {exam.get_subject_display()} saved successfully!')
        return redirect('result_list', exam_id=exam.id)
    
    # Get existing results
    existing_results = {}
    for result in StudentResult.objects.filter(exam=exam):
        existing_results[result.student_id] = result
    
    context = {
        'exam': exam,
        'students': students,
        'existing_results': existing_results,
    }
    return render(request, 'institute/result_entry.html', context)

@login_required
def result_list(request, exam_id):
    """View results for an exam"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Get all students for this exam
    students = Admission.objects.filter(
        is_admitted=True,
        course__icontains=exam.stream,
        batch=exam.batch
    ).order_by('student_name')
    
    # Get all results
    results = StudentResult.objects.filter(
        exam=exam
    ).select_related('student')
    
    # Organize results by student
    student_results = []
    for student in students:
        result = results.filter(student=student).first()
        student_results.append({
            'student': student,
            'result': result,
            'marks': result.marks_obtained if result and not result.is_absent else 0,
            'is_absent': result.is_absent if result else False,
            'percentage': result.percentage if result else 0,
            'grade': result.grade if result else 'N/A'
        })
    
    # Calculate statistics
    total_students = students.count()
    appeared_students = results.filter(is_absent=False).count()
    passed_students = results.filter(is_absent=False, marks_obtained__gte=exam.passing_marks).count()
    avg_marks = results.filter(is_absent=False).aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0
    
    context = {
        'exam': exam,
        'student_results': student_results,
        'total_students': total_students,
        'appeared_students': appeared_students,
        'passed_students': passed_students,
        'avg_marks': avg_marks,
    }
    return render(request, 'institute/result_list.html', context)

@login_required
def report_card(request):
    """Generate report card for students"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    exam_id = request.GET.get('exam', '')
    student_id = request.GET.get('student', '')
    download = request.GET.get('download', '')
    
    students = []
    # Get ALL completed exams initially (will be filtered later)
    exams = Exam.objects.filter(status='completed').order_by('-exam_date')
    selected_exam = None
    selected_student = None
    
    # If download parameter is present, generate PDF
    if download == 'pdf' and student_id and exam_id:
        return generate_report_card_pdf(request, exam_id, student_id)
    
    if student_id:
        try:
            selected_student = Admission.objects.get(id=student_id, is_admitted=True)
            
            # CRITICAL FIX: Filter exams based on student's batch and course
            exams = Exam.objects.filter(
                status='completed',
                batch=selected_student.batch,  # Match student's batch
                stream__icontains=selected_student.course  # Match student's course/stream
            ).order_by('-exam_date')
            
        except Admission.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    if exam_id:
        try:
            selected_exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            messages.error(request, 'Exam not found.')
    
    # Search for students
    if search_query:
        students = Admission.objects.filter(
            Q(is_admitted=True),
            Q(student_name__icontains=search_query) |
            Q(admission_id__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )[:20]
    
    # Get existing results for the selected student
    exam_results = {}
    if selected_student:
        results = StudentResult.objects.filter(
            student=selected_student,
            exam__in=exams
        ).select_related('exam')
        
        for result in results:
            exam_results[result.exam.id] = result
    
    context = {
        'search_query': search_query,
        'students': students,
        'exams': exams,
        'selected_exam': selected_exam,
        'selected_student': selected_student,
        'exam_results': exam_results,  # Pass results to template
    }
    return render(request, 'institute/report_card_search.html', context)



def generate_report_card_pdf(request, exam_id, student_id):
    """Generate PDF report card for a student"""
    try:
        exam = get_object_or_404(Exam, id=exam_id)
        student = get_object_or_404(Admission, id=student_id, is_admitted=True)
        
        # Get student result for this exam
        try:
            result = StudentResult.objects.get(exam=exam, student=student)
        except StudentResult.DoesNotExist:
            result = None
        
        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()
        
        # Create the PDF object
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Create custom styles
        center_style = ParagraphStyle(
            'CenterStyle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # Header with Institute Name
        elements.append(Paragraph("THE MOTHER INSTITUTE OF SCIENCE", title_style))
        elements.append(Paragraph("Excellence in Science Education", center_style))
        elements.append(Paragraph("Trilochanpada, Jajpur Town, Near Maa Biraja Temple", center_style))
        elements.append(Paragraph("Contact: +91 9439387324 | Email: contact@motherinstitute.edu", center_style))
        elements.append(Spacer(1, 20))
        
        # Report Card Title
        elements.append(Paragraph("STUDENT REPORT CARD", heading_style))
        elements.append(Spacer(1, 10))
        
        # Exam Details
        exam_details = [
            ["Exam Name:", exam.name],
            ["Subject:", exam.get_subject_display()],
            ["Exam Date:", exam.exam_date.strftime('%d/%m/%Y') if exam.exam_date else 'N/A'],
            ["Batch:", exam.batch],
            ["Maximum Marks:", str(exam.total_marks)],
            ["Passing Marks:", str(exam.passing_marks)],
        ]
        
        exam_table = Table(exam_details, colWidths=[120, 300])
        exam_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(exam_table)
        elements.append(Spacer(1, 20))
        
        # Student Details
        student_details = [
            ["Student Name:", student.student_name],
            ["Admission ID:", student.admission_id],
            ["Father's Name:", student.father_name],
            ["Mother's Name:", student.mother_name],
            ["Course:", student.course],
            ["Mobile:", student.mobile_number],
        ]
        
        student_table = Table(student_details, colWidths=[120, 300])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(student_table)
        elements.append(Spacer(1, 20))
        
        # Result Details
        if result:
            marks_obtained = result.marks_obtained if not result.is_absent else 0
            percentage = (marks_obtained / exam.total_marks * 100) if exam.total_marks > 0 and not result.is_absent else 0
            status = "Absent" if result.is_absent else ("Pass" if marks_obtained >= exam.passing_marks else "Fail")
            
            # Determine grade
            if result.is_absent:
                grade = "AB"
            elif percentage >= 90:
                grade = "A+"
            elif percentage >= 80:
                grade = "A"
            elif percentage >= 70:
                grade = "B+"
            elif percentage >= 60:
                grade = "B"
            elif percentage >= 50:
                grade = "C"
            elif percentage >= 33:
                grade = "D"
            else:
                grade = "F"
            
            result_details = [
                ["Marks Obtained:", f"{marks_obtained} / {exam.total_marks}"],
                ["Percentage:", f"{percentage:.1f}%"],
                ["Status:", status],
                ["Grade:", grade],
                ["Remarks:", result.remarks if result.remarks else "-"],
            ]
        else:
            result_details = [
                ["Marks Obtained:", "Not Available"],
                ["Percentage:", "Not Available"],
                ["Status:", "Not Available"],
                ["Grade:", "Not Available"],
                ["Remarks:", "No result found"],
            ]
        
        result_table = Table(result_details, colWidths=[120, 300])
        result_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (1, 2), (1, 2), colors.green if status == 'Pass' else colors.red),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(result_table)
        elements.append(Spacer(1, 30))
        
        # Signatures
        signature_data = [
            ["_________________________", "_________________________", "_________________________"],
            ["Class Teacher", "Principal", "Director"],
            ["Date: " + datetime.now().strftime("%d/%m/%Y"), "", ""],
        ]
        
        signature_table = Table(signature_data, colWidths=[200, 200, 200])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, 1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
        ]))
        
        elements.append(signature_table)
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create the HttpResponse
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_card_{student.admission_id}_{exam.name}.pdf"'
        response['Content-Length'] = len(pdf)
        response.write(pdf)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating report card: {str(e)}')
        return redirect('report_card')


@login_required
def view_report_card(request, exam_id, student_id):
    """View report card in browser (not PDF)"""
    if request.user.user_type != 'admin':
        return redirect('home')
    
    exam = get_object_or_404(Exam, id=exam_id)
    student = get_object_or_404(Admission, id=student_id, is_admitted=True)
    
    try:
        result = StudentResult.objects.get(exam=exam, student=student)
    except StudentResult.DoesNotExist:
        result = None
    
    context = {
        'exam': exam,
        'student': student,
        'result': result,
    }
    return render(request, 'institute/report_card_view.html', context)


@login_required
def api_get_students_for_exam(request, exam_id):
    """API to get students eligible for an exam"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    students = Admission.objects.filter(
        is_admitted=True,
        course__icontains=exam.stream,
        batch=exam.batch
    ).values('id', 'student_name', 'admission_id', 'mobile_number').order_by('student_name')
    
    return JsonResponse({'students': list(students)})


@login_required
def api_get_exam_stats(request, exam_id):
    """API to get statistics for an exam"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    total_students = Admission.objects.filter(
        is_admitted=True,
        course__icontains=exam.stream,
        batch=exam.batch
    ).count()
    
    # Count students who have results
    results = StudentResult.objects.filter(exam=exam)
    appeared_students = results.filter(is_absent=False).count()
    completed_students = results.count()
    
    return JsonResponse({
        'total_students': total_students,
        'appeared_students': appeared_students,
        'completed_students': completed_students,
    })
    
    
# @login_required
# def edit_student_result(request, exam_id, student_id):
#     """Edit individual student result"""
#     if request.user.user_type != 'admin':
#         return redirect('home')
    
#     exam = get_object_or_404(Exam, id=exam_id)
#     student = get_object_or_404(Admission, id=student_id)
    
#     # Get existing result
#     try:
#         result = StudentResult.objects.get(exam=exam, student=student)
#     except StudentResult.DoesNotExist:
#         result = None
    
#     context = {
#         'exam': exam,
#         'student': student,
#         'result': result,
#     }
#     return render(request, 'institute/edit_student_result.html', context)


# @login_required
# @require_POST
# def update_student_result(request, exam_id, student_id):
#     """Update individual student result"""
#     if request.user.user_type != 'admin':
#         return redirect('home')
    
#     exam = get_object_or_404(Exam, id=exam_id)
#     student = get_object_or_404(Admission, id=student_id)
    
#     marks = request.POST.get('marks_obtained')
#     is_absent = request.POST.get('is_absent') == 'on'
#     remarks = request.POST.get('remarks', '')
    
#     # Update or create result
#     result, created = StudentResult.objects.update_or_create(
#         exam=exam,
#         student=student,
#         defaults={
#             'marks_obtained': marks if marks and not is_absent else 0,
#             'is_absent': is_absent,
#             'remarks': remarks,
#             'entered_by': request.user
#         }
#     )
    
#     messages.success(request, f'Result for {student.student_name} updated successfully!')
#     return redirect('result_list', exam_id=exam.id)


@login_required
@require_POST
def bulk_update_results(request, exam_id):
    """Bulk update multiple student results at once"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Permission denied')
        return redirect('result_list', exam_id=exam_id)
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Get all students for this exam
    students = Admission.objects.filter(
        is_admitted=True,
        course__icontains=exam.stream,
        batch=exam.batch
    )
    
    updated_count = 0
    
    for student in students:
        marks_key = f'marks_{student.id}'
        absent_key = f'absent_{student.id}'
        
        marks = request.POST.get(marks_key)
        is_absent = request.POST.get(absent_key) == 'on'
        
        # Only update if the field was present in the form
        if marks_key in request.POST or absent_key in request.POST:
            # Get or create result
            result, created = StudentResult.objects.update_or_create(
                exam=exam,
                student=student,
                defaults={
                    'marks_obtained': marks if marks and not is_absent else 0,
                    'is_absent': is_absent,
                    'entered_by': request.user,
                    'updated_at': timezone.now()
                }
            )
            updated_count += 1
    
    messages.success(request, f'Successfully updated {updated_count} student results!')
    return redirect('result_list', exam_id=exam.id)