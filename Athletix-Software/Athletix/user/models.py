from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role='athlete', **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, role='coach', **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('athlete', 'Athlete'),
        ('coach', 'Coach'),
        ('medical', 'Medical Staff'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='athlete')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    is_approved = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    @property
    def first_name(self):
        return self.name.split()[0] if self.name else ''
    
    @property
    def last_name(self):
        parts = self.name.split()
        return ' '.join(parts[1:]) if len(parts) > 1 else ''

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.get_role_display()}"

    @property
    def health_record_count(self):
        return self.health_records.count()

    @property
    def medical_feedback_count(self):
        return self.medical_feedbacks.count()

    class Meta:
        db_table = 'user_table'


class AthleteProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='athlete_profile')
    sport_type = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.CharField(max_length=20, blank=True, help_text="e.g., 5'10\" or 178 cm")
    weight = models.CharField(max_length=20, blank=True, help_text="e.g., 70 kg")
    fitness_level = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )

    def __str__(self):
        return f"Athlete: {self.user.name}"

    class Meta:
        db_table = 'athlete_profile'


class CoachProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coach_profile')
    sport = models.ForeignKey('player.Sport', on_delete=models.SET_NULL, null=True, blank=True, related_name='coaches')
    specialization = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    certification = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Coach: {self.user.name}"

    class Meta:
        db_table = 'coach_profile'


class MedicalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='medical_profile')
    license_no = models.CharField(max_length=100, unique=True, blank=True, null=True)
    specialty = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Medical: {self.user.name}"

    class Meta:
        db_table = 'medical_profile'
