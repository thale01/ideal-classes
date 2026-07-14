from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name

class Year(models.Model):
    category = models.ForeignKey(Category, related_name='years', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Subject(models.Model):
    branch = models.ForeignKey(Branch, related_name='subjects', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='subjects', on_delete=models.CASCADE)
    year = models.ForeignKey(Year, related_name='subjects', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        unique_together = ('branch', 'category', 'year', 'name')

    @property
    def total_items(self):
        return sum(chapter.contents.count() for chapter in self.chapters.all())

    def __str__(self):
        # Format: Subject Name - Course - Department - Year (with dynamic N+1 query optimization and complete crash protection)
        from django.core.exceptions import ObjectDoesNotExist

        try:
            category_name = self.category.name if 'category' in self.__dict__ else getattr(self.category, 'name', '')
        except ObjectDoesNotExist:
            category_name = f"Course ID: {self.category_id}"
        except Exception:
            category_name = "Unknown Course"

        try:
            branch_name = self.branch.name if 'branch' in self.__dict__ else getattr(self.branch, 'name', '')
        except ObjectDoesNotExist:
            branch_name = f"Dept ID: {self.branch_id}"
        except Exception:
            branch_name = "Unknown Department"

        year_name = ""
        if self.year_id:
            try:
                year_name = f" - {self.year.name}" if 'year' in self.__dict__ else f" - {getattr(self.year, 'name', '')}"
            except ObjectDoesNotExist:
                year_name = f" - Year ID: {self.year_id}"
            except Exception:
                year_name = " - Unknown Year"

        return f"{self.name} - {category_name} - {branch_name}{year_name}"

    def get_progress(self, student):
        # Prevent circular imports
        from .models import Content, WatchedVideo
        
        # 1. Structured chapter-based videos
        total_chapter_videos = Content.objects.filter(chapter__subject=self, content_type='Video').count()
        # 2. Direct videos
        total_direct_videos = self.videos.count()
        
        total_videos = total_chapter_videos + total_direct_videos
        if total_videos == 0:
            return None
            
        watched_chapter_videos = WatchedVideo.objects.filter(student=student, content__chapter__subject=self).count()
        watched_direct_videos = WatchedVideo.objects.filter(student=student, video__subject=self).count()
        
        watched_total = watched_chapter_videos + watched_direct_videos
        
        percentage = min(100, int((watched_total / total_videos) * 100))
        return {
            'total': total_videos,
            'watched': watched_total,
            'percentage': percentage
        }

class Chapter(models.Model):
    subject = models.ForeignKey(Subject, related_name='chapters', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('subject', 'name')

    def __str__(self):
        return f"{self.name} | {self.subject.name}"

    @property
    def videos(self):
        return [c for c in self.contents.all() if c.content_type == 'Video']

    @property
    def notes(self):
        return [c for c in self.contents.all() if c.content_type == 'Notes']

class Content(models.Model):
    CONTENT_TYPES = (
        ('Notes', 'Notes'),
        ('Video', 'Video'),
    )
    chapter = models.ForeignKey(Chapter, related_name='contents', on_delete=models.CASCADE, null=True, blank=True)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    file = models.FileField(upload_to='notes/', blank=True, null=True, help_text="Upload a file or provide a URL below")
    file_url = models.URLField(blank=True, null=True, help_text="Link to external storage (Google Drive, Cloudinary, etc.)")
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.content_type})"

    @property
    def get_file_link(self):
        if self.file_url:
            link = self.file_url.strip()
            # Convert Google Drive link to preview link for direct PDF viewing
            if 'drive.google.com' in link:
                if '/file/d/' in link:
                    parts = link.split('/file/d/')
                    if len(parts) > 1:
                        file_id = parts[1].split('/')[0]
                        return f"https://drive.google.com/file/d/{file_id}/preview"
                elif 'open?id=' in link:
                    parts = link.split('open?id=')
                    if len(parts) > 1:
                        file_id = parts[1].split('&')[0]
                        return f"https://drive.google.com/file/d/{file_id}/preview"
            return link
        if self.file:
            return self.file.url
        return "#"

    @property
    def yt_embed_url(self):
        if self.video_url and 'youtube.com' in self.video_url:
            video_id = self.video_url.split('v=')[-1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif self.video_url and 'youtu.be' in self.video_url:
            video_id = self.video_url.split('/')[-1]
            return f"https://www.youtube.com/embed/{video_id}"
        return self.video_url

class StudentAdmission(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    ACCOUNT_STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Graduated', 'Graduated'),
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='admissions')
    year = models.ForeignKey(Year, on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='admissions')
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        year_str = f" - {self.year.name}" if self.year else ""
        return f"{self.full_name} - {self.category.name}{year_str} {self.branch.name} ({self.status})"

class GlobalSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.key

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

class SavedContent(models.Model):
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE, related_name='saved_items')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'content')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.student.full_name} saved {self.content.title}"

