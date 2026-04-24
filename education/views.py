from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Category, Branch, Subject, Content, StudentAdmission, GlobalSetting, Year, ContactMessage, SavedContent, Note, Video
from .forms import AdmissionForm, ContentForm, CommonPasswordForm, ContactForm
import json
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import Category, Branch, Subject, Content, StudentAdmission, GlobalSetting, Year, ContactMessage, SavedContent, Note, Video, FCMToken
import firebase_admin
from firebase_admin import messaging, credentials
import os

# Initialize Firebase (only once)
if not firebase_admin._apps:
    try:
        # Check Render Secret File location first, then environment variable
        render_secret = '/etc/secrets/firebase_service_account.json'
        env_secret = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        
        cred_path = None
        if os.path.exists(render_secret):
            cred_path = render_secret
        elif env_secret:
            cred_path = env_secret
            
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Initialized Successfully")
    except Exception as e:
        print(f"Firebase Initialization Error: {e}")

def send_fcm_notification(title, body):
    tokens = FCMToken.objects.values_list('token', flat=True)
    if not tokens:
        return
    
    # We use Multicast for multiple tokens
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=list(tokens),
    )
    try:
        response = messaging.send_multicast(message)
        print(f"Successfully sent {response.success_count} notifications")
    except Exception as e:
        print(f"Error sending FCM: {e}")

