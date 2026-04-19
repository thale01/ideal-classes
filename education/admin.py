from django.contrib import admin
from django import forms
from .models import Category, Branch, Subject, Chapter, Content, Year, ContactMessage, StudentAdmission

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

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    form = SubjectAdminForm
    list_display = ('name', 'branch', 'category', 'year')
    list_filter = ('category', 'year', 'branch')
    search_fields = ('name', 'branch__name', 'category__name', 'year__name')
    inlines = [ChapterInline]

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
    list_display = ('full_name', 'email', 'category', 'branch', 'status', 'created_at')
    list_filter = ('status', 'category', 'branch', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'order')
    list_filter = ('subject__category', 'subject__branch', 'subject')
    search_fields = ('name', 'subject__name')
    inlines = [ContentInline]

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'content_type', 'created_at')
    list_filter = ('content_type', 'chapter__subject__category', 'chapter__subject')
    search_fields = ('title', 'description', 'chapter__name', 'chapter__subject__name')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)

    
