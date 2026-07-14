from django.test import TestCase
from django.contrib.auth.models import User
from .models import Category, Branch, Subject, Chapter, Content, Video, StudentAdmission, WatchedVideo

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