@login_required
def save_fcm_token(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')
            if token:
                FCMToken.objects.update_or_create(
                    token=token,
                    defaults={'user': request.user}
                )
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

def firebase_messaging_sw(request):
    file_path = os.path.join(settings.BASE_DIR, 'firebase-messaging-sw.js')
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse("Service worker file not found.", status=404)

def home(request):
    categories = Category.objects.all()
    context = {'categories': categories}
    
    if request.user.is_staff:
        context['total_students'] = StudentAdmission.objects.filter(status='Approved').count()
        context['pending_admissions'] = StudentAdmission.objects.filter(status='Pending').count()
        context['total_subjects'] = Subject.objects.count()
        
    return render(request, 'education/index.html', context)


def category_branches(request, pk):
    if not (request.user.is_authenticated or request.session.get('is_student')):
        return redirect('login_selection')
    category = get_object_or_404(Category, pk=pk)
    
    # Check if category has years (like Degree/Diploma)
    years = category.years.all()
    if years.exists():
        return render(request, 'education/category_years.html', {'category': category, 'years': years})
        
    # Get branches that have subjects in this category (for 11th/12th)
    branches = Branch.objects.filter(subjects__category=category).distinct()
    return render(request, 'education/category_branches.html', {'category': category, 'branches': branches})

def year_subjects(request, category_pk, year_pk):
    if not (request.user.is_authenticated or request.session.get('is_student')):
        return redirect('login_selection')
        
    category = get_object_or_404(Category, pk=category_pk)
    year = get_object_or_404(Year, pk=year_pk)
    
    # Get all subjects for this year
    subjects = Subject.objects.filter(category=category, year=year)
    
    # Get all branches involved for tabs
    branches = Branch.objects.filter(subjects__in=subjects).distinct()
    
    selected_branch_id = request.GET.get('branch')
    if selected_branch_id:
        subjects = subjects.filter(branch_id=selected_branch_id)
        
    return render(request, 'education/year_subjects.html', {
        'category': category,
        'year': year,
        'subjects': subjects,
        'branches': branches,
        'selected_branch_id': int(selected_branch_id) if selected_branch_id else None
    })

def branch_subjects(request, category_pk, branch_pk):
    if not (request.user.is_authenticated or request.session.get('is_student')):
        return redirect('login_selection')
    category = get_object_or_404(Category, pk=category_pk)
    branch = get_object_or_404(Branch, pk=branch_pk)
    subjects = Subject.objects.filter(category=category, branch=branch)
    return render(request, 'education/branch_subjects.html', {
        'category': category,
        'branch': branch,
        'subjects': subjects
    })

def subject_detail(request, pk):
    if not (request.user.is_authenticated or request.session.get('is_student')):
        return redirect('login_selection')
        
    subject = get_object_or_404(
        Subject.objects.prefetch_related('chapters__contents'), 
        pk=pk
    )
    
    saved_content_ids = []
    if request.session.get('is_student'):
        student_id = request.session.get('student_id')
        saved_content_ids = SavedContent.objects.filter(student_id=student_id).values_list('content_id', flat=True)
        
    return render(request, 'education/subject_detail.html', {
        'subject': subject,
        'saved_content_ids': saved_content_ids
    })

def search(request):
    if not (request.user.is_authenticated or request.session.get('is_student')):
        return redirect('login_selection')
    query = request.GET.get('q')
    subjects = Subject.objects.none()
    contents = Content.objects.none()
    
    if query:
        subjects = Subject.objects.filter(name__icontains=query)
        contents = Content.objects.filter(title__icontains=query)
        
    return render(request, 'education/search_results.html', {
        'query': query,
        'subjects': subjects,
        'contents': contents,
    })

def admission_apply(request):
    if request.method == 'POST':
        form = AdmissionForm(request.POST)
        if form.is_valid():
            admission = form.save()
            messages.success(request, "Your admission request has been submitted and is under review")
            
            # Trigger FCM Notification to Admin
            send_fcm_notification(
                title="New Admission",
                body=f"A student {admission.full_name} has submitted the admission form for {admission.category.name}."
            )
            
            return redirect('admission_apply')
    else:
        form = AdmissionForm()
    return render(request, 'education/admission.html', {'form': form})

def login_selection(request):
    return render(request, 'education/login_selection.html')

def student_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            admission = StudentAdmission.objects.get(email=email)
        except StudentAdmission.DoesNotExist:
            messages.error(request, "Account not found. Please apply for admission first.")
            return redirect('student_login')
            
        if admission.status == 'Pending':
            messages.warning(request, "Your admission request is still under review.")
            return redirect('student_login')
        elif admission.status == 'Rejected':
            messages.error(request, "Your admission request was rejected.")
            return redirect('student_login')
        else: # Approved
            # Check Common Password
            common_pwd_obj = GlobalSetting.objects.filter(key='student_common_password').first()
            if common_pwd_obj:
                if check_password(password, common_pwd_obj.value):
                    # Login Success
                    request.session['student_id'] = admission.id
                    request.session['student_email'] = admission.email
                    request.session['is_student'] = True
                    messages.success(request, f"Welcome back, {admission.full_name}!")
                    return redirect('student_dashboard')
                else:
                    messages.error(request, "Invalid password")
            else:
                messages.error(request, "Student login is currently disabled by admin.")
    
    return render(request, 'education/student_login.html')

def student_logout(request):
    if 'student_id' in request.session:
        del request.session['student_id']
    if 'is_student' in request.session:
        del request.session['is_student']
    return redirect('login_selection')

from django.core.mail import send_mail
from django.conf import settings

@user_passes_test(lambda u: u.is_staff)
def update_admission_status(request, pk, status):
    admission = get_object_or_404(StudentAdmission, pk=pk)
    if status in ['Approved', 'Rejected']:
        admission.status = status
        admission.save()
        
        if status == 'Approved':
            # Get common password
            common_pwd_obj = GlobalSetting.objects.filter(key='student_common_password_plain').first()
            password = common_pwd_obj.value if common_pwd_obj else "Contact Admin"
            
            # Send Email
            subject = "Admission Approved - Ideal Classes"
            message = f"Hello {admission.full_name},\n\n" \
                      f"Your admission has been successfully approved.\n\n" \
                      f"Course: {admission.category.name} - {admission.branch.name}\n" \
                      f"Year: {admission.year.name if admission.year else 'N/A'}\n\n" \
                      f"You can now log in using:\n" \
                      f"Email: {admission.email}\n" \
                      f"Password: {password}\n\n" \
                      f"Regards,\nIdeal Classes"
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [admission.email],
                    fail_silently=False,
                )
                messages.success(request, f"Admission for {admission.full_name} has been Approved and email sent.")
            except Exception as e:
                messages.warning(request, f"Admission Approved but email failed: {str(e)}")
        else:
            messages.success(request, f"Admission for {admission.full_name} has been {status}")
            
    return redirect('admin_admissions')

