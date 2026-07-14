from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Category, Branch, Subject, Content, StudentAdmission, GlobalSetting, Year, ContactMessage, SavedContent, Note, Video, TopStudent
from .forms import AdmissionForm, ContentForm, CommonPasswordForm, ContactForm, NoteForm
import json
import os
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import Category, Branch, Subject, Content, StudentAdmission, GlobalSetting, Year, ContactMessage, SavedContent, Note, Video, FCMToken, TopStudent, Feedback
import firebase_admin
from firebase_admin import messaging, credentials
from functools import wraps

def active_student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
            
        if not request.session.get('is_student'):
            return redirect('student_login')
            
        student_id = request.session.get('student_id')
        student = StudentAdmission.objects.filter(pk=student_id).first()
        
        if not student or student.status != 'Approved':
            if 'student_id' in request.session:
                del request.session['student_id']
            if 'is_student' in request.session:
                del request.session['is_student']
            return redirect('student_login')
            
        if student.account_status == 'Inactive':
            if 'student_id' in request.session:
                del request.session['student_id']
            if 'is_student' in request.session:
                del request.session['is_student']
            messages.error(request, "Your account is currently inactive. Please contact the administrator.")
            return redirect('student_login')
            
        if student.account_status == 'Graduated':
            if 'student_id' in request.session:
                del request.session['student_id']
            if 'is_student' in request.session:
                del request.session['is_student']
            messages.info(request, "Your course has been completed. Please contact the administrator if you believe this is incorrect.")
            return redirect('student_login')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view



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
    categories = Category.objects.all().only('name')
    
    try:
        top_students = TopStudent.objects.all().order_by('-created_at')
        # Force evaluation to catch any relation/database errors before rendering
        list(top_students[:1])
    except Exception as e:
        top_students = None
        
    # Fetch testimonials for landing page
    testimonials = Feedback.objects.filter(is_approved=True, is_featured=True).select_related('student', 'student__category', 'student__branch').order_by('-updated_at')

    context = {
        'categories': categories,
        'top_students': top_students,
        'testimonials': testimonials
    }
    
    if request.user.is_staff:
        import datetime
        from django.db.models import Count, Avg
        
        # Admin statistics (counts)
        context['total_all_students'] = StudentAdmission.objects.count()
        context['total_students'] = StudentAdmission.objects.filter(status='Approved', account_status='Active').count()
        context['active_students_count'] = StudentAdmission.objects.filter(status='Approved', account_status='Active').count()
        context['graduated_students_count'] = StudentAdmission.objects.filter(status='Approved', account_status='Graduated').count()
        context['inactive_students_count'] = StudentAdmission.objects.filter(status='Approved', account_status='Inactive').count()
        context['pending_admissions'] = StudentAdmission.objects.filter(status='Pending').count()
        context['total_courses'] = Category.objects.count()
        context['total_departments'] = Branch.objects.count()
        context['total_subjects'] = Subject.objects.count()
        context['total_notes'] = Note.objects.count() + Content.objects.filter(content_type='Note').count()
        context['total_videos'] = Video.objects.count() + Content.objects.filter(content_type='Video').count()
        context['total_enquiries'] = ContactMessage.objects.count()
        context['total_feedbacks'] = Feedback.objects.count()
        
        # 1. Students per Course Chart
        courses_chart = list(Category.objects.annotate(num_students=Count('admissions')).values('name', 'num_students'))
        context['courses_chart_json'] = json.dumps(courses_chart)
        
        # 2. Admissions per Month Chart (Python-based database-agnostic grouping)
        admissions_dates = StudentAdmission.objects.values_list('created_at', flat=True)
        months_data = {}
        for dt in admissions_dates:
            if dt:
                m_str = dt.strftime('%b %Y')
                months_data[m_str] = months_data.get(m_str, 0) + 1
        sorted_months = sorted(months_data.keys(), key=lambda m: datetime.datetime.strptime(m, '%b %Y') if m else datetime.datetime.min)
        admissions_chart = [{'month': m, 'count': months_data[m]} for m in sorted_months]
        context['admissions_chart_json'] = json.dumps(admissions_chart)
        
        # 3. Students per Department Chart
        departments_chart = list(Branch.objects.annotate(num_students=Count('admissions')).values('name', 'num_students'))
        context['departments_chart_json'] = json.dumps(departments_chart)
        
        # 4. Notes per Subject Chart
        subject_notes_chart = []
        for sub in Subject.objects.prefetch_related('notes', 'chapters__contents'):
            direct_notes_count = sub.notes.count()
            chapter_notes_count = sum(ch.contents.filter(content_type='Note').count() for ch in sub.chapters.all())
            subject_notes_chart.append({
                'name': sub.name,
                'count': direct_notes_count + chapter_notes_count
            })
        context['subject_notes_chart_json'] = json.dumps(subject_notes_chart)
        
        # 5. Videos per Subject Chart
        subject_videos_chart = []
        for sub in Subject.objects.prefetch_related('videos', 'chapters__contents'):
            direct_videos_count = sub.videos.count()
            chapter_videos_count = sum(ch.contents.filter(content_type='Video').count() for ch in sub.chapters.all())
            subject_videos_chart.append({
                'name': sub.name,
                'count': direct_videos_count + chapter_videos_count
            })
        context['subject_videos_chart_json'] = json.dumps(subject_videos_chart)
        
        # 6. Status Distribution Chart
        status_chart = list(StudentAdmission.objects.filter(status='Approved').values('account_status').annotate(num_students=Count('id')))
        context['status_chart_json'] = json.dumps(status_chart)
        
        # Feedback Analytics Stats
        avg_rating = Feedback.objects.aggregate(avg=Avg('rating'))['avg']
        context['avg_rating'] = round(avg_rating, 1) if avg_rating else 0
        context['total_reviews'] = Feedback.objects.count()
        context['featured_reviews_count'] = Feedback.objects.filter(is_featured=True).count()
        
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for item in Feedback.objects.values('rating').annotate(count=Count('id')):
            r = item['rating']
            if r in rating_counts:
                rating_counts[r] = item['count']
        
        rating_dist_list = []
        for r in sorted(rating_counts.keys(), reverse=True):
            count = rating_counts[r]
            pct = round((count / context['total_reviews'] * 100), 1) if context['total_reviews'] > 0 else 0
            rating_dist_list.append({
                'rating': r,
                'count': count,
                'percentage': pct
            })
        context['rating_distribution_list'] = rating_dist_list
    elif request.session.get('is_student'):
        email = request.session.get('student_email')
        admission = StudentAdmission.objects.filter(email=email).first()
        if admission:
            if admission.account_status == 'Inactive':
                if 'student_id' in request.session:
                    del request.session['student_id']
                if 'is_student' in request.session:
                    del request.session['is_student']
                messages.error(request, "Your account is currently inactive. Please contact the administrator.")
                return redirect('student_login')
            elif admission.account_status == 'Graduated':
                if 'student_id' in request.session:
                    del request.session['student_id']
                if 'is_student' in request.session:
                    del request.session['is_student']
                messages.info(request, "Your course has been completed. Please contact the administrator if you believe this is incorrect.")
                return redirect('student_login')
            # 1. Get subjects that match student's profile (Course and Department)
            subjects = Subject.objects.filter(
                category=admission.category,
                branch=admission.branch
            )
            # Safely match specific year OR subjects that don't have a year assigned (global to department)
            if admission.year:
                subjects = subjects.filter(
                    models.Q(year=admission.year) | models.Q(year__isnull=True)
                )
            
            # 2. Include manually assigned subjects (if any)
            assigned_subjects = admission.subjects.all()
            all_subjects = (subjects | assigned_subjects).distinct().order_by('name')
            
            # 3. Fetch Notes and Videos related to these subjects
            notes = Note.objects.filter(subject__in=all_subjects).select_related('subject')
            videos = Video.objects.filter(subject__in=all_subjects).select_related('subject')
            
            # Fetch watched video IDs for dashboard display
            from .models import WatchedVideo
            watched_video_ids = WatchedVideo.objects.filter(student=admission, video__isnull=False).values_list('video_id', flat=True)
            
            # Calculate progress for each subject
            for sub in all_subjects:
                sub.progress = sub.get_progress(admission)

            context.update({
                'admission': admission,
                'subjects': all_subjects,
                'notes': notes,
                'videos': videos,
                'total_notes': notes.count(),
                'total_videos': videos.count(),
                'watched_video_ids': watched_video_ids,
            })
        
    return render(request, 'education/index.html', context)


