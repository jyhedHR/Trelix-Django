from django.contrib import admin
from .models import Profile, TrustedDevice

@admin.register(TrustedDevice)
class TrustedDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_key', 'last_used', 'created_at')
    list_filter = ('created_at', 'last_used')
    search_fields = ('user__username', 'user__email', 'user_agent')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'two_step_verification', 'phone_number', 'created_at')
    list_filter = ('user_type', 'two_step_verification', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'profile_picture')
        }),
        ('Security', {
            'fields': ('two_step_verification', 'otp_secret', 'backup_codes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
