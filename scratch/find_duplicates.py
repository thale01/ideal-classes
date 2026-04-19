import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from education.models import Year
from django.db.models import Count

duplicates = (
    Year.objects.values('category', 'name')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

if not duplicates:
    print("No duplicates found.")
else:
    print(f"Found {len(duplicates)} duplicate year groups.")
    for d in duplicates:
        print(f"Category ID: {d['category']}, Name: {d['name']}, Count: {d['count']}")
        years = Year.objects.filter(category_id=d['category'], name=d['name'])
        for y in years:
            # We check the database column directly since 'branch' is missing in models.py
            # But wait, we can't easily check 'branch' if it's missing in models.py
            # But we know they are duplicates.
            print(f"  - Year ID: {y.id}")
