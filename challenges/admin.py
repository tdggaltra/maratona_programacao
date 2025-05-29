# challenges/admin.py
from django.contrib import admin
from .models import ProgrammingLanguage, BrazilState, Challenge, Submission

@admin.register(ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'extension')
    search_fields = ('name',)

@admin.register(BrazilState)
class BrazilStateAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'order')
    list_filter = ('region',)
    search_fields = ('name', 'abbreviation')
    ordering = ('order',)

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'state', 'difficulty', 'points', 'language')
    list_filter = ('difficulty', 'language', 'state__region')
    search_fields = ('title', 'description')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'state', 'difficulty', 'points', 'language')
        }),
        ('Descrição', {
            'fields': ('description', 'input_description', 'output_description', 'example_input', 'example_output')
        }),
        ('Configurações', {
            'fields': ('test_cases', 'time_limit')
        }),
    )

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'status', 'execution_time', 'submitted_at')
    list_filter = ('status', 'language', 'challenge')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('submitted_at',)
