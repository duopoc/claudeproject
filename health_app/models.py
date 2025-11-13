"""
Health App models for tracking health metrics
"""
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class HealthRecord(models.Model):
    """Health metrics record"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_records')
    
    # Measurements
    blood_pressure_systolic = models.IntegerField(verbose_name='ความดันบน')
    blood_pressure_diastolic = models.IntegerField(verbose_name='ความดันล่าง')
    height = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='ส่วนสูง (cm)')
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='น้ำหนัก (kg)')
    waist = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='เส้นรอบเอว (cm)')
    
    # Blood work metrics
    cholesterol = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Cholesterol (mg/dL)', default=0, null=True, blank=True)
    ldl = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='LDL (mg/dL)', default=0, null=True, blank=True)
    hdl = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='HDL (mg/dL)', default=0, null=True, blank=True)
    fbs = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='FBS (mg/dL)', default=0, null=True, blank=True)
    triglycerides = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Triglycerides (mg/dL)', default=0, null=True, blank=True) 
    
    # Body composition
    bmi = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='BMI')
    fat_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='เปอร์เซ็นต์ไขมัน')
    visceral_fat = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='ไขมันในช่องท้อง')
    muscle_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='เปอร์เซ็นต์กล้ามเนื้อ')
    bmr = models.IntegerField(verbose_name='อัตราการเผาผลาญ BMR')
    body_age = models.IntegerField(verbose_name='อายุร่างกาย')
    
    # Metadata
    recorded_at = models.DateTimeField(default=datetime.now, verbose_name='วันที่บันทึก')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Health Record'
        verbose_name_plural = 'Health Records'
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.recorded_at.strftime('%Y-%m-%d')}"
    
    def get_bmi_status(self):
        """Get BMI status with exact Thai text"""
        bmi = float(self.bmi)
        if bmi < 18.5:
            return {
                'text': 'น้อยกว่าปกติ/ผอม',
                'risk': 'ภาวะเสี่ยงต่อโรค มากกว่าคนปกติ',
                'color': '#dc3545',  # Red
                'normal_range': '18.5 - 22.9'
            }
        elif 18.5 <= bmi <= 22.9:
            return {
                'text': 'ปกติ/สุขภาพดี',
                'risk': 'ภาวะเสี่ยงต่อโรค เท่ากับคนปกติ',
                'color': '#28a745',  # Green
                'normal_range': '18.5 - 22.9'
            }
        elif 23 <= bmi <= 24.9:
            return {
                'text': 'ท้วม/โรคอ้วนระดับ 1',
                'risk': 'ภาวะเสี่ยงต่อโรค อันตรายระดับ 1',
                'color': '#ffb6c1',  # Pink
                'normal_range': '18.5 - 22.9'
            }
        elif 25 <= bmi <= 30:
            return {
                'text': 'อ้วน/โรคอ้วนระดับ 2',
                'risk': 'ภาวะเสี่ยงต่อโรค อันตรายระดับ 2',
                'color': '#fd7e14',  # Orange
                'normal_range': '18.5 - 22.9'
            }
        else:  # > 30
            return {
                'text': 'อ้วนมาก/โรคอ้วนระดับ 3',
                'risk': 'ภาวะเสี่ยงต่อโรค อันตรายระดับ 3',
                'color': '#dc3545',  # Red
                'normal_range': '18.5 - 22.9'
            }

    
    def get_fat_percent_status(self):
        """Get fat percent status based on gender with exact conditions"""
        fat = float(self.fat_percent)
        gender = self.user.profile.gender
        
        if gender == 'female':
            if 5 <= fat <= 19.9:
                return {
                    'text': 'ต่ำ',
                    'color': '#28a745',  # Green
                    'normal_range': '20 - 29.9'
                }
            elif 20 <= fat <= 29.9:
                return {
                    'text': 'ปกติ',
                    'color': '#32ee32',  # Light green
                    'normal_range': '20 - 29.9'
                }
            elif 30 <= fat <= 34.5:
                return {
                    'text': 'เริ่มอ้วน',
                    'color': '#ffc107',  # Yellow
                    'normal_range': '20 - 29.9'
                }
            else:  # 35-50
                return {
                    'text': 'อ้วน',
                    'color': '#dc3545',  # Red
                    'normal_range': '20 - 29.9',
                    'advice': 'คุณมีไขมันในร่างกายมากเกินไป ควรรีบปรึกษาบุคลากรทางการแพทย์'
                }
        else:  # male
            if 5 <= fat <= 9.9:
                return {
                    'text': 'ต่ำ',
                    'color': '#28a745',  # Green
                    'normal_range': '10 - 19.9'
                }
            elif 10 <= fat <= 19.9:
                return {
                    'text': 'ปกติ',
                    'color': '#32ee32',  # Light green
                    'normal_range': '10 - 19.9'
                }
            elif 20 <= fat <= 24.9:
                return {
                    'text': 'เริ่มอ้วน',
                    'color': '#ffc107',  # Yellow
                    'normal_range': '10 - 19.9'
                }
            else:  # 25-50
                return {
                    'text': 'อ้วน',
                    'color': '#dc3545',  # Red
                    'normal_range': '10 - 19.9',
                    'advice': 'คุณมีไขมันในร่างกายมากเกินไป ควรรีบปรึกษาบุคลากรทางการแพทย์ด่วน'
                }
    
    def get_visceral_fat_status(self):
        """Get visceral fat status with exact conditions"""
        vf = float(self.visceral_fat)
        if 1 <= vf <= 9:
            return {
                'text': 'ปกติ',
                'color': '#28a745',  # Green
                'normal_range': '1 - 9'
            }
        elif 10 <= vf <= 14:
            return {
                'text': 'สูง',
                'color': '#fd7e14',  # Orange
                'normal_range': '1 - 9'
            }
        else:  # 15-30
            return {
                'text': 'สูงมาก',
                'color': '#dc3545',  # Red
                'normal_range': '1 - 9',
                'advice': 'คุณมีภาวะเสี่ยงอันตรายจากการมีไขมันช่องท้องมากผิดปกติ ควรรีบปรึกษาบุคลากรทางการแพทย์'
            }
    
    def get_muscle_percent_status(self):
        """Get muscle percent status based on age and gender with exact conditions"""
        muscle = float(self.muscle_percent)
        age = self.user.profile.age
        gender = self.user.profile.gender
        
        if gender == 'female':
            if 18 <= age <= 39:
                if muscle < 24.3:
                    return {
                        'text': 'ต่ำ',
                        'color': '#dc3545',  # Red
                        'normal_range': '24.3 - 30.3',
                        'advice': 'คุณมีมวลกล้ามเนื้อน้อยเกินไป ควรปรึกษาบุคลากรทางการแพทย์เพื่อปรับเปลี่ยนโภชนาการและการออกกำลังกายสร้างกล้ามเนื้อ'
                    }
                elif 24.3 <= muscle <= 30.3:
                    return {'text': 'ปกติ', 'color': "#32ee32", 'normal_range': '24.3 - 30.3'}
                elif 30.4 <= muscle <= 35.3:
                    return {'text': 'สูง', 'color': '#28a745', 'normal_range': '24.3 - 30.3'}
                else:  # >= 35.4
                    return {
                        'text': 'สูงมาก',
                        'color': '#006400',  # Dark green
                        'normal_range': '24.3 - 30.3',
                        'advice': 'คุณมีมวลกล้ามเนื้อในระดับนักกีฬา พยายามรักษาพฤติกรรมสุขภาพต่อไป'
                    }
            elif 40 <= age <= 59:
                if muscle < 24.1:
                    return {
                        'text': 'ต่ำ',
                        'color': '#dc3545',
                        'normal_range': '24.1 - 30.1',
                        'advice': 'คุณมีมวลกล้ามเนื้อน้อยเกินไป ควรปรึกษาบุคลากรทางการแพทย์เพื่อปรับเปลี่ยนโภชนาการและการออกกำลังกายสร้างกล้ามเนื้อ'
                    }
                elif 24.1 <= muscle <= 30.1:
                    return {'text': 'ปกติ', 'color': '#32ee32', 'normal_range': '24.1 - 30.1'}
                elif 30.2 <= muscle <= 35.1:
                    return {'text': 'สูง', 'color': '#28a745', 'normal_range': '24.1 - 30.1'}
                else:  # >= 35.2
                    return {
                        'text': 'สูงมาก',
                        'color': '#006400',
                        'normal_range': '24.1 - 30.1',
                        'advice': 'คุณมีมวลกล้ามเนื้อในระดับนักกีฬา พยายามรักษาพฤติกรรมสุขภาพต่อไป'
                    }
            else:  # 60-80
                if muscle < 23.9:
                    return {'text': 'ต่ำ', 'color': '#dc3545', 'normal_range': '23.9 - 29.9'}
                elif 23.9 <= muscle <= 29.9:
                    return {'text': 'ปกติ', 'color': '#32ee32', 'normal_range': '23.9 - 29.9'}
                elif 30 <= muscle <= 34.9:
                    return {'text': 'สูง', 'color': '#28a745', 'normal_range': '23.9 - 29.9'}
                else:  # >= 35
                    return {'text': 'สูงมาก', 'color': '#006400', 'normal_range': '23.9 - 29.9'}
        else:  # male
            if 18 <= age <= 39:
                if muscle < 33.3:
                    return {'text': 'ต่ำ', 'color': '#dc3545', 'normal_range': '33.3 - 39.3'}
                elif 33.3 <= muscle <= 39.3:
                    return {'text': 'ปกติ', 'color': '#32ee32', 'normal_range': '33.3 - 39.3'}
                elif 39.4 <= muscle <= 44:
                    return {'text': 'สูง', 'color': '#28a745', 'normal_range': '33.3 - 39.3'}
                else:  # >= 44.1
                    return {'text': 'สูงมาก', 'color': '#006400', 'normal_range': '33.3 - 39.3'}
            elif 40 <= age <= 59:
                if muscle < 33.1:
                    return {'text': 'ต่ำ', 'color': '#dc3545', 'normal_range': '33.1 - 39.1'}
                elif 33.1 <= muscle <= 39.1:
                    return {'text': 'ปกติ', 'color': '#32ee32', 'normal_range': '33.1 - 39.1'}
                elif 39.2 <= muscle <= 43.8:
                    return {'text': 'สูง', 'color': '#28a745', 'normal_range': '33.1 - 39.1'}
                else:  # >= 43.9
                    return {'text': 'สูงมาก', 'color': '#006400', 'normal_range': '33.1 - 39.1'}
            else:  # 60-80
                if muscle < 32.9:
                    return {'text': 'ต่ำ', 'color': '#dc3545', 'normal_range': '32.9 - 38.9'}
                elif 32.9 <= muscle <= 38.9:
                    return {'text': 'ปกติ', 'color': '#32ee32', 'normal_range': '32.9 - 38.9'}
                elif 39 <= muscle <= 43.6:
                    return {'text': 'สูง', 'color': '#28a745', 'normal_range': '32.9 - 38.9'}
                else:  # >= 43.7
                    return {'text': 'สูงมาก', 'color': '#006400', 'normal_range': '32.9 - 38.9'}

    
    def get_blood_pressure_status(self):
        """Get blood pressure status with exact conditions"""
        systolic = self.blood_pressure_systolic
        diastolic = self.blood_pressure_diastolic
        
        if systolic < 120 and diastolic < 80:
            return {
                'text': 'เหมาะสม',
                'color': '#006400',  # Dark green
                'normal_range': '<120/<80',
                'advice': 'ควบคุมอาหาร, มีกิจกรรมทางกาย และวัดความดันสม่ำเสมอ'
            }
        elif 120 <= systolic <= 129 and 80 <= diastolic <= 84:
            return {
                'text': 'ปกติ',
                'color': '#28a745',  # Green
                'normal_range': '<120/<80',
                'advice': 'ควบคุมอาหาร, มีกิจกรรมทางกาย และวัดความดันสม่ำเสมอ'
            }
        elif (130 <= systolic <= 139) or (85 <= diastolic <= 89):
            return {
                'text': 'สูงกว่าปกติ',
                'color': '#ffc107',  # Yellow
                'normal_range': '<120/<80',
                'advice': 'ลดน้ำหนักหากมีน้ำหนักเกิน, หลีกเลี่ยงความเครียด บุหรี่, มีกิจกรรมทางกายอย่างสม่ำเสมอ, ลดการกินเค็ม, ปรึกษาบุคลากรทางการแพทย์'
            }
        elif (140 <= systolic <= 159) or (90 <= diastolic <= 99):
            return {
                'text': 'ระดับ 1',
                'color': '#fd7e14',  # Orange
                'normal_range': '<120/<80',
                'advice': 'ควรรีบปรึกษาแพทย์เพื่อรับการวินิจฉัยและรับการรักษาที่เหมาะสม รวมถึงเข้าสู่กระบวนการปรับเปลี่ยนพฤติกรรม'
            }
        elif (160 <= systolic <= 179) or (100 <= diastolic <= 109):
            return {
                'text': 'ระดับ 2',
                'color': '#dc3545',  # Red
                'normal_range': '<120/<80',
                'advice': 'ควรรีบปรึกษาแพทย์เพื่อรับการวินิจฉัยและรับการรักษาที่เหมาะสม รวมถึงเข้าสู่กระบวนการปรับเปลี่ยนพฤติกรรม'
            }
        elif systolic >= 180 or diastolic >= 110:
            return {
                'text': 'ระดับ 3',
                'color': '#8b0000',  # Dark red
                'normal_range': '<120/<80',
                'advice': 'ควรรีบพบแพทย์ทันที'
            }
        elif systolic >= 140 and diastolic < 90:
            return {
                'text': 'สูงเฉพาะตัวบน',
                'color': '#ffb6c1',  # Pink
                'normal_range': '<120/<80',
                'advice': 'ควรปรึกษาบุคลากรทางการแพทย์'
            }
        elif systolic < 140 and diastolic >= 90:
            return {
                'text': 'สูงเฉพาะตัวล่าง',
                'color': '#ff1493',  # Dark pink
                'normal_range': '<120/<80',
                'advice': 'ควรปรึกษาบุคลากรทางการแพทย์'
            }
        else:
            return {
                'text': 'ปกติ',
                'color': '#28a745',
                'normal_range': '<120/<80'
            }
    
    def get_cholesterol_status(self):
        """Get cholesterol status"""
        if not self.cholesterol:
            return None
        
        chol = float(self.cholesterol)
        if chol < 200:
            return {
                'text': 'ปกติ',
                'color': '#28a745',  # Green
                'normal_range': '<200',
                'full_text': 'ปริมาณไขมันคอเลสเตอรอลอยู่ในระดับปกติ'
            }
        else:  # chol > 200
            return {
                'text': 'มากผิดปกติ',
                'color': '#fd7e14',  # Orange
                'normal_range': '<200',
                'full_text': 'ปริมาณไขมันคอเลสเตอรอลอยู่ในระดับมากผิดปกติ'
            }
    
    def get_ldl_status(self):
        """Get LDL status"""
        if not self.ldl:
            return None
        
        ldl_val = float(self.ldl)
        if ldl_val < 130:
            return {
                'text': 'ปกติ',
                'color': '#28a745',  # Green
                'normal_range': '<130',
                'full_text': 'ไขมันไม่ดีอยู่ในระดับปกติ'
            }
        else:  # ldl > 130
            return {
                'text': 'มากผิดปกติ',
                'color': '#fd7e14',  # Orange
                'normal_range': '<130',
                'full_text': 'ปริมาณไขมันไม่ดีอยู่ในระดับมากผิดปกติ'
            }
    
    def get_hdl_status(self):
        """Get HDL status based on gender"""
        if not self.hdl:
            return None
        
        hdl_val = float(self.hdl)
        gender = self.user.profile.gender
        
        if gender == 'male':
            if hdl_val > 40:
                return {
                    'text': 'ปกติ',
                    'color': '#28a745',  # Green
                    'normal_range': '>40 (ชาย)',
                    'full_text': 'ปริมาณไขมันดีอยู่ในระดับปกติ'
                }
            else:  # hdl <= 40
                return {
                    'text': 'ต่ำกว่าปกติ',
                    'color': '#fd7e14',  # Orange
                    'normal_range': '>40 (ชาย)',
                    'full_text': 'ปริมาณไขมันดีอยู่ในระดับต่ำกว่าปกติ'
                }
        else:  # female
            if hdl_val > 50:
                return {
                    'text': 'ปกติ',
                    'color': '#28a745',  # Green
                    'normal_range': '>50 (หญิง)',
                    'full_text': 'ปริมาณไขมันดีอยู่ในระดับปกติ'
                }
            else:  # hdl <= 50
                return {
                    'text': 'ต่ำกว่าปกติ',
                    'color': '#fd7e14',  # Orange
                    'normal_range': '>50 (หญิง)',
                    'full_text': 'ปริมาณไขมันดีอยู่ในระดับต่ำกว่าปกติ'
                }
    
    def get_fbs_status(self):
        """Get FBS (Fasting Blood Sugar) status"""
        if not self.fbs:
            return None
        
        fbs_val = float(self.fbs)
        if fbs_val < 100:
            return {
                'text': 'ปกติ',
                'color': '#28a745',  # Green
                'normal_range': '<100',
                'full_text': 'ระดับน้ำตาลอยู่ในเกณฑ์ปกติ'
            }
        elif 100 <= fbs_val <= 125:
            return {
                'text': 'ก่อนเบาหวาน',
                'color': '#fd7e14',  # Orange
                'normal_range': '<100',
                'full_text': 'ระดับน้ำตาลในเลือดเสี่ยงเป็นโรคเบาหวานหรือมีภาวะก่อนเบาหวาน'
            }
        else:  # fbs >= 126
            return {
                'text': 'เบาหวาน',
                'color': '#dc3545',  # Red
                'normal_range': '<100',
                'full_text': 'ระดับน้ำตาลในเลือดอยู่ในเกณฑ์โรคเบาหวาน'
            }
        
    def get_triglycerides_status(self):
        """Get Triglycerides status"""
        if not self.triglycerides:
            return None
        
        tg_val = float(self.triglycerides)
        if tg_val < 150:
            return {
                'text': 'ปกติ',
                'color': '#28a745',  # Green
                'normal_range': '<150',
                'full_text': 'ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์ปกติ'
            }
        elif 150 <= tg_val <= 199:
            return {
                'text': 'สูงเล็กน้อย',
                'color': '#ffc107',  # Yellow
                'normal_range': '<150',
                'full_text': 'ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์สูงเล็กน้อย'
            }
        elif 200 <= tg_val <= 499:
            return {
                'text': 'สูง',
                'color': '#fd7e14',  # Orange
                'normal_range': '<150',
                'full_text': 'ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์สูง'
            }
        else:  # tg_val >= 500
            return {
                'text': 'สูงมาก',
                'color': '#dc3545',  # Red
                'normal_range': '<150',
                'full_text': 'ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์สูงมาก'
            }
    
    def get_waist_status(self):
        """Get waist circumference status based on height calculation"""
        waist_val = float(self.waist)
        height_val = float(self.height)
        waist_threshold = height_val / 2
        
        # Allow small tolerance for "equal"
        if abs(waist_val - waist_threshold) < 1:
            return {
                'text': 'ปกติ',
                'color': '#28a745',  # Green
                'normal_range': f'≈{waist_threshold:.1f} cm',
                'full_text': 'เส้นรอบเอวของคุณอยู่ในเกณฑ์ปกติ'
            }
        elif waist_val > waist_threshold:
            return {
                'text': 'เกินเกณฑ์',
                'color': '#fd7e14',  # Orange
                'normal_range': f'≈{waist_threshold:.1f} cm',
                'full_text': 'เส้นรอบเอวของคุณเกินเกณฑ์'
            }
        else:  # waist < waist_threshold
            return {
                'text': 'ดีมาก',
                'color': '#006400',  # Dark green
                'normal_range': f'≈{waist_threshold:.1f} cm',
                'full_text': 'รอบเอวของคุณอยู่ในเกณฑ์ดีมาก'
            }
