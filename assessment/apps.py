from django.apps import AppConfig


class AssessmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assessment'

    def ready(self):
        print("Assessment App Ready - Console Output Verified")
