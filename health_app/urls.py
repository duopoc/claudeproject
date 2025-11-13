"""
Health App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'health_app'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add/', views.add_metric_view, name='add_metric'),
    path('history/', views.history_view, name='history'),
    path('record/<int:record_id>/update/', views.update_record_view, name='update_record'),
]
