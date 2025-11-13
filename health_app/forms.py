"""
Health App forms for health record management
"""
from django import forms
from .models import HealthRecord


class HealthRecordForm(forms.ModelForm):
    """Form for creating and updating health records"""
    class Meta:
        model = HealthRecord
        fields = [
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'height', 'weight', 'waist',
            'cholesterol', 'ldl', 'hdl', 'fbs', 'triglycerides',
            'bmi', 'fat_percent', 'visceral_fat', 'muscle_percent',
            'bmr', 'body_age', 'recorded_at'
        ]
        widgets = {
            'blood_pressure_systolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ความดันบน'}),
            'blood_pressure_diastolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ความดันล่าง'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'ส่วนสูง (cm)'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'น้ำหนัก (kg)'}),
            'waist': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'เส้นรอบเอว (cm)'}),
            'cholesterol': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Cholesterol (mg/dL)'}),
            'ldl': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'LDL (mg/dL)'}),
            'hdl': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'HDL (mg/dL)'}),
            'fbs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'FBS (mg/dL)'}),
            'triglycerides': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Triglycerides (mg/dL)'}),
            'bmi': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'BMI'}),
            'fat_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'เปอร์เซ็นต์ไขมัน'}),
            'visceral_fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'ไขมันในช่องท้อง'}),
            'muscle_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'เปอร์เซ็นต์กล้ามเนื้อ'}),
            'bmr': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'อัตราการเผาผลาญ BMR'}),
            'body_age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'อายุร่างกาย'}),
            'recorded_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recorded_at'].input_formats = ['%Y-%m-%dT%H:%M']


class DateRangeFilterForm(forms.Form):
    """Form for filtering records by date range"""
    date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='วันที่เริ่มต้น'
    )
    date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='วันที่สิ้นสุด'
    )
