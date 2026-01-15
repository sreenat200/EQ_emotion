from django.contrib import admin
from .models import AssessmentResult

@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ('profession', 'age', 'gender', 'overall_score', 'rating', 'created_at')
    list_filter = ('profession', 'rating', 'created_at')
    search_fields = ('profession', 'rating')
    readonly_fields = ('created_at', 'scores', 'scenario_used')
