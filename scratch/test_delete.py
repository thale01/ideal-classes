import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from education.models import Branch, Subject, StudentAdmission

print("Simulating branch deletion...")

# Try to find a branch that has subjects or admissions
branch = Branch.objects.first()
if not branch:
    print("No branch found to test deletion.")
else:
    print(f"Attempting to delete branch: {branch.name}")
    try:
        # We use a transaction to roll back after testing
        from django.db import transaction
        with transaction.atomic():
            branch.delete()
            print("Deletion successful in simulation (rolled back anyway).")
            # Force a rollback
            raise Exception("Force rollback")
    except Exception as e:
        if str(e) == "Force rollback":
            print("Finished simulation.")
        else:
            print(f"Error during deletion: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
