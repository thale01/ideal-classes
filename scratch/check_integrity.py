import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from education.models import Branch, Subject, StudentAdmission

print("Checking for integrity issues...")

# Check if any Subject has a branch that doesn't exist (though FK should prevent this)
subjects = Subject.objects.all()
for s in subjects:
    try:
        b = s.branch
    except Branch.DoesNotExist:
        print(f"Subject {s.id} has a missing branch!")

# Check if any StudentAdmission has a branch that doesn't exist
admissions = StudentAdmission.objects.all()
for a in admissions:
    try:
        b = a.branch
    except Branch.DoesNotExist:
        print(f"Admission {a.id} has a missing branch!")

print("Check complete.")