@active_student_required
def category_branches(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    # Check if category has years (like Degree/Diploma)
    years = category.years.all()
    if years.exists():
        return render(request, 'education/category_years.html', {'category': category, 'years': years})
        
    # Get branches that have subjects in this category (for 11th/12th)
    branches = Branch.objects.filter(subjects__category=category).distinct()
    return render(request, 'education/category_branches.html', {'category': category, 'branches': branches})

@active_student_required
def year_subjects(request, category_pk, year_pk):
        
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

@active_student_required
def branch_subjects(request, category_pk, branch_pk):
    category = get_object_or_404(Category, pk=category_pk)
    branch = get_object_or_404(Branch, pk=branch_pk)
    subjects = Subject.objects.filter(category=category, branch=branch)
    return render(request, 'education/branch_subjects.html', {
        'category': category,
        'branch': branch,
        'subjects': subjects
    })

@active_student_required
def subject_detail(request, pk):
        
    subject = get_object_or_404(
        Subject.objects.prefetch_related('chapters__contents'), 
        pk=pk
    )
    
    saved_content_ids = []
    watched_content_ids = []
    watched_video_ids = []
    chapters_data = []
    
    if request.session.get('is_student'):
        student_id = request.session.get('student_id')
        student = get_object_or_404(StudentAdmission, pk=student_id)
        saved_content_ids = SavedContent.objects.filter(student_id=student_id).values_list('content_id', flat=True)
        
        # Fetch watched video IDs for this student
        from .models import WatchedVideo
        watched_content_ids = WatchedVideo.objects.filter(student=student, content__isnull=False).values_list('content_id', flat=True)
        watched_video_ids = WatchedVideo.objects.filter(student=student, video__isnull=False).values_list('video_id', flat=True)
        
        # Calculate progress for each chapter
        for chapter in subject.chapters.all():
            total_videos = len(chapter.videos)
            if total_videos > 0:
                watched_count = sum(1 for v in chapter.videos if v.pk in watched_content_ids)
                percentage = min(100, int((watched_count / total_videos) * 100))
            else:
                percentage = None
                watched_count = 0
            
            chapters_data.append({
                'chapter': chapter,
                'total_videos': total_videos,
                'watched_count': watched_count,
                'percentage': percentage
            })
    else:
        # For admin/staff, we don't calculate progress
        for chapter in subject.chapters.all():
            chapters_data.append({
                'chapter': chapter,
                'total_videos': len(chapter.videos),
                'watched_count': 0,
                'percentage': None
            })
        
    return render(request, 'education/subject_detail.html', {
        'subject': subject,
        'saved_content_ids': saved_content_ids,
        'watched_content_ids': watched_content_ids,
        'watched_video_ids': watched_video_ids,
        'chapters_data': chapters_data
    })

@active_student_required
def search(request):
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
            admission = StudentAdmission.objects.get(email__iexact=email)
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
                    # Check lifecycle status first
                    if admission.account_status == 'Inactive':
                        messages.error(request, "Your account is currently inactive. Please contact the administrator.")
                        return redirect('student_login')
                    elif admission.account_status == 'Graduated':
                        messages.info(request, "Your course has been completed. Please contact the administrator if you believe this is incorrect.")
                        return redirect('student_login')

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
            
            import threading
            
            def send_email_async(subj, msg, from_em, to_em):
                try:
                    send_mail(subj, msg, from_em, [to_em], fail_silently=False)
                except Exception as e:
                    print(f"Async email sending failed: {e}")
            
            thread = threading.Thread(
                target=send_email_async,
                args=(subject, message, settings.EMAIL_HOST_USER, admission.email)
            )
            thread.start()
            messages.success(request, f"Admission for {admission.full_name} has been Approved successfully! (Notification email is being sent in the background.)")
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
    notes = Note.objects.select_related('subject', 'subject__category', 'subject__branch', 'subject__year').all().order_by('-created_at')[:100]
    videos = Video.objects.select_related('subject', 'subject__category', 'subject__branch', 'subject__year').all().order_by('-created_at')[:100]
    
    from .forms import NoteForm, VideoForm
    note_form = NoteForm()
    video_form = VideoForm()
    active_tab = 'note'
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_note':
            note_form = NoteForm(request.POST)
            if note_form.is_valid():
                note_form.save()
                messages.success(request, "Study note added successfully!")
                return redirect('manage_content')
            active_tab = 'note'
        elif action == 'add_video':
            video_form = VideoForm(request.POST)
            if video_form.is_valid():
                video_form.save()
                messages.success(request, "Video lecture added successfully!")
                return redirect('manage_content')
            active_tab = 'video'
            
    return render(request, 'education/manage_content.html', {
        'notes': notes,
        'videos': videos,
        'note_form': note_form,
        'video_form': video_form,
        'active_tab': active_tab,
    })

@user_passes_test(lambda u: u.is_staff)
def delete_content(request, pk):
    content = get_object_or_404(Note, pk=pk)
    content.delete()
    messages.success(request, "Note deleted successfully.")
    return redirect('manage_content')

@user_passes_test(lambda u: u.is_staff)
def delete_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    video.delete()
    messages.success(request, "Video lecture deleted successfully.")
    return redirect('manage_content')


def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            enquiry = form.save()
            
            # Send confirmation email
            from django.core.mail import send_mail
            email = form.cleaned_data.get('email')
            name = form.cleaned_data.get('name')
            subject = form.cleaned_data.get('subject')
            
            email_message = (
                f"Hi {name},\n\n"
                f"Thank you for contacting Ideal Classes. We have received your message regarding '{subject}' and will get back to you shortly.\n\n"
                f"Your Message:\n\"{enquiry.message}\"\n\n"
                f"Best regards,\n"
                f"Ideal Classes Team"
            )
            try:
                send_mail(
                    subject="Thank you for contacting Ideal Classes",
                    message=email_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Error sending contact confirmation email: {e}")
                
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
    categories = Category.objects.prefetch_related('years').all().only('name')
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

@active_student_required
def student_dashboard(request):
    
    # Fetch student info
    email = request.session.get('student_email')
    admission = get_object_or_404(StudentAdmission, email=email)
    
    # 1. Get subjects that match student's profile (Course and Department)
    subjects = Subject.objects.filter(
        category=admission.category,
        branch=admission.branch
    )
    # Safely match specific year OR subjects that don't have a year assigned (global to department)
    if admission.year:
        subjects = subjects.filter(
            models.Q(year=admission.year) | models.Q(year__isnull=True)
        )
    
    # 2. Include manually assigned subjects (if any)
    assigned_subjects = admission.subjects.all()
    all_subjects = (subjects | assigned_subjects).distinct().order_by('name')
    
    # 3. Fetch Notes and Videos related to these subjects
    notes = Note.objects.filter(subject__in=all_subjects).select_related('subject')
    videos = Video.objects.filter(subject__in=all_subjects).select_related('subject')
    
    # Fetch watched video IDs for dashboard display
    from .models import WatchedVideo, Feedback
    watched_video_ids = WatchedVideo.objects.filter(student=admission, video__isnull=False).values_list('video_id', flat=True)
    
    # Calculate progress for each subject
    for sub in all_subjects:
        sub.progress = sub.get_progress(admission)

    student_feedback = Feedback.objects.filter(student=admission).first()

    return render(request, 'education/student_dashboard.html', {
        'admission': admission,
        'subjects': all_subjects,
        'notes': notes,
        'videos': videos,
        'total_notes': notes.count(),
        'total_videos': videos.count(),
        'watched_video_ids': watched_video_ids,
        'student_feedback': student_feedback
    })

@active_student_required
def submit_feedback(request):
    if request.method == 'POST':
        student_id = request.session.get('student_id')
        student = get_object_or_404(StudentAdmission, pk=student_id)
        
        try:
            rating = int(request.POST.get('rating', 5))
        except ValueError:
            rating = 5
            
        comment = request.POST.get('comment', '').strip()
        
        if not comment:
            messages.error(request, "Please enter your review comment.")
            return redirect('student_dashboard')
            
        from .models import Feedback
        feedback, created = Feedback.objects.update_or_create(
            student=student,
            defaults={
                'rating': rating,
                'comment': comment
            }
        )
        
        if created:
            messages.success(request, "Thank you for your feedback! It has been submitted for moderation.")
        else:
            messages.success(request, "Your feedback has been successfully updated.")
            
    return redirect('student_dashboard')

@active_student_required
def content_view(request, class_name):
    return render(request, 'education/content.html', {'class_name': class_name})

@active_student_required
def toggle_save_content(request, pk):
    
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

@active_student_required
def toggle_watch_content(request, pk):
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(StudentAdmission, pk=student_id)
    content = get_object_or_404(Content, pk=pk)
    
    from .models import WatchedVideo
    watched_record = WatchedVideo.objects.filter(student=student, content=content).first()
    
    if watched_record:
        watched_record.delete()
        watched = False
        message = "Marked as unwatched."
    else:
        WatchedVideo.objects.create(student=student, content=content)
        watched = True
        message = "Marked as watched!"
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'watched': watched,
            'message': message
        })
        
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@active_student_required
def toggle_watch_video(request, pk):
        
    student_id = request.session.get('student_id')
    student = get_object_or_404(StudentAdmission, pk=student_id)
    video = get_object_or_404(Video, pk=pk)
    
    from .models import WatchedVideo
    watched_record = WatchedVideo.objects.filter(student=student, video=video).first()
    
    if watched_record:
        watched_record.delete()
        watched = False
        message = "Marked as unwatched."
    else:
        WatchedVideo.objects.create(student=student, video=video)
        watched = True
        message = "Marked as watched!"
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'watched': watched,
            'message': message
        })
        
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@active_student_required
def saved_notes_page(request):
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(StudentAdmission, pk=student_id)
    saved_items = SavedContent.objects.filter(student=student).select_related('content', 'content__chapter', 'content__chapter__subject')
    
    return render(request, 'education/saved_notes.html', {
        'saved_items': saved_items,
        'student': student
    })

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /student/dashboard/",
        "Disallow: /my-saved-notes/",
        "Disallow: /search/",
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def sitemap_xml(request):
    domain = f"{request.scheme}://{request.get_host()}"
    
    urls = [
        {'loc': f"{domain}/", 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': f"{domain}/curriculum/", 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': f"{domain}/admission/", 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': f"{domain}/contact-us/", 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f"{domain}/login-selection/", 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': f"{domain}/student/login/", 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': f"{domain}/faculty/login/", 'changefreq': 'monthly', 'priority': '0.4'},
        {'loc': f"{domain}/privacy-policy/", 'changefreq': 'yearly', 'priority': '0.3'},
        {'loc': f"{domain}/terms-of-use/", 'changefreq': 'yearly', 'priority': '0.3'},
    ]
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml_content += '  <url>\n'
        xml_content += f"    <loc>{url['loc']}</loc>\n"
        xml_content += f"    <changefreq>{url['changefreq']}</changefreq>\n"
        xml_content += f"    <priority>{url['priority']}</priority>\n"
        xml_content += '  </url>\n'
    xml_content += '</urlset>'
    
    return HttpResponse(xml_content, content_type="application/xml")

