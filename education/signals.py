from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudentAdmission, Subject

@receiver(post_save, sender=StudentAdmission)
def assign_subjects_on_approval(sender, instance, created, **kwargs):
    if instance.status == 'Approved':
        # Filter matching subjects
        matching_subjects = Subject.objects.filter(
            branch=instance.branch,
            category=instance.category,
            year=instance.year
        )
        # Assign them using set()
        instance.subjects.set(matching_subjects)
