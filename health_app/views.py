"""
Health App views with graphs, comparisons, and health summaries
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from .models import HealthRecord
from .forms import HealthRecordForm, DateRangeFilterForm
from accounts.models import UserActivity


def log_health_activity(user, action, description='', request=None):
    """Log health-related activity"""
    activity = UserActivity.objects.create(
        user=user,
        action=action,
        description=description
    )
    if request:
        activity.ip_address = request.META.get('REMOTE_ADDR', '')
        activity.user_agent = request.META.get('HTTP_USER_AGENT', '')
        activity.save()


@login_required
def dashboard_view(request):
    """Main dashboard with health overview"""
    user = request.user
    profile = user.profile
    
    # Check if MFA is required but not setup
    if profile.requires_mfa() and not profile.mfa_enabled:
        messages.error(request, '⚠️ คุณต้องตั้งค่า MFA ก่อนใช้งานระบบ')
        return redirect('accounts:mfa_setup')
    
    # Check if profile is complete
    if not profile.firstname or not profile.lastname or not profile.birthdate:
        messages.warning(request, 'กรุณาเพิ่มข้อมูลโปรไฟล์ให้ครบถ้วนก่อนใช้งาน')
        return redirect('accounts:profile')
    
    # Get latest record
    latest_record = HealthRecord.objects.filter(user=user).first()
    
    if not latest_record:
        messages.info(request, 'กรุณาเพิ่มข้อมูลสุขภาพของคุณ')
        return redirect('health_app:add_metric')
    
    # Get status for all metrics
    bmi_status = latest_record.get_bmi_status()
    fat_status = latest_record.get_fat_percent_status()
    visceral_status = latest_record.get_visceral_fat_status()
    muscle_status = latest_record.get_muscle_percent_status()
    blood_pressure_status = latest_record.get_blood_pressure_status()
    waist_status = latest_record.get_waist_status()
    cholesterol_status = latest_record.get_cholesterol_status()
    ldl_status = latest_record.get_ldl_status()
    hdl_status = latest_record.get_hdl_status()
    fbs_status = latest_record.get_fbs_status()
    triglycerides_status = latest_record.get_triglycerides_status()
    
    # Generate health overview recommendations
    health_overview = generate_health_overview(latest_record, profile, bmi_status, fat_status, visceral_status, muscle_status)
    
    context = {
        'profile': profile,
        'latest_record': latest_record,
        'bmi_status': bmi_status,
        'fat_status': fat_status,
        'visceral_status': visceral_status,
        'muscle_status': muscle_status,
        'blood_pressure_status': blood_pressure_status,
        'waist_status': waist_status,
        'cholesterol_status': cholesterol_status,
        'ldl_status': ldl_status,
        'hdl_status': hdl_status,
        'fbs_status': fbs_status,
        'triglycerides_status': triglycerides_status,
        'health_overview': health_overview,
    }
    
    return render(request, 'health_app/dashboard_n.html', context)


def generate_health_overview(record, profile, bmi_status, fat_status, visceral_status, muscle_status):

    def create_item(text, color='info', severity='normal'):
        """Create overview item with color"""
        return {
            'text': text,
            'color': color,      # Bootstrap alert class
            'severity': severity
        }
    
    """Generate comprehensive health overview with recommendations"""
    overview = []
    
    # Blood Pressure Recommendations (with detailed conditions and advice)
    systolic = record.blood_pressure_systolic
    diastolic = record.blood_pressure_diastolic
    
    if systolic < 120 and diastolic < 80:
        overview.append(create_item('คุณมีความดันโลหิตในระดับเหมาะสม', 'success'))
        overview.append(create_item('คำแนะนำ: ควบคุมอาหาร, มีกิจกรรมทางกาย และวัดความดันสม่ำเสมอ', 'success'))
    elif 120 <= systolic <= 129 and 80 <= diastolic <= 84:
        overview.append(create_item('คุณมีความดันโลหิตในระดับปกติ', 'success'))
        overview.append(create_item('คำแนะนำ: ควบคุมอาหาร, มีกิจกรรมทางกาย และวัดความดันสม่ำเสมอ', 'success'))
    elif (130 <= systolic <= 139) or (85 <= diastolic <= 89):
        overview.append(create_item('คุณมีความดันโลหิตสูงกว่าปกติ', 'warning'))
        overview.append(create_item('คำแนะนำ: ลดน้ำหนักหากมีน้ำหนักเกิน, หลีกเลี่ยงความเครียด บุหรี่, มีกิจกรรมทางกายอย่างสม่ำเสมอ, ลดการกินเค็ม', 'warning'))
    elif (140 <= systolic <= 159) or (90 <= diastolic <= 99):
        overview.append(create_item('คุณอาจเป็นโรคความดันโลหิตสูงระดับที่ 1', 'warning'))
        overview.append(create_item('คำแนะนำ: ควรรีบปรึกษาแพทย์เพื่อรับการวินิจฉัยและรับการรักษาที่เหมาะสม รวมถึงเข้าสู่กระบวนการปรับเปลี่ยนพฤติกรรม', 'warning'))
    elif (160 <= systolic <= 179) or (100 <= diastolic <= 109):
        overview.append(create_item('คุณอาจเป็นโรคความดันโลหิตสูงระดับที่ 2', 'warning'))
        overview.append(create_item('คำแนะนำ: ควรรีบปรึกษาแพทย์เพื่อรับการวินิจฉัยและรับการรักษาที่เหมาะสม รวมถึงเข้าสู่กระบวนการปรับเปลี่ยนพฤติกรรม', 'warning'))
    elif systolic >= 180 or diastolic >= 110:
        overview.append(create_item('คุณอาจเป็นโรคความดันโลหิตสูงระดับที่ 3', 'danger'))
        overview.append(create_item('คำแนะนำ: ควรรีบพบแพทย์ทันที', 'danger'))
    elif systolic >= 140 and diastolic < 90:
        overview.append(create_item('คุณอาจเป็นโรคความดันโลหิตสูงเฉพาะตัวบน', 'danger'))
        overview.append(create_item('คำแนะนำ: ควรปรึกษาบุคลากรทางการแพทย์', 'danger'))
    elif systolic < 140 and diastolic >= 90:
        overview.append(create_item('คุณอาจเป็นโรคความดันโลหิตสูงเฉพาะตัวล่าง', 'danger'))
        overview.append(create_item('คำแนะนำ: ควรปรึกษาบุคลากรทางการแพทย์', 'danger'))
    
    # Waist Circumference (calculated from height)
    waist = float(record.waist)
    height = float(record.height)
    waist_threshold = height / 2
    
    if abs(waist - waist_threshold) < 1:  # Approximately equal
        overview.append(create_item('เส้นรอบเอวของคุณอยู่ในเกณฑ์ปกติ', 'success'))
    elif waist > waist_threshold:
        overview.append(create_item('เส้นรอบเอวของคุณเกินเกณฑ์', 'danger'))
    else:  # waist < waist_threshold
        overview.append(create_item('รอบเอวของคุณอยู่ในเกณฑ์ดีมาก', 'success'))
    
    # BMI Recommendations (following exact conditions)
    bmi = float(record.bmi)
    
    if bmi < 18.5:
        overview.append(create_item('น้อยกว่าปกติ/ผอม - ภาวะเสี่ยงต่อโรค มากกว่าคนปกติ', 'warning'))
    elif 18.5 <= bmi <= 22.9:
        overview.append(create_item('ปกติ/สุขภาพดี - ภาวะเสี่ยงต่อโรค เท่ากับคนปกติ', 'success'))
    elif 23 <= bmi <= 24.9:
        overview.append(create_item('ท้วม มีภาวะน้ำหนักเกินหรือโรคอ้วนระดับ 1 แนะนำให้ดูมวลกล้ามเนื้อประกอบด้วย - ภาวะเสี่ยงต่อโรค อันตรายระดับ 1 ', 'warning'))
    elif 25 <= bmi <= 30:
        overview.append(create_item('อ้วน มีภาวะน้ำหนักเกินหรือโรคอ้วนระดับ 2 - ภาวะเสี่ยงต่อโรค อันตรายระดับ 2 ', 'warning'))
    else:  # bmi > 30
        overview.append(create_item('อ้วนมาก มีภาวะน้ำหนักเกินมากอย่างมากหรือโรคอ้วนระดับ 3 - ภาวะเสี่ยงต่อโรค อันตรายระดับ 3', 'danger'))
    
    # Fat Percent Recommendations (gender-based)
    fat = float(record.fat_percent)
    gender = profile.gender
    
    if gender == 'female':
        if 5 <= fat <= 19.9:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: ต่ำ', 'success'))
        elif 20 <= fat <= 29.9:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: ปกติ', 'success'))
        elif 30 <= fat <= 34.5:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: เริ่มอ้วน ', 'warning'))
        elif 35 <= fat <= 50:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: อ้วน - คุณมีไขมันในร่างกายมากเกินไป ', 'danger'))
    else:  # male
        if 5 <= fat <= 9.9:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: ต่ำ', 'success'))
        elif 10 <= fat <= 19.9:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: ปกติ', 'success'))
        elif 20 <= fat <= 24.9:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: เริ่มอ้วน ', 'warning'))
        elif 25 <= fat <= 50:
            overview.append(create_item('เปอร์เซ็นต์ไขมัน: อ้วน - คุณมีไขมันในร่างกายมากเกินไป ', 'danger'))
    # Visceral Fat Recommendations
    vf = float(record.visceral_fat)
    
    if 1 <= vf <= 9:
        overview.append(create_item('ไขมันในช่องท้อง: ปกติ', 'success'))
    elif 10 <= vf <= 14:
        overview.append(create_item('ไขมันในช่องท้อง: สูง - คุณมีภาวะเสี่ยงจากการมีไขมันช่องท้องสูง', 'warning'))
    elif 15 <= vf <= 30:
        overview.append(create_item('ไขมันในช่องท้อง: สูงมาก - คุณมีภาวะเสี่ยงอันตรายจากการมีไขมันช่องท้องมากผิดปกติ', 'danger'))
    
    # Muscle Percent Recommendations (age and gender-based)
    muscle = float(record.muscle_percent)
    age = profile.get_age_years()
    
    if gender == 'female':
        if 18 <= age <= 39:
            if muscle < 24.3:
                overview.append(create_item('มวลกล้ามเนื้อ: ต่ำ - คุณมีมวลกล้ามเนื้อน้อยเกินไป สร้างกล้ามเนื้อโดยเน้น เพิ่มโปรตีนคุณภาพ นอนหลับคุณภาพ ออกกำลังกายแบบบอดี้เวท หรือเวทเทรนนิ่ง', 'warning'))
            elif 24.3 <= muscle <= 30.3:
                overview.append(create_item('มวลกล้ามเนื้อ: ปกติ', 'success'))
            elif 30.4 <= muscle <= 35.3:
                overview.append(create_item('มวลกล้ามเนื้อ: สูง ร่างกายแข็งแรง', 'success'))
            elif muscle >= 35.4:
                overview.append(create_item('มวลกล้ามเนื้อ: สูงมาก - คุณมีมวลกล้ามเนื้อในระดับนักกีฬา ร่างกายแข็งแรง พยายามรักษาพฤติกรรมสุขภาพต่อไป', 'success','success'))
        elif 40 <= age <= 59:
            if muscle < 24.1:
                overview.append(create_item('มวลกล้ามเนื้อ: ต่ำ - คุณมีมวลกล้ามเนื้อน้อยเกินไป สร้างกล้ามเนื้อโดยเน้น เพิ่มโปรตีนคุณภาพ นอนหลับคุณภาพ ออกกำลังกายแบบบอดี้เวท หรือเวทเทรนนิ่ง', 'warning'))
            elif 24.1 <= muscle <= 30.1:
                overview.append(create_item('มวลกล้ามเนื้อ: ปกติ', 'success'))
            elif 30.2 <= muscle <= 35.1:
                overview.append(create_item('มวลกล้ามเนื้อ: สูง ร่างกายแข็งแรง', 'success'))
            elif muscle >= 35.2:
                overview.append(create_item('มวลกล้ามเนื้อ: สูงมาก - คุณมีมวลกล้ามเนื้อในระดับนักกีฬา ร่างกายแข็งแรง พยายามรักษาพฤติกรรมสุขภาพต่อไป', 'success','success'))
        elif 60 <= age <= 80:
            if muscle < 23.9:
                overview.append(create_item('มวลกล้ามเนื้อ: ต่ำ - คุณมีมวลกล้ามเนื้อน้อยเกินไป สร้างกล้ามเนื้อโดยเน้น เพิ่มโปรตีนคุณภาพ นอนหลับคุณภาพ ออกกำลังกายแบบบอดี้เวท หรือเวทเทรนนิ่ง', 'warning'))
            elif 23.9 <= muscle <= 29.9:
                overview.append(create_item('มวลกล้ามเนื้อ: ปกติ', 'success'))
            elif 30 <= muscle <= 34.9:
                overview.append(create_item('มวลกล้ามเนื้อ: สูง ร่างกายแข็งแรง', 'success'))
            elif muscle >= 35:
                overview.append(create_item('มวลกล้ามเนื้อ: สูงมาก - คุณมีมวลกล้ามเนื้อในระดับนักกีฬา ร่างกายแข็งแรง พยายามรักษาพฤติกรรมสุขภาพต่อไป', 'success','success'))
    else:  # male
        if 18 <= age <= 39:
            if muscle < 33.3:
                overview.append(create_item('มวลกล้ามเนื้อ: ต่ำ - คุณมีมวลกล้ามเนื้อน้อยเกินไป สร้างกล้ามเนื้อโดยเน้น เพิ่มโปรตีนคุณภาพ นอนหลับคุณภาพ ออกกำลังกายแบบบอดี้เวท หรือเวทเทรนนิ่ง', 'warning'))
            elif 33.3 <= muscle <= 39.3:
                overview.append(create_item('มวลกล้ามเนื้อ: ปกติ', 'success'))
            elif 39.4 <= muscle <= 44:
                overview.append(create_item('มวลกล้ามเนื้อ: สูง ร่างกายแข็งแรง', 'success'))
            elif muscle >= 44.1:
                overview.append(create_item('มวลกล้ามเนื้อ: สูงมาก - คุณมีมวลกล้ามเนื้อในระดับนักกีฬา ร่างกายแข็งแรง พยายามรักษาพฤติกรรมสุขภาพต่อไป', 'success','success'))
        elif 40 <= age <= 59:
            if muscle < 33.1:
                overview.append(create_item('มวลกล้ามเนื้อ: ต่ำ - คุณมีมวลกล้ามเนื้อน้อยเกินไป สร้างกล้ามเนื้อโดยเน้น เพิ่มโปรตีนคุณภาพ นอนหลับคุณภาพ ออกกำลังกายแบบบอดี้เวท หรือเวทเทรนนิ่ง', 'warning'))
            elif 33.1 <= muscle <= 39.1:
                overview.append(create_item('มวลกล้ามเนื้อ: ปกติ', 'success'))
            elif 39.2 <= muscle <= 43.8:
                overview.append(create_item('มวลกล้ามเนื้อ: สูง ร่างกายแข็งแรง', 'success'))
            elif muscle >= 43.9:
                overview.append(create_item('มวลกล้ามเนื้อ: สูงมาก - คุณมีมวลกล้ามเนื้อในระดับนักกีฬา ร่างกายแข็งแรง พยายามรักษาพฤติกรรมสุขภาพต่อไป', 'success','success'))
        elif 60 <= age <= 80:
            if muscle < 32.9:
                overview.append(create_item('มวลกล้ามเนื้อ: ต่ำ - คุณมีมวลกล้ามเนื้อน้อยเกินไป สร้างกล้ามเนื้อโดยเน้น เพิ่มโปรตีนคุณภาพ นอนหลับคุณภาพ ออกกำลังกายแบบบอดี้เวท หรือเวทเทรนนิ่ง', 'warning'))
            elif 32.9 <= muscle <= 38.9:
                overview.append(create_item('มวลกล้ามเนื้อ: ปกติ', 'success'))
            elif 39 <= muscle <= 43.6:
                overview.append(create_item('มวลกล้ามเนื้อ: สูง ร่างกายแข็งแรง', 'success'))
            elif muscle >= 43.7:
                overview.append(create_item('มวลกล้ามเนื้อ: สูงมาก - คุณมีมวลกล้ามเนื้อในระดับนักกีฬา ร่างกายแข็งแรง พยายามรักษาพฤติกรรมสุขภาพต่อไป', 'success','success'))
    
    # Cholesterol (if available)
    if record.cholesterol:
        chol = float(record.cholesterol)
        if chol < 200:
            overview.append(create_item('ปริมาณไขมันคอเลสเตอรอลอยู่ในระดับปกติ', 'success'))
        else:  # chol > 200
            overview.append(create_item('ปริมาณไขมันคอเลสเตอรอลอยู่ในระดับมากผิดปกติ', 'warning'))
    
    # LDL (if available)
    if record.ldl:
        ldl = float(record.ldl)
        if ldl < 130:
            overview.append(create_item('ไขมันไม่ดีอยู่ในระดับปกติ', 'success'))
        else:  # ldl > 130
            overview.append(create_item('ปริมาณไขมันไม่ดีอยู่ในระดับมากผิดปกติ', 'warning'))
    
    # HDL (if available)
    if record.hdl:
        hdl = float(record.hdl)
        if gender == 'male':
            if hdl > 40:
                overview.append(create_item('ปริมาณไขมันดีอยู่ในระดับปกติ', 'success'))
            else:  # hdl < 40
                overview.append(create_item('ปริมาณไขมันดีอยู่ในระดับต่ำกว่าปกติ ', 'warning'))
        else:  # female
            if hdl > 50:
                overview.append(create_item('ปริมาณไขมันดีอยู่ในระดับปกติ', 'success'))
            else:  # hdl < 50
                overview.append(create_item('ปริมาณไขมันดีอยู่ในระดับต่ำกว่าปกติ ', 'warning'))
    
    # FBS (if available)
    if record.fbs:
        fbs = float(record.fbs)
        if fbs < 100:
            overview.append(create_item('ระดับน้ำตาลอยู่ในเกณฑ์ปกติ', 'success'))
        elif 100 <= fbs <= 125:
            overview.append(create_item('ระดับน้ำตาลในเลือดเสี่ยงเป็นโรคเบาหวานหรือมีภาวะก่อนเบาหวาน', 'warning'))
        else:  # fbs >= 126
            overview.append(create_item('ระดับน้ำตาลในเลือดอยู่ในเกณฑ์โรคเบาหวาน', 'danger'))
    # Triglycerides (if available)
    if record.triglycerides:
        tg = float(record.triglycerides)
        if tg < 150:
            overview.append(create_item('ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์ปกติ', 'success'))
        elif 150 <= tg <= 199:
            overview.append(create_item('ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์สูงเล็กน้อย ลดอาหารที่มีน้ำตาลและไขมันทรานส์ กินอาหารคาร์บคุณภาพ งด/ลดอาหารแปรรูปขั้นสูง งดเครื่องดื่มแอลกอฮอล์ และทำ IF กินและอดอาหารเป็นช่วงๆ', 'warning'))
        elif 200 <= tg <= 499:
            overview.append(create_item('ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์สูง ลดอาหารที่มีน้ำตาลและไขมันทรานส์ กินอาหารคาร์บคุณภาพ งด/ลดอาหารแปรรูปขั้นสูง งดเครื่องดื่มแอลกอฮอล์ และทำ IF กินและอดอาหารเป็นช่วงๆ ', 'warning'))
        else:  # tg >= 500
            overview.append(create_item('ระดับไตรกลีเซอไรด์อยู่ในเกณฑ์สูงมาก ซึ่งอาจเพิ่มความเสี่ยงต่อการเกิดตับอ่อนอักเสบ ควรรีบปรึกษาบุคลากรทางการแพทย์ทันที', 'danger'))

    return overview



@login_required
def add_metric_view(request):
    """Add new health metric"""
    profile = request.user.profile

    # Check if profile is complete
    if not profile.firstname or not profile.lastname or not profile.birthdate:
        messages.warning(request, 'กรุณาเพิ่มข้อมูลโปรไฟล์ให้ครบถ้วนก่อนเพิ่มข้อมูลสุขภาพ')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            log_health_activity(request.user, 'health_record_add', f'Added health record for {record.recorded_at}', request)
            messages.success(request, 'เพิ่มข้อมูลสุขภาพสำเร็จ!')
            return redirect('health_app:dashboard')
    else:
        form = HealthRecordForm()
    
    context = {
        'form': form,
        'profile': profile,
    }
    
    return render(request, 'health_app/add_metric.html', context)


@login_required
def update_record_view(request, record_id):
    """Update existing health record"""
    record = get_object_or_404(HealthRecord, id=record_id, user=request.user)
    
    if request.method == 'POST':
        form = HealthRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            log_health_activity(request.user, 'health_record_update', f'Updated health record for {record.recorded_at}', request)
            messages.success(request, 'อัปเดตข้อมูลสำเร็จ!')
            return redirect('health_app:history')
    else:
        form = HealthRecordForm(instance=record)
    
    return render(request, 'health_app/update_record.html', {'form': form, 'record': record})


@login_required
def history_view(request):
    """History view with graphs and comparison tables"""
    user = request.user
    
    # Get all records
    records = HealthRecord.objects.filter(user=user).order_by('recorded_at')
    
    if not records.exists():
        messages.info(request, 'ไม่มีข้อมูลประวัติ')
        return redirect('health_app:add_metric')
    
    # Get filter parameters
    metric_filter = request.GET.get('metric', 'bmi')  # Default to BMI
    date_start_str = request.GET.get('date_start', '')
    date_end_str = request.GET.get('date_end', '')
    
    # Apply date filters
    filtered_records = records
    if date_start_str:
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d').date()
        filtered_records = filtered_records.filter(recorded_at__date__gte=date_start)
    if date_end_str:
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d').date()
        filtered_records = filtered_records.filter(recorded_at__date__lte=date_end)
    
    # Get first and last dates for defaults
    first_record = records.first()
    last_record = records.last()
    
    # Generate graph
    graph_base64 = generate_metric_graph(filtered_records, metric_filter, user.profile)
    
    # Generate comparison table
    comparison_data = None
    summary_info = None
    if filtered_records.count() >= 2:
        first_filtered = filtered_records.first()
        last_filtered = filtered_records.last()
        comparison_data = generate_comparison_table(first_filtered, last_filtered, user.profile)
        summary_info = generate_summary_info(first_filtered, last_filtered, user.profile)
    
    context = {
        'records': records,
        'graph_base64': graph_base64,
        'metric_filter': metric_filter,
        'date_start': date_start_str or (first_record.recorded_at.strftime('%Y-%m-%d') if first_record else ''),
        'date_end': date_end_str or (last_record.recorded_at.strftime('%Y-%m-%d') if last_record else ''),
        'first_record': first_record,
        'last_record': last_record,
        'comparison_data': comparison_data,
        'summary_info': summary_info,
    }
    
    return render(request, 'health_app/history.html', context)


def generate_metric_graph(records, metric_name, profile):
    """Generate line graph for specific metric"""
    if not records.exists():
        return None
    
    plt.figure(figsize=(12, 6))
    plt.rcParams['font.family'] = 'DejaVu Sans'
    
    dates = [r.recorded_at for r in records]
    
    # Metric configuration
    metric_config = {
        'bmi': {
            'values': [float(r.bmi) for r in records],
            'title': 'BMI',
            'ylabel': 'BMI',
            'normal_range': (18.5, 22.9),
        },
        'fat_percent': {
            'values': [float(r.fat_percent) for r in records],
            'title': 'Fat Percent',
            'ylabel': 'Fat Percent (%)',
            'normal_range': get_fat_normal_range(profile),
        },
        'visceral_fat': {
            'values': [float(r.visceral_fat) for r in records],
            'title': 'Visceral Fat',
            'ylabel': 'Visceral Fat',
            'normal_range': (1, 9),
        },
        'muscle_percent': {
            'values': [float(r.muscle_percent) for r in records],
            'title': 'Muscle Percent',
            'ylabel': 'Muscle Percent (%)',
            'normal_range': get_muscle_normal_range(profile),
        },
        'blood_pressure_systolic': {
            'values': [float(r.blood_pressure_systolic) for r in records],
            'title': 'Blood Pressure Systolic',
            'ylabel': 'Systolic (mmHg)',
            'normal_range': (90, 120),
        },
        'blood_pressure_diastolic': {
            'values': [float(r.blood_pressure_diastolic) for r in records],
            'title': 'Blood Pressure Diastolic',
            'ylabel': 'Diastolic (mmHg)',
            'normal_range': (60, 80),
        },
        'waist': {
            'values': [float(r.waist) for r in records],
            'title': 'Waist Circumference',
            'ylabel': 'Waist (cm)',
            'normal_range': (60, 90 if profile.gender == 'male' else 80),
        },
        'cholesterol': {
            'values': [float(r.cholesterol) for r in records if r.cholesterol],
            'title': 'Cholesterol',
            'ylabel': 'Cholesterol (mg/dL)',
            'normal_range': (0, 200),
        },
        'ldl': {
            'values': [float(r.ldl) for r in records if r.ldl],
            'title': 'LDL',
            'ylabel': 'LDL (mg/dL)',
            'normal_range': (0, 100),
        },
        'hdl': {
            'values': [float(r.hdl) for r in records if r.hdl],
            'title': 'HDL',
            'ylabel': 'HDL (mg/dL)',
            'normal_range': (40, 100),
        },
        'fbs': {
            'values': [float(r.fbs) for r in records if r.fbs],
            'title': 'FBS (Fasting Blood Sugar)',
            'ylabel': 'FBS (mg/dL)',
            'normal_range': (70, 100),
        },
        'triglycerides': {
            'values': [float(r.triglycerides) for r in records if r.triglycerides],
            'title': 'Triglycerides',
            'ylabel': 'Triglycerides (mg/dL)',
            'normal_range': (0, 150),
        },
    }
    
    config = metric_config.get(metric_name, metric_config['bmi'])
    values = config['values']
    normal_range = config['normal_range']
    
    # Plot values
    plt.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=8, label='Your Values')
    
    # Plot normal range as green horizontal lines
    if normal_range:
        plt.axhline(y=normal_range[0], color='green', linestyle='--', linewidth=2, alpha=0.7, label=f'Normal Range ({normal_range[0]}-{normal_range[1]})')
        plt.axhline(y=normal_range[1], color='green', linestyle='--', linewidth=2, alpha=0.7)
        plt.fill_between(dates, normal_range[0], normal_range[1], color='green', alpha=0.1)
    
    plt.title(config['title'], fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel(config['ylabel'], fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64


def get_fat_normal_range(profile):
    """Get normal fat percent range based on gender"""
    if profile.gender == 'female':
        return (20, 29.9)
    else:
        return (10, 19.9)


def get_muscle_normal_range(profile):
    """Get normal muscle percent range based on age and gender"""
    age = profile.get_age_years()
    gender = profile.gender
    
    if gender == 'female':
        if 18 <= age <= 39:
            return (24.3, 30.3)
        elif 40 <= age <= 59:
            return (24.1, 30.1)
        else:  # 60-80
            return (23.9, 29.9)
    else:  # male
        if 18 <= age <= 39:
            return (33.3, 39.3)
        elif 40 <= age <= 59:
            return (33.1, 39.1)
        else:  # 60-80
            return (32.9, 38.9)
        
def get_triglycerides_status(value):
    """Get triglycerides status"""
    if value is None:
        return None, None
    if value < 150:
        return 'ปกติ', '#28a745'
    elif 150 <= value < 200:
        return 'สูงกว่าปกติ', '#ffc107'
    elif 200 <= value < 500:
        return 'สูง', '#fd7e14'
    else:
        return 'สูงมาก', '#dc3545'


def generate_comparison_table(first_record, last_record, profile):
    """Generate comparison table between two records"""
    comparison = {}
    
    # BMI comparison
    bmi_diff = float(last_record.bmi) - float(first_record.bmi)
    bmi_text = get_comparison_text(bmi_diff)
    bmi_status = last_record.get_bmi_status()
    comparison['bmi'] = {
        'start_value': float(first_record.bmi),
        'end_value': float(last_record.bmi),
        'diff': bmi_diff,
        'text': bmi_text,
        'color': bmi_status['color'],
        'normal_range': bmi_status['normal_range'],
    }
    
    # Fat percent comparison
    fat_diff = float(last_record.fat_percent) - float(first_record.fat_percent)
    fat_text = get_comparison_text(fat_diff)
    fat_status = last_record.get_fat_percent_status()
    comparison['fat_percent'] = {
        'start_value': float(first_record.fat_percent),
        'end_value': float(last_record.fat_percent),
        'diff': fat_diff,
        'text': fat_text,
        'color': fat_status['color'],
        'normal_range': fat_status['normal_range'],
    }
    
    # Visceral fat comparison
    vf_diff = float(last_record.visceral_fat) - float(first_record.visceral_fat)
    vf_text = get_comparison_text(vf_diff)
    vf_status = last_record.get_visceral_fat_status()
    comparison['visceral_fat'] = {
        'start_value': float(first_record.visceral_fat),
        'end_value': float(last_record.visceral_fat),
        'diff': vf_diff,
        'text': vf_text,
        'color': vf_status['color'],
        'normal_range': vf_status['normal_range'],
    }
    
    # Muscle percent comparison
    muscle_diff = float(last_record.muscle_percent) - float(first_record.muscle_percent)
    muscle_text = get_comparison_text(muscle_diff)
    muscle_status = last_record.get_muscle_percent_status()
    comparison['muscle_percent'] = {
        'start_value': float(first_record.muscle_percent),
        'end_value': float(last_record.muscle_percent),
        'diff': muscle_diff,
        'text': muscle_text,
        'color': muscle_status['color'],
        'normal_range': muscle_status['normal_range'],
    }
    
    # Blood pressure systolic comparison
    bp_sys_diff = last_record.blood_pressure_systolic - first_record.blood_pressure_systolic
    bp_sys_text = get_comparison_text(bp_sys_diff)
    bp_sys_status = last_record.get_blood_pressure_status()
    comparison['blood_pressure_systolic'] = {
        'start_value': first_record.blood_pressure_systolic,
        'end_value': last_record.blood_pressure_systolic,
        'diff': bp_sys_diff,
        'text': bp_sys_text,
        #'color': '#28a745' if abs(bp_sys_diff) <= 5 else '#ffc107',
        'color': bp_sys_status['color'],
        'normal_range': bp_sys_status['normal_range'],
    }
    
    # Blood pressure diastolic comparison
    bp_dia_diff = last_record.blood_pressure_diastolic - first_record.blood_pressure_diastolic
    bp_dia_text = get_comparison_text(bp_dia_diff)
    bp_dia_status = last_record.get_blood_pressure_status()
    comparison['blood_pressure_diastolic'] = {
        'start_value': first_record.blood_pressure_diastolic,
        'end_value': last_record.blood_pressure_diastolic,
        'diff': bp_dia_diff,
        'text': bp_dia_text,
        #'color': '#28a745' if abs(bp_dia_diff) <= 5 else '#ffc107',
        'color': bp_dia_status['color'],
        'normal_range': bp_dia_status['normal_range'],
    }
    
    # Waist comparison
    waist_diff = float(last_record.waist) - float(first_record.waist)
    waist_text = get_comparison_text(waist_diff)
    waist_status = last_record.get_waist_status()
    comparison['waist'] = {
        'start_value': float(first_record.waist),
        'end_value': float(last_record.waist),
        'diff': waist_diff,
        'text': waist_text,
        'color': waist_status['color'],
        'normal_range': waist_status['normal_range'],
    }
    
    # Cholesterol comparison
    if first_record.cholesterol and last_record.cholesterol:
        chol_diff = float(last_record.cholesterol) - float(first_record.cholesterol)
        chol_text = get_comparison_text(chol_diff)
        chol_status = last_record.get_cholesterol_status()
        comparison['cholesterol'] = {
            'start_value': float(first_record.cholesterol),
            'end_value': float(last_record.cholesterol),
            'diff': chol_diff,
            'text': chol_text,
            'color': chol_status['color'] if chol_status else '#6c757d',
        }
    
    # LDL comparison
    if first_record.ldl and last_record.ldl:
        ldl_diff = float(last_record.ldl) - float(first_record.ldl)
        ldl_text = get_comparison_text(ldl_diff)
        ldl_status = last_record.get_ldl_status()
        comparison['ldl'] = {
            'start_value': float(first_record.ldl),
            'end_value': float(last_record.ldl),
            'diff': ldl_diff,
            'text': ldl_text,
            'color': ldl_status['color'] if ldl_status else '#6c757d',
        }
    
    # HDL comparison
    if first_record.hdl and last_record.hdl:
        hdl_diff = float(last_record.hdl) - float(first_record.hdl)
        hdl_text = get_comparison_text(hdl_diff)
        hdl_status = last_record.get_hdl_status()
        comparison['hdl'] = {
            'start_value': float(first_record.hdl),
            'end_value': float(last_record.hdl),
            'diff': hdl_diff,
            'text': hdl_text,
            'color': hdl_status['color'] if hdl_status else '#6c757d',
        }
    
    # FBS comparison
    if first_record.fbs and last_record.fbs:
        fbs_diff = float(last_record.fbs) - float(first_record.fbs)
        fbs_text = get_comparison_text(fbs_diff)
        fbs_status = last_record.get_fbs_status()
        comparison['fbs'] = {
            'start_value': float(first_record.fbs),
            'end_value': float(last_record.fbs),
            'diff': fbs_diff,
            'text': fbs_text,
            'color': fbs_status['color'] if fbs_status else '#6c757d',
        }

    # Triglycerides comparison
    if first_record.triglycerides and last_record.triglycerides:
        tg_diff = float(last_record.triglycerides) - float(first_record.triglycerides)
        tg_text = get_comparison_text(tg_diff)
        tg_status = last_record.get_triglycerides_status()
        comparison['triglycerides'] = {
            'start_value': float(first_record.triglycerides),
            'end_value': float(last_record.triglycerides),
            'diff': tg_diff,
            'text': tg_text,
            'color': tg_status['color'] if tg_status else '#6c757d',
        }
    
    return comparison


def get_comparison_text(diff):
    """Get Thai comparison text based on difference"""
    if diff > 0:
        return f"เพิ่มขึ้น {abs(diff):.1f}"
    elif diff < 0:
        return f"ลดลง {abs(diff):.1f}"
    else:
        return "เท่าเดิม"


def generate_summary_info(first_record, last_record, profile):
    """Generate summary information with Thai text"""
    comparison = generate_comparison_table(first_record, last_record, profile)
    
    summary = {
        
        'bmi': f"BMI {comparison['bmi']['text']} ค่าปกติ {comparison['bmi']['normal_range']}",
        'waist': f"รอบเอว {comparison['waist']['text']} ค่าปกติ {comparison['waist']['normal_range']}",
        'blood_pressure_systolic': f"ความดันโลหิตตัวบน {comparison['blood_pressure_systolic']['text']} ค่าปกติ {comparison['blood_pressure_systolic']['normal_range']}",
        'blood_pressure_diastolic': f"ความดันโลหิตตัวล่าง {comparison['blood_pressure_diastolic']['text']} ค่าปกติ {comparison['blood_pressure_diastolic']['normal_range']}",
        'fat_percent': f"เปอร์เซ็นต์ไขมัน {comparison['fat_percent']['text']} ค่าปกติ {comparison['fat_percent']['normal_range']}",
        'visceral_fat': f"เปอร์เซ็นต์ไขมันในช่องท้อง {comparison['visceral_fat']['text']} ค่าปกติ {comparison['visceral_fat']['normal_range']}",
        'muscle_percent': f"เปอร์เซ็นต์มวลกล้ามเนื้อ {comparison['muscle_percent']['text']} ค่าปกติ {comparison['muscle_percent']['normal_range']}",
        'cholesterol': f"คอเลสเตอรอล {comparison['cholesterol']['text']}" if 'cholesterol' in comparison else '',
        'ldl': f"LDL {comparison['ldl']['text']}" if 'ldl' in comparison else '',
        'hdl': f"HDL {comparison['hdl']['text']}" if 'hdl' in comparison else '',
        'fbs': f"น้ำตาลในเลือดขณะอดอาหาร {comparison['fbs']['text']}" if 'fbs' in comparison else '',
        'triglycerides': f"ไตรกลีเซอไรด์ {comparison['triglycerides']['text']}" if 'triglycerides' in comparison else '',
    }
    
    return summary
