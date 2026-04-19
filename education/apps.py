from django.apps import AppConfig


class EducationConfig(AppConfig):
    name = 'education'

    def ready(self):
        import education.signals
