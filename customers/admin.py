from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'phone', 'province', 'is_active')
    search_fields = ('code', 'name', 'phone', 'tax_id')
    list_filter = ('province', 'is_active')
    ordering = ('code',)