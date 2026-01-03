from django.contrib import admin
from .models import Quotation, QuotationItem, Province, Amphure, Tambon

class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0
    readonly_fields = ('total_price',)

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('qt_number', 'customer_name', 'date', 'grand_total', 'status')
    inlines = [QuotationItemInline]
    search_fields = ('qt_number', 'customer_name')

# Register Master Data
admin.site.register(Province)
admin.site.register(Amphure)
admin.site.register(Tambon)