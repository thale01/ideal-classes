import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from education.models import Year, Subject, StudentAdmission
from django.db.models import Count
from django.db import transaction

duplicates = (
    Year.objects.values('category', 'name')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

with transaction.atomic():
    for d in duplicates:
        years = list(Year.objects.filter(category_id=d['category'], name=d['name']).order_by('id'))
        master = years[0]
        to_delete = years[1:]
        
        print(f"Merging duplicates for {master}: keeping {master.id}, deleting {[y.id for y in to_delete]}")
        
        for y in to_delete:
            # Update Subjects
            updated_subjects = Subject.objects.filter(year=y).update(year=master)
            print(f"  Updated {updated_subjects} subjects")
            
            # Update Admissions
            updated_admissions = StudentAdmission.objects.filter(year=y).update(year=master)
            print(f"  Updated {updated_admissions} admissions")
            
            # Delete the duplicate year
            y.delete()

print("Deduplication complete.")
