from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
class CustomUserAdmin(UserAdmin):
    # Show name, email, and staff status in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    
    # Organize the detail page
    list_filter = ('is_staff', 'is_superuser', 'is_active')

admin.site.register(User, CustomUserAdmin)
