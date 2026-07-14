from django.test import TestCase
from django.contrib.auth.models import User
from .models import Category, Branch, Subject, Chapter, Content, Video, StudentAdmission, WatchedVideo, GlobalSetting

class VideoProgressTestCase(TestCase):
    def setUp(self):
        # Create categories, branches, etc.
        self.category = Category.objects.create(name="Diploma")
        self.branch = Branch.objects.create(name="Computer")
        self.subject = Subject.objects.create(
            category=self.category,
            branch=self.branch,
            name="Data Structures"
        )
        self.chapter = Chapter.objects.create(
            subject=self.subject,
            name="Linked Lists",
            order=1
        )
        self.student = StudentAdmission.objects.create(
            full_name="Siddhesh Patil",
            email="siddhesh@example.com",
            phone="1234567890",
            category=self.category,
            branch=self.branch,
            status="Approved"
        )

    def test_progress_calculation(self):
        # 1. No videos - get_progress should return None
        progress = self.subject.get_progress(self.student)
        self.assertIsNone(progress)

        # 2. Add one chapter-based video and one direct video
        content_video = Content.objects.create(
            chapter=self.chapter,
            title="Intro to Linked Lists",
            content_type="Video",
            video_url="https://www.youtube.com/watch?v=123"
        )
        direct_video = Video.objects.create(
            subject=self.subject,
            title="Linked Lists Part 2",
            video_url="https://www.youtube.com/watch?v=456"
        )

        # 3. 0% progress
        progress = self.subject.get_progress(self.student)
        self.assertIsNotNone(progress)
        self.assertEqual(progress['total'], 2)
        self.assertEqual(progress['watched'], 0)
        self.assertEqual(progress['percentage'], 0)

        # 4. Watch chapter video - progress should be 50%
        WatchedVideo.objects.create(student=self.student, content=content_video)
        progress = self.subject.get_progress(self.student)
        self.assertEqual(progress['watched'], 1)
        self.assertEqual(progress['percentage'], 50)

        # 5. Watch direct video - progress should be 100%
        WatchedVideo.objects.create(student=self.student, video=direct_video)
        progress = self.subject.get_progress(self.student)
        self.assertEqual(progress['watched'], 2)
        self.assertEqual(progress['percentage'], 100)

from django.urls import reverse
from django.contrib.auth.hashers import make_password

class StudentLifecycleTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Diploma")
        self.branch = Branch.objects.create(name="Computer")
        self.common_pwd = GlobalSetting.objects.create(
            key='student_common_password',
            value=make_password('common123')
        )
        # Active Student
        self.active_student = StudentAdmission.objects.create(
            full_name="Active Student",
            email="active@example.com",
            phone="1111111111",
            category=self.category,
            branch=self.branch,
            status="Approved",
            account_status="Active"
        )
        # Inactive Student
        self.inactive_student = StudentAdmission.objects.create(
            full_name="Inactive Student",
            email="inactive@example.com",
            phone="2222222222",
            category=self.category,
            branch=self.branch,
            status="Approved",
            account_status="Inactive"
        )
        # Graduated Student
        self.graduated_student = StudentAdmission.objects.create(
            full_name="Graduated Student",
            email="graduated@example.com",
            phone="3333333333",
            category=self.category,
            branch=self.branch,
            status="Approved",
            account_status="Graduated"
        )

    def test_student_login_statuses(self):
        # 1. Test Active student login - should succeed and redirect to dashboard
        response = self.client.post(reverse('student_login'), {
            'email': 'active@example.com',
            'password': 'common123'
        })
        self.assertRedirects(response, reverse('student_dashboard'))
        self.client.logout()

        # 2. Test Inactive student login - should fail and redirect to login page with message
        response = self.client.post(reverse('student_login'), {
            'email': 'inactive@example.com',
            'password': 'common123'
        }, follow=True)
        self.assertRedirects(response, reverse('student_login'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Your account is currently inactive. Please contact the administrator.")

        # 3. Test Graduated student login - should fail and redirect to login page with message
        response = self.client.post(reverse('student_login'), {
            'email': 'graduated@example.com',
            'password': 'common123'
        }, follow=True)
        self.assertRedirects(response, reverse('student_login'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Your course has been completed. Please contact the administrator if you believe this is incorrect.")

    def test_decorator_enforcement(self):
        # Log in as active student
        session = self.client.session
        session['student_id'] = self.active_student.id
        session['student_email'] = self.active_student.email
        session['is_student'] = True
        session.save()

        # Dashboard should be accessible
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Deactivate student in database
        self.active_student.account_status = 'Inactive'
        self.active_student.save()

        # Accessing dashboard should now clear session and redirect to login
        response = self.client.get(reverse('student_dashboard'), follow=True)
        self.assertRedirects(response, reverse('student_login'))
        self.assertNotIn('is_student', self.client.session)

    def test_homepage_student_count(self):
        # Create a staff user to view homepage stats
        staff_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.login(username='admin', password='password')

        response = self.client.get(reverse('home'))
        # Total active students should be 1 (only self.active_student)
        self.assertEqual(response.context['total_students'], 1)
