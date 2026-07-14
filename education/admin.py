from django.contrib import admin
from django import forms
from .models import Category, Branch, Subject, Chapter, Content, Year, ContactMessage, StudentAdmission, Note, Video, TopStudent, WatchedVideo, Feedback

class ContentInline(admin.TabularInline):
    model = Content
    extra = 1

class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1
    show_change_link = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class YearAdminForm(forms.ModelForm):
    class Meta:
        model = Year
        fields = '__all__'
        labels = {
            'category': 'Course',
        }

@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    form = YearAdminForm
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class SubjectAdminForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = '__all__'
        labels = {
            'branch': 'Department',
            'category': 'Course',
        }

class NoteInline(admin.TabularInline):
    model = Note
    extra = 1

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    form = SubjectAdminForm
    list_display = ('name', 'branch', 'category', 'year')
    list_filter = ('category', 'year', 'branch')
    search_fields = ('name', 'branch__name', 'category__name', 'year__name')
    inlines = [ChapterInline, NoteInline, VideoInline]

class StudentAdmissionAdminForm(forms.ModelForm):
    class Meta:
        model = StudentAdmission
        fields = '__all__'
        labels = {
            'branch': 'Department',
            'category': 'Course',
        }

@admin.register(StudentAdmission)
class StudentAdmissionAdmin(admin.ModelAdmin):
    form = StudentAdmissionAdminForm
    list_display = ('full_name', 'category', 'branch', 'year', 'account_status', 'status', 'created_at')
    list_filter = ('account_status', 'status', 'category', 'branch', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_select_related = ('category', 'branch', 'year')
    actions = ['mark_graduated', 'mark_inactive', 'mark_active']

    @admin.action(description="Mark selected as Graduated")
    def mark_graduated(self, request, queryset):
        updated = queryset.update(account_status='Graduated')
        self.message_user(request, f"Successfully marked {updated} students as Graduated.")

    @admin.action(description="Mark selected as Inactive")
    def mark_inactive(self, request, queryset):
        updated = queryset.update(account_status='Inactive')
        self.message_user(request, f"Successfully marked {updated} students as Inactive.")

    @admin.action(description="Activate selected")
    def mark_active(self, request, queryset):
        updated = queryset.update(account_status='Active')
        self.message_user(request, f"Successfully activated {updated} students.")

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'order')
    list_filter = ('subject__category', 'subject__branch', 'subject')
    search_fields = ('name', 'subject__name')
    list_select_related = ('subject', 'subject__branch', 'subject__category', 'subject__year')
    inlines = [ContentInline]

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'content_type', 'created_at')
    list_filter = ('content_type', 'chapter__subject__category', 'chapter__subject')
    search_fields = ('title', 'description', 'chapter__name', 'chapter__subject__name')
    list_select_related = ('chapter', 'chapter__subject')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description="Mark selected enquiries as Read")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"Successfully marked {updated} enquiries as Read.")

    @admin.action(description="Mark selected enquiries as Unread")
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"Successfully marked {updated} enquiries as Unread.")

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'rating', 'is_approved', 'is_featured', 'created_at', 'updated_at')
    list_filter = ('rating', 'is_approved', 'is_featured', 'created_at')
    search_fields = ('student__full_name', 'comment')
    actions = ['approve_feedback', 'reject_feedback', 'feature_feedback', 'unfeature_feedback']

    @admin.action(description="Approve selected feedback")
    def approve_feedback(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Successfully approved {updated} feedbacks.")

    @admin.action(description="Reject selected feedback")
    def reject_feedback(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Successfully rejected {updated} feedbacks.")

    @admin.action(description="Feature selected feedback (Show on home page)")
    def feature_feedback(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"Successfully featured {updated} feedbacks on the home page.")

    @admin.action(description="Unfeature selected feedback (Hide from home page)")
    def unfeature_feedback(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"Successfully unfeatured {updated} feedbacks.")

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'drive_link', 'created_at')
    list_filter = ('subject__category', 'subject__branch', ('subject', admin.RelatedOnlyFieldListFilter))
    search_fields = ('title', 'subject__name', 'drive_link')
    list_select_related = ('subject', 'subject__branch', 'subject__category', 'subject__year')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "subject":
            kwargs["queryset"] = Subject.objects.select_related('branch', 'category', 'year')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'video_url', 'created_at')
    list_filter = ('subject__category', 'subject__branch', 'subject')
    search_fields = ('title', 'subject__name', 'video_url')
    list_select_related = ('subject', 'subject__branch', 'subject__category', 'subject__year')

@admin.register(TopStudent)
class TopStudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'department', 'subject', 'score_obtained', 'total_marks', 'percentage_display', 'academic_year', 'created_at')
    list_filter = ('course', 'department', 'academic_year')
    search_fields = ('name', 'subject', 'achievement')
    ordering = ('-created_at',)

    def percentage_display(self, obj):
        return f"{obj.percentage}%"
    percentage_display.short_description = 'Percentage'

@admin.register(WatchedVideo)
class WatchedVideoAdmin(admin.ModelAdmin):
    list_display = ('student', 'video_or_content_title', 'watched_at')
    list_filter = ('watched_at', 'student__category', 'student__branch')
    search_fields = ('student__full_name', 'content__title', 'video__title')
    list_select_related = ('student', 'content', 'video')

    def video_or_content_title(self, obj):
        if obj.content:
            return f"[Chapter Video] {obj.content.title}"
        if obj.video:
            return f"[Direct Video] {obj.video.title}"
        return "Unknown Video"
    video_or_content_title.short_description = 'Video Title'

