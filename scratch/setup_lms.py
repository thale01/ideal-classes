import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from education.models import Category, Branch, Year

def setup_lms_data():
    # Categories
    categories = ['11th', '12th', 'Diploma', 'Degree']
    cat_objs = {}
    for name in categories:
        cat, created = Category.objects.get_or_create(name=name)
        cat_objs[name] = cat
        print(f"Category '{name}' {'created' if created else 'already exists'}")

    # Years
    years_data = {
        'Diploma': ['1st Year', '2nd Year', '3rd Year'],
        'Degree': ['1st Year', '2nd Year', '3rd Year', '4th Year']
    }
    for cat_name, year_names in years_data.items():
        cat = cat_objs[cat_name]
        for y_name in year_names:
            y, created = Year.objects.get_or_create(category=cat, name=y_name)
            print(f"Year '{y_name}' for '{cat_name}' {'created' if created else 'already exists'}")

    # Branches
    branches_11_12 = ['Arts', 'Commerce', 'Science']
    branches_tech = ['Computer', 'Mechanical', 'Civil', 'Electrical', 'Instrumental']
    
    for b_name in list(set(branches_11_12 + branches_tech)):
        b, created = Branch.objects.get_or_create(name=b_name)
        print(f"Branch '{b_name}' {'created' if created else 'already exists'}")

if __name__ == "__main__":
    setup_lms_data()
