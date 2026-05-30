import os
import sys
import django

sys.path.append(r'C:\Users\siddh\OneDrive\Desktop\IDEAL-CLASSES')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from education.models import Category, Branch, StudentAdmission, Subject, Year
from django.db import transaction

def test_admission_save_signal():
    print("Testing StudentAdmission save signal locally...")
    
    # Create required lookup objects
    category, _ = Category.objects.get_or_create(name="Diploma")
    branch, _ = Branch.objects.get_or_create(name="Mechanical")
    year, _ = Year.objects.get_or_create(category=category, name="Diploma - 1st Year")
    
    # Create student admission
    try:
        with transaction.atomic():
            admission = StudentAdmission.objects.create(
                full_name="Test Student",
                email="test_student@example.com",
                phone="1234567890",
                category=category,
                branch=branch,
                year=year,
                status="Pending"
            )
            print("Successfully created pending admission.")
            
            # Now simulate approval which triggers the signal
            admission.status = "Approved"
            print("Saving approved admission...")
            admission.save()
            print("Approved admission saved successfully!")
            
            # Force a rollback so we don't dirty the local database
            raise Exception("Rollback successfully")
    except Exception as e:
        if str(e) == "Rollback successfully":
            print("Test passed successfully (rolled back transaction).")
        else:
            print("Error encountered:")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_admission_save_signal()
