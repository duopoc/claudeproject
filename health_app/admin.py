"""
Health App admin configuration
"""
from django.contrib import admin
from .models import HealthRecord


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'recorded_at', 'bmi', 'fat_percent', 'visceral_fat', 'muscle_percent']
    list_filter = ['recorded_at', 'user']
    search_fields = ['user__username', 'user__profile__firstname', 'user__profile__lastname']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'recorded_at'
    
    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'recorded_at')
        }),
        ('Measurements', {
            'fields': ('blood_pressure_systolic', 'blood_pressure_diastolic', 'height', 'weight', 'waist')
        }),
        ('Body Composition', {
            'fields': ('bmi', 'fat_percent', 'visceral_fat', 'muscle_percent', 'bmr', 'body_age')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
