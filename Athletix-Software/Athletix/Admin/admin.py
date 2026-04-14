from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from player.models import AthleteCoach, AthleteSport, CoachRequest, DailyRoutine, Sport
from user.models import AthleteProfile, CoachProfile, MedicalProfile, User


class CoachProfileInline(admin.StackedInline):
    model = CoachProfile
    can_delete = False
    extra = 0


class AthleteProfileInline(admin.StackedInline):
    model = AthleteProfile
    can_delete = False
    extra = 0


class MedicalProfileInline(admin.StackedInline):
    model = MedicalProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'name', 'role', 'is_approved', 'is_active', 'is_staff', 'is_superuser', 'date_joined'
    )
    list_filter = ('role', 'is_approved', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'name', 'phone')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    actions = [
        'approve_selected_coaches',
        'mark_selected_users_active',
        'mark_selected_users_inactive',
    ]

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        if obj.role == 'coach':
            return [CoachProfileInline]
        if obj.role == 'athlete':
            return [AthleteProfileInline]
        if obj.role == 'medical':
            return [MedicalProfileInline]
        return []

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'role', 'phone', 'date_of_birth', 'blood_group', 'address', 'profile_photo')}),
        ('Approval', {'fields': ('is_approved',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    @admin.action(description='Approve selected coaches (complete signup)')
    def approve_selected_coaches(self, request, queryset):
        updated = queryset.filter(role='coach', is_approved=False).update(is_approved=True, is_active=True)
        self.message_user(request, f'{updated} coach account(s) approved.')

    @admin.action(description='Set selected users active')
    def mark_selected_users_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) marked active.')

    @admin.action(description='Set selected users inactive')
    def mark_selected_users_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) marked inactive.')


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(CoachRequest)
class CoachRequestAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'coach', 'sport', 'status', 'created_at')
    list_filter = ('status', 'sport', 'created_at')
    search_fields = ('athlete__name', 'coach__name', 'sport__name')


@admin.register(AthleteCoach)
class AthleteCoachAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'coach', 'sport', 'start_date', 'is_active')
    list_filter = ('is_active', 'sport', 'start_date')
    search_fields = ('athlete__name', 'coach__name', 'sport__name')


@admin.register(DailyRoutine)
class DailyRoutineAdmin(admin.ModelAdmin):
    list_display = ('title', 'athlete', 'coach', 'sport', 'day', 'start_time', 'end_time')
    list_filter = ('day', 'sport', 'coach')
    search_fields = ('title', 'athlete__name', 'coach__name', 'sport__name')


@admin.register(AthleteSport)
class AthleteSportAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'sport', 'skill_level', 'joined_at')
    list_filter = ('sport', 'skill_level')
    search_fields = ('athlete__name', 'sport__name')


@admin.register(AthleteProfile)
class AthleteProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'height', 'weight', 'fitness_level')
    search_fields = ('user__name', 'user__email')


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'sport', 'specialization', 'experience_years', 'certification')
    list_filter = ('sport',)
    search_fields = ('user__name', 'user__email', 'specialization', 'certification')


@admin.register(MedicalProfile)
class MedicalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_no', 'specialty')
    search_fields = ('user__name', 'user__email', 'license_no', 'specialty')


admin.site.site_header = 'Athletix Administration'
admin.site.site_title = 'Athletix Admin'
