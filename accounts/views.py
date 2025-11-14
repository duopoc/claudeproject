"""
Accounts views for user management, authentication, and MFA
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
import qrcode
import io
import base64
from .models import UserProfile, UserActivity
from .forms import (
    UserRegistrationForm, UserProfileForm, MFATokenForm,
    UserManagementForm, AdminUserCreationForm
)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(user, action, description='', request=None):
    """Log user activity"""
    activity = UserActivity.objects.create(
        user=user,
        action=action,
        description=description
    )
    if request:
        activity.ip_address = get_client_ip(request)
        activity.user_agent = request.META.get('HTTP_USER_AGENT', '')
        activity.save()


def register_view(request):
    """User registration view - users start as inactive"""
    if request.user.is_authenticated:
        return redirect('health_app:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user but don't save yet
            user = form.save(commit=False)
            user.is_active = False  # User starts inactive
            user.save()
            
            # Create/update profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.firstname = form.cleaned_data['firstname']
            profile.lastname = form.cleaned_data['lastname']
            profile.gender = form.cleaned_data['gender']
            profile.birthdate = form.cleaned_data['birthdate']
            profile.phone = form.cleaned_data['phone']
            profile.is_active_status = False  # Needs admin approval
            profile.role = 'normal'
            profile.save()
            
            log_activity(user, 'profile_update', 'User registered - awaiting approval', request)
            
            messages.success(request, 'ลงทะเบียนสำเร็จ! รอการอนุมัติจากผู้ดูแลระบบ')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Login view with MFA support"""
    if request.user.is_authenticated:
        return redirect('health_app:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is active
            if not user.is_active or not user.profile.is_active_status:
                messages.error(request, 'บัญชีของคุณยังไม่ได้รับการอนุมัติหรือถูกระงับ')
                return redirect('accounts:login')
            
            # Check if banned
            if user.profile.is_banned:
                messages.error(request, 'บัญชีของคุณถูกแบน')
                return redirect('accounts:login')
            
            # Check if profile is complete
            if not user.profile.firstname or not user.profile.lastname:
                messages.warning(request, 'กรุณาเพิ่มข้อมูลโปรไฟล์ให้ครบถ้วน')
                login(request, user)
                return redirect('accounts:profile')
            
            # Check if user requires MFA
            if user.profile.requires_mfa():
                # Check if MFA is already setup
                if user.profile.mfa_enabled:
                    # MFA is setup, verify the code
                    request.session['pre_mfa_user_id'] = user.id
                    request.session['pre_mfa_username'] = user.username
                    return redirect('accounts:mfa_verify')
                else:
                    # MFA is required but not setup yet, login and redirect to setup
                    login(request, user)
                    user.profile.last_login_at = timezone.now()
                    user.profile.save()
                    log_activity(user, 'login', f'Logged in from {get_client_ip(request)} - MFA setup required', request)
                    messages.warning(request, '⚠️ คุณต้องตั้งค่า MFA (Google Authenticator) เพื่อความปลอดภัย')
                    return redirect('accounts:mfa_setup')
            else:
                # No MFA required, login directly
                login(request, user)
                user.profile.last_login_at = timezone.now()
                user.profile.save()
                log_activity(user, 'login', f'Logged in from {get_client_ip(request)}', request)
                messages.success(request, f'ยินดีต้อนรับ {user.profile.firstname or user.username}!')
                return redirect('health_app:dashboard')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    
    return render(request, 'accounts/login.html')


def mfa_verify_view(request):
    """MFA verification view"""
    # Check if user is in pre-MFA session
    if 'pre_mfa_user_id' not in request.session:
        messages.error(request, 'เซสชันหมดอายุ กรุณาล็อกอินใหม่')
        return redirect('accounts:login')
    
    user_id = request.session.get('pre_mfa_user_id')
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = MFATokenForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            
            if user.profile.verify_mfa_token(token):
                # MFA successful
                login(request, user)
                user.profile.last_login_at = timezone.now()
                user.profile.save()
                
                # Clear pre-MFA session
                del request.session['pre_mfa_user_id']
                del request.session['pre_mfa_username']
                
                log_activity(user, 'login', f'Logged in with MFA from {get_client_ip(request)}', request)
                messages.success(request, f'ยินดีต้อนรับ {user.profile.firstname}!')
                return redirect('health_app:dashboard')
            else:
                messages.error(request, 'รหัส MFA ไม่ถูกต้อง')
    else:
        form = MFATokenForm()
    
    return render(request, 'accounts/mfa_verify.html', {
        'form': form,
        'username': request.session.get('pre_mfa_username')
    })


@login_required
def mfa_setup_view(request):
    """MFA setup view for admin/superuser"""
    if not request.user.profile.requires_mfa():
        messages.error(request, 'MFA ไม่จำเป็นสำหรับบัญชีของคุณ')
        return redirect('accounts:profile')
    
    profile = request.user.profile
    
    # Generate MFA secret if not exists
    if not profile.mfa_secret:
        profile.generate_mfa_secret()
    
    # Generate QR code
    qr_uri = profile.get_mfa_uri()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    if request.method == 'POST':
        form = MFATokenForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            if profile.verify_mfa_token(token):
                profile.mfa_enabled = True
                profile.save()
                messages.success(request, 'เปิดใช้งาน MFA สำเร็จ!')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'รหัส MFA ไม่ถูกต้อง กรุณาลองใหม่')
    else:
        form = MFATokenForm()
    
    return render(request, 'accounts/mfa_setup.html', {
        'form': form,
        'qr_code': qr_code_base64,
        'secret_key': profile.mfa_secret
    })


