from django.contrib import admin
from .models import Quotation, QuotationItem, Customer

# ==========================================
# 👥 1. ส่วนจัดการลูกค้า (CRM)
# ==========================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'tax_id', 'branch')
    search_fields = ('name', 'contact_person', 'tax_id', 'phone')
    list_filter = ('branch',)
    
    # เพิ่มความสวยงาม: แสดงช่องค้นหาด้านบน
    ordering = ('name',) 

# ==========================================
# 📄 2. ส่วนจัดการใบเสนอราคา (Quotation)
# ==========================================
class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0 # ไม่ต้องโชว์บรรทัดว่าง
    readonly_fields = ('total_price',) # ห้ามแก้ราคารวมเอง (ให้ระบบคำนวณ)

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('qt_number', 'customer_name', 'date', 'grand_total', 'status', 'sales_person')
    list_filter = ('status', 'date', 'sales_person')
    search_fields = ('qt_number', 'customer_name')
    date_hierarchy = 'date'
    
    # เอารายการสินค้าไปแปะในหน้าแก้ใบเสนอราคาด้วย
    inlines = [QuotationItemInline]