@user_passes_test(lambda u: u.is_staff)
def admin_admissions(request):
    status_filter = request.GET.get('status', 'Pending')
    category_filter = request.GET.get('category', '')
    branch_filter = request.GET.get('branch', '')
    
    admissions = StudentAdmission.objects.filter(status=status_filter)
    
    query = request.GET.get('q', '')
    if query:
        admissions = admissions.filter(
            models.Q(full_name__icontains=query) | 
            models.Q(email__icontains=query)
        )
    
    if category_filter:
        admissions = admissions.filter(category__name=category_filter)
    if branch_filter:
        admissions = admissions.filter(branch__name__icontains=branch_filter)
        
    admissions = admissions.order_by('-created_at')
    
    # Handle Password Settings
    pw_form = CommonPasswordForm()
    if request.method == 'POST' and 'set_password' in request.POST:
        pw_form = CommonPasswordForm(request.POST)
        if pw_form.is_valid():
            new_pw = pw_form.cleaned_data['password']
            hashed_pw = make_password(new_pw)
            GlobalSetting.objects.update_or_create(
                key='student_common_password',
                defaults={'value': hashed_pw}
            )
            GlobalSetting.objects.update_or_create(
                key='student_common_password_plain',
                defaults={'value': new_pw}
            )
            messages.success(request, "Common password updated successfully!")
            return redirect('admin_admissions')

    return render(request, 'education/admin_dashboard.html', {
        'admissions': admissions,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'branch_filter': branch_filter,
        'pw_form': pw_form
    })

@user_passes_test(lambda u: u.is_staff)
def manage_content(request):
    contents = Content.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        from .forms import ContentForm
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Hierarchical content uploaded successfully!")
            return redirect('manage_content')
    else:
        from .forms import ContentForm
        form = ContentForm()
        
    return render(request, 'education/manage_content.html', {
        'contents': contents,
        'form': form
    })

@user_passes_test(lambda u: u.is_staff)
def delete_content(request, pk):
    content = get_object_or_404(Content, pk=pk)
    content.delete()
    messages.success(request, "Content deleted.")
    return redirect('manage_content')

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully! Our team will get back to you soon.")
            return redirect('contact_us')
    else:
        form = ContactForm()
    
    return render(request, 'education/contact_us.html', {'form': form})

def privacy_policy(request):
    return render(request, 'education/privacy_policy.html')

def terms_of_use(request):
    return render(request, 'education/terms_of_use.html')

def curriculum(request):
    categories = Category.objects.prefetch_related('years').all()
    return render(request, 'education/curriculum.html', {'categories': categories})

def faculty_login(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name if user.first_name else user.username}!")
                return redirect('home')
            else:
                messages.error(request, "Access denied. Only staff members can log in here.")
        else:
            messages.error(request, "Invalid username or password")
            
    return render(request, 'education/faculty_login.html')

def student_dashboard(request):
    if not request.session.get('is_student'):
        return redirect('student_login')
    
    # Fetch student info
    email = request.session.get('student_email')
    admission = get_object_or_404(StudentAdmission, email=email)
    
    # 1. Get subjects that match student's profile
    # Filtering Logic: subject.course == student.course, subject.department == student.department, subject.year == student.year
    subjects = Subject.objects.filter(
        category=admission.category,
        branch=admission.branch,
        year=admission.year
    )
    
    # 2. Include manually assigned subjects (if any)
    assigned_subjects = admission.subjects.all()
    all_subjects = (subjects | assigned_subjects).distinct().order_by('name')
    
    # 3. Fetch Notes and Videos related to these subjects
    notes = Note.objects.filter(subject__in=all_subjects).select_related('subject')
    videos = Video.objects.filter(subject__in=all_subjects).select_related('subject')
    
    return render(request, 'education/student_dashboard.html', {
        'admission': admission,
        'subjects': all_subjects,
        'notes': notes,
        'videos': videos,
        'total_notes': notes.count(),
        'total_videos': videos.count(),
    })

def content_view(request, class_name):
    return render(request, 'education/content.html', {'class_name': class_name})

def toggle_save_content(request, pk):
    if not request.session.get('is_student'):
        return redirect('login_selection')
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(StudentAdmission, pk=student_id)
    content = get_object_or_404(Content, pk=pk)
    
    saved_item = SavedContent.objects.filter(student=student, content=content).first()
    
    if saved_item:
        saved_item.delete()
        messages.info(request, "Removed from saved items.")
    else:
        SavedContent.objects.create(student=student, content=content)
        messages.success(request, "Saved to your notes!")
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def saved_notes_page(request):
    if not request.session.get('is_student'):
        return redirect('login_selection')
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(StudentAdmission, pk=student_id)
    saved_items = SavedContent.objects.filter(student=student).select_related('content', 'content__chapter', 'content__chapter__subject')
    
    return render(request, 'education/saved_notes.html', {
        'saved_items': saved_items,
        'student': student
    })
