from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario



@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'rol', 'is_staff', 'date_joined']
    list_filter = ['rol', 'is_staff', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Farmacia', {'fields': ('rol', 'telefono')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Farmacia', {'fields': ('rol', 'telefono')}),
    )