from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html # เครื่องมือสร้างรูปภาพ
from import_export.admin import ImportExportModelAdmin

# ✅ เพิ่ม CompanyInfo เข้าไปในรายการ import
from .models import Employee, Attendance, LeaveRequest, Product, Order, OrderItem, Category, BOMItem, ProductionOrder, CompanyInfo

# ==========================================
# 1. ปรับแต่ง User Admin (หน้ารายชื่อ User)
# ==========================================
class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'ข้อมูลพนักงาน (Employee Info)'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (EmployeeInline, )
    list_display = ('username', 'first_name', 'last_name', 'get_department', 'get_employee_status', 'is_staff')

    def get_department(self, obj):
        if hasattr(obj, 'employee') and obj.employee:
            return obj.employee.department
        return "-"
    get_department.short_description = 'แผนก'

    def get_employee_status(self, obj):
        if hasattr(obj, 'employee') and obj.employee:
            return obj.employee.status
        return "-"
    get_employee_status.short_description = 'สถานะ'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ==========================================
# 2. Employee Admin (จัดการพนักงาน)
# ==========================================
@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin): # ✅ ระบบ Export ยังอยู่ครบ
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'position', 'manager', 'status')
    search_fields = ('first_name', 'last_name', 'employee_id', 'department', 'user__username')
    list_filter = ('department', 'position', 'status')

# ==========================================
# 3. Model อื่นๆ (Attendance, Leave)
# ==========================================
@admin.register(Attendance)
class AttendanceAdmin(ImportExportModelAdmin):
    list_display = ('employee', 'date', 'time_in', 'time_out')
    list_filter = ('date', 'employee__department')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(ImportExportModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')

# ==========================================
# 4. ✅ ส่วนจัดการหมวดหมู่ (Category & Product)
# ==========================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # ✅ ใช้ field 'category' ตัวจริง
    list_display = ('show_image', 'name', 'category', 'price', 'stock', 'is_active')

    # แก้ไขหมวดหมู่ได้ทันทีจากหน้ารวม (List Editable)
    list_editable = ('price', 'stock', 'is_active', 'category')

    # ค้นหาได้ทั้งชื่อสินค้า และ ชื่อหมวดหมู่
    search_fields = ('name', 'category__name')

    # ตัวกรองด้านขวา
    list_filter = ('category', 'is_active')

    # ฟังก์ชันโชว์รูปภาพ
    def show_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;">', obj.image.url)
        return format_html('<img src="https://placehold.co/50x50?text=No+Img" style="width: 50px; height: 50px; border-radius: 5px; opacity: 0.5;">')

    show_image.short_description = 'รูปตัวอย่าง'

# ตัวจัดการ Order (คงเดิม)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_total_item_price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'total_amount', 'order_date')
    inlines = [OrderItemInline]
    readonly_fields = ('order_date',)

# ==========================================
# 5. 🏭 ส่วนจัดการโรงงาน (Manufacturing Admin)
# ==========================================

class BOMItemInline(admin.TabularInline):
    model = BOMItem
    fk_name = 'finished_good'
    extra = 1
    verbose_name = "วัตถุดิบที่ต้องใช้"
    verbose_name_plural = "สูตรการผลิต (Recipe)"

@admin.register(BOMItem)
class BOMItemAdmin(admin.ModelAdmin):
    list_display = ('finished_good', 'raw_material', 'quantity')
    list_filter = ('finished_good',)
    search_fields = ('finished_good__name', 'raw_material__name')

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'quantity', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__name', 'note')
    date_hierarchy = 'created_at'
    list_editable = ('status',)

# ==========================================
# 6. 🏢 ข้อมูลบริษัท (Global Company Settings) ✅ เพิ่มใหม่
# ==========================================
@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['name_th', 'tax_id', 'phone']
    
    # เทคนิค: ป้องกันไม่ให้สร้างข้อมูลบริษัทเกิน 1 แห่ง
    def has_add_permission(self, request):
        # ถ้ามีข้อมูลอยู่แล้ว ห้ามสร้างเพิ่ม (ให้กดแก้ไขของเดิมเอา)
        if CompanyInfo.objects.exists():
            return False
        return True