@login_required
def profile_view(request):
    """User profile view"""
    profile = request.user.profile

    # Check if profile is incomplete
    profile_incomplete = not profile.firstname or not profile.lastname or not profile.birthdate
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'profile_update', 'Profile updated', request)
            messages.success(request, 'อัปเดตโปรไฟล์สำเร็จ!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    # Check if MFA is required but not enabled
    mfa_warning = profile.requires_mfa() and not profile.mfa_enabled
    mfa_required_but_not_setup = mfa_warning  # More descriptive variable name
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'mfa_warning': mfa_warning,
        'mfa_required_but_not_setup': mfa_required_but_not_setup,
        'profile_incomplete': profile_incomplete,
    })


@login_required
def logout_view(request):
    """Logout view"""
    log_activity(request.user, 'logout', f'Logged out from {get_client_ip(request)}', request)
    logout(request)
    messages.success(request, 'ออกจากระบบสำเร็จ')
    return redirect('accounts:login')


# Admin-only views
def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and user.profile.role in ['admin', 'superuser']


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.profile.role == 'superuser'


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with user management"""
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    
    # Filter options
    status_filter = request.GET.get('status', 'all')
    role_filter = request.GET.get('role', 'all')
    search_query = request.GET.get('search', '')
    
    if status_filter == 'active':
        users = users.filter(profile__is_active_status=True, profile__is_banned=False)
    elif status_filter == 'inactive':
        users = users.filter(profile__is_active_status=False)
    elif status_filter == 'banned':
        users = users.filter(profile__is_banned=True)
    
    if role_filter != 'all':
        users = users.filter(profile__role=role_filter)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__firstname__icontains=search_query) |
            Q(profile__lastname__icontains=search_query)
        )
    
    # Get recent activities
    recent_activities = UserActivity.objects.select_related('user').all()[:50]
    
    # Statistics
    total_users = User.objects.count()
    active_users = UserProfile.objects.filter(is_active_status=True, is_banned=False).count()
    pending_users = UserProfile.objects.filter(is_active_status=False, is_banned=False).count()
    banned_users = UserProfile.objects.filter(is_banned=True).count()
    
    context = {
        'users': users,
        'recent_activities': recent_activities,
        'total_users': total_users,
        'active_users': active_users,
        'pending_users': pending_users,
        'banned_users': banned_users,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'search_query': search_query,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def user_management_view(request, user_id):
    """User management view for admin"""
    managed_user = get_object_or_404(User, id=user_id)
    profile = managed_user.profile
    
    # Superuser restrictions
    if profile.role == 'admin' and request.user.profile.role != 'superuser':
        messages.error(request, 'คุณไม่มีสิทธิ์จัดการแอดมิน')
        return redirect('accounts:admin_dashboard')
    
    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=profile)
        if form.is_valid():
            # Role change restrictions
            if profile.role == 'admin' and request.user.profile.role != 'superuser':
                messages.error(request, 'เฉพาะ Superuser เท่านั้นที่จัดการแอดมินได้')
                return redirect('accounts:admin_dashboard')
            
            old_status = profile.is_active_status
            form.save()
            
            # Update user.is_active based on profile status
            managed_user.is_active = profile.is_active_status and not profile.is_banned
            managed_user.save()
            
            # Log the change
            if old_status != profile.is_active_status:
                status = 'approved' if profile.is_active_status else 'deactivated'
                log_activity(managed_user, 'status_change', f'Status changed to {status} by {request.user.username}', request)
            
            messages.success(request, 'อัปเดตข้อมูลผู้ใช้สำเร็จ!')
            return redirect('accounts:admin_dashboard')
    else:
        form = UserManagementForm(instance=profile)
    
    return render(request, 'accounts/user_management.html', {
        'form': form,
        'managed_user': managed_user,
        'profile': profile
    })


@login_required
@user_passes_test(is_admin)
def user_delete_view(request, user_id):
    """Delete user (admin only)"""
    managed_user = get_object_or_404(User, id=user_id)
    
    if managed_user.profile.role in ['admin', 'superuser'] and request.user.profile.role != 'superuser':
        messages.error(request, 'คุณไม่มีสิทธิ์ลบแอดมิน')
        return redirect('accounts:admin_dashboard')
    
    if request.method == 'POST':
        username = managed_user.username
        managed_user.delete()
        messages.success(request, f'ลบผู้ใช้ {username} สำเร็จ!')
        return redirect('accounts:admin_dashboard')
    
    return render(request, 'accounts/user_delete_confirm.html', {'managed_user': managed_user})


@login_required
@user_passes_test(is_admin)
def user_create_view(request):
    """Create new user (admin only)"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if form.is_valid():
            # Check role permissions
            role = form.cleaned_data['role']
            if role in ['admin', 'superuser'] and request.user.profile.role != 'superuser':
                messages.error(request, 'เฉพาะ Superuser เท่านั้นที่สร้างแอดมินได้')
                return redirect('accounts:admin_dashboard')
            
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = form.cleaned_data['is_active_status']
            user.save()
            
            # Update profile
            profile = user.profile
            profile.firstname = form.cleaned_data['firstname']
            profile.lastname = form.cleaned_data['lastname']
            profile.gender = form.cleaned_data['gender']
            profile.age = form.cleaned_data['age']
            profile.phone = form.cleaned_data['phone']
            profile.role = form.cleaned_data['role']
            profile.is_active_status = form.cleaned_data['is_active_status']
            profile.save()
            
            log_activity(user, 'profile_update', f'User created by {request.user.username}', request)
            messages.success(request, f'สร้างผู้ใช้ {username} สำเร็จ!')
            return redirect('accounts:admin_dashboard')
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'accounts/user_create.html', {'form': form})


# Password Reset Views
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view"""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


def landing_page(request):
    """Landing page view"""
    if request.user.is_authenticated:
        return redirect('health_app:dashboard')
    return render(request, 'accounts/landing.html')
