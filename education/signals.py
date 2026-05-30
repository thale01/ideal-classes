from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from .models import StudentAdmission, Subject

@receiver(post_save, sender=StudentAdmission)
def assign_subjects_on_approval(sender, instance, created, **kwargs):
    if instance.status == 'Approved' and not instance.subjects.exists():
        # Filter matching subjects based on Course and Department
        matching_subjects = Subject.objects.filter(
            branch=instance.branch,
            category=instance.category
        )
        # Safely match specific year OR subjects that don't have a year assigned (global to department)
        if instance.year:
            matching_subjects = matching_subjects.filter(
                Q(year=instance.year) | Q(year__isnull=True)
            )
        # Assign them using set()
        instance.subjects.set(matching_subjects)
