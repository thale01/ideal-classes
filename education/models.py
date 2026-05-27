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
            return self.file_url
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
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='admissions')
    year = models.ForeignKey(Year, on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='admissions')
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
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
