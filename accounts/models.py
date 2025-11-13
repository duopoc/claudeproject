"""
Accounts models with User Profile and MFA support
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import pyotp


class UserProfile(models.Model):
    """Extended user profile with MFA and additional information"""
    ROLE_CHOICES = [
        ('normal', 'Normal User'),
        ('admin', 'Admin'),
        ('superuser', 'Super User'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'ชาย'),
        ('female', 'หญิง'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    firstname = models.CharField(max_length=100, verbose_name='ชื่อ', default='', blank=True)
    lastname = models.CharField(max_length=100, verbose_name='นามสกุล', default='', blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='เพศ', default='male', blank=True)
    age = models.IntegerField(verbose_name='อายุ', default=30, blank=True)
    phone = models.CharField(max_length=20, verbose_name='เบอร์โทรศัพท์', default='', blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True, verbose_name='รูปโปรไฟล์')
    nickname = models.CharField(max_length=50, null=True, blank=True, verbose_name='ชื่อเล่น')
    
    # User status and role
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='normal')
    is_active_status = models.BooleanField(default=False, verbose_name='สถานะการใช้งาน')
    is_banned = models.BooleanField(default=False, verbose_name='ถูกแบน')
    
    # MFA fields
    mfa_enabled = models.BooleanField(default=False, verbose_name='เปิดใช้ MFA')
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.user.username})"
    
    def generate_mfa_secret(self):
        """Generate a new MFA secret key"""
        if not self.mfa_secret:
            self.mfa_secret = pyotp.random_base32()
            self.save()
        return self.mfa_secret
    
    def get_mfa_uri(self):
        """Get the provisioning URI for QR code generation"""
        if not self.mfa_secret:
            self.generate_mfa_secret()
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.user.username,
            issuer_name='Health Progress'
        )
    
    def verify_mfa_token(self, token):
        """Verify the MFA token"""
        if not self.mfa_secret:
            return False
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token, valid_window=1)
    
    def requires_mfa(self):
        """Check if user requires MFA (admin or superuser)"""
        return self.role in ['admin', 'superuser']
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class UserActivity(models.Model):
    """Track user activities for admin dashboard"""
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('profile_update', 'Profile Update'),
        ('health_record_add', 'Health Record Added'),
        ('health_record_update', 'Health Record Updated'),
        ('password_reset', 'Password Reset'),
        ('status_change', 'Status Changed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when user is created or updated"""
    if created:
        # Determine role based on user permissions
        if instance.is_superuser:
            role = 'superuser'
            is_active_status = True
        elif instance.is_staff:
            role = 'admin'
            is_active_status = True
        else:
            role = 'normal'
            is_active_status = False
        
        UserProfile.objects.create(
            user=instance,
            role=role,
            is_active_status=is_active_status
        )
    else:
        if hasattr(instance, 'profile'):
            # Update profile role if user permissions changed
            profile = instance.profile
            if instance.is_superuser and profile.role != 'superuser':
                profile.role = 'superuser'
                profile.is_active_status = True
                profile.save()
            instance.profile.save()
