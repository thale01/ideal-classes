import os
import django

import sys
sys.path.append(r'C:\Users\siddh\OneDrive\Desktop\IDEAL-CLASSES')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import site
from education.models import Note

def test_admin_note_page():
    print("Testing NoteAdmin list page locally...")
    note_admin = site._registry[Note]
    
    # Create a request factory
    factory = RequestFactory()
    request = factory.get('/admin/education/note/')
    
    # Create a superuser
    superuser, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_superuser': True, 'is_staff': True}
    )
    request.user = superuser
    
    try:
        # Call changelist_view
        response = note_admin.changelist_view(request)
        print("Success! Changelist status code:", response.status_code)
    except Exception as e:
        print("Error encountered:")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_admin_note_page()