class Note(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='notes')
    drive_link = models.URLField(default='', help_text="Google Drive PDF Link")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

    @property
    def get_link(self):
        link = self.drive_link.strip() if self.drive_link else ""
        if not link:
            return "#"
        if not (link.startswith('http://') or link.startswith('https://')):
            link = f"https://{link}"
        
        # Convert Google Drive link to preview link for direct PDF viewing
        if 'drive.google.com' in link:
            if '/file/d/' in link:
                parts = link.split('/file/d/')
                if len(parts) > 1:
                    file_id = parts[1].split('/')[0]
                    return f"https://drive.google.com/file/d/{file_id}/preview"
            elif 'open?id=' in link:
                parts = link.split('open?id=')
                if len(parts) > 1:
                    file_id = parts[1].split('&')[0]
                    return f"https://drive.google.com/file/d/{file_id}/preview"
                    
        return link

class Video(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='videos')
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

    @property
    def yt_embed_url(self):
        if 'youtube.com' in self.video_url:
            video_id = self.video_url.split('v=')[-1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be' in self.video_url:
            video_id = self.video_url.split('/')[-1]
            return f"https://www.youtube.com/embed/{video_id}"
        return self.video_url

class FCMToken(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='fcm_tokens', null=True, blank=True)
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.user.username if self.user else "Anonymous"
        return f"Token for {name} ({self.created_at.strftime('%Y-%m-%d')})"

class TopStudent(models.Model):
    name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='top_students/', help_text="Upload student photo")
    course = models.CharField(max_length=200, help_text="Course Name (e.g. Diploma, Degree, 11th)")
    department = models.CharField(max_length=200, help_text="Department/Stream (e.g. Mechanical, Computer, Science)")
    subject = models.CharField(max_length=200, help_text="Subject Name (e.g. Mathematics, Physics)")
    score_obtained = models.PositiveIntegerField(help_text="Marks obtained by student")
    total_marks = models.PositiveIntegerField(help_text="Total marks for the subject")
    achievement = models.CharField(max_length=250, blank=True, null=True, help_text="Specific achievement or rank (e.g. Class Topper, Gold Medalist)")
    academic_year = models.CharField(max_length=50, help_text="Academic Year (e.g. 2025-2026)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Top Student"
        verbose_name_plural = "Top Students"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject} ({self.percentage}%)"

    @property
    def percentage(self):
        if self.total_marks > 0:
            return round((self.score_obtained / self.total_marks) * 100, 2)
        return 0

class WatchedVideo(models.Model):
    student = models.ForeignKey(StudentAdmission, on_delete=models.CASCADE, related_name='watched_videos')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, null=True, blank=True, related_name='watched_records')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True, related_name='watched_records')
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Watched Video"
        verbose_name_plural = "Watched Videos"
        # Ensure a student can only mark a specific content video or direct video as watched once
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'content'],
                name='unique_student_content_watch',
                condition=models.Q(content__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['student', 'video'],
                name='unique_student_video_watch',
                condition=models.Q(video__isnull=False)
            ),
        ]

    def __str__(self):
        video_title = self.content.title if self.content else (self.video.title if self.video else "Unknown Video")
        return f"{self.student.full_name} watched {video_title}"
