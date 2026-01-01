from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ================================
# 1. ตารางพนักงาน (Employee) 👨‍💼
# ================================
class Employee(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'ทำงานอยู่'),
        ('PROBATION', 'ทดลองงาน'),
        ('RESIGNED', 'ลาออก'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="รหัสพนักงาน")

    first_name = models.CharField(max_length=100, verbose_name="ชื่อจริง", default="")
    last_name = models.CharField(max_length=100, verbose_name="นามสกุล", default="")

    image = models.ImageField(upload_to='employee_images/', blank=True, null=True, verbose_name="รูปโปรไฟล์")
    position = models.CharField(max_length=100, verbose_name="ตำแหน่ง")
    department = models.CharField(max_length=100, verbose_name="แผนก")
    line_user_id = models.CharField(max_length=50, blank=True, null=True, help_text="ใส่ User ID ของ LINE (U...) เพื่อรับแจ้งเตือน")

    # ระบบหัวหน้างาน
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name="หัวหน้างานโดยตรง (Manager)"
    )

    base_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=15000, verbose_name="เงินเดือน")
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="โบนัสสะสม")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="สถานะ")
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="เบอร์โทร")
    joined_date = models.DateField(auto_now_add=True, verbose_name="วันที่เริ่มงาน")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"

    @property
    def formatted_salary(self):
        return "{:,.2f}".format(self.base_allowance)

# ================================
# 2. ตารางตอกบัตร (Attendance) 🕒
# ================================
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.first_name} - {self.date}"

# ================================
# 3. ตารางการลา (Leave Request) 🏖️
# ================================
class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('SICK', 'ลาป่วย'),
        ('BUSINESS', 'ลากิจ'),
        ('VACATION', 'พักร้อน'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'รออนุมัติ'),
        ('APPROVED', 'อนุมัติ'),
        ('REJECTED', 'ไม่อนุมัติ'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.first_name} - {self.leave_type}"

    @property
    def days(self):
        delta = self.end_date - self.start_date
        return delta.days + 1

# ==========================================
# 4. ตารางซัพพลายเออร์ (Supplier)
# ==========================================
class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อบริษัท/ร้านค้า")
    contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="ชื่อผู้ติดต่อ")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    address = models.TextField(blank=True, null=True, verbose_name="ที่อยู่")
    line_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Line ID")

    def __str__(self):
        return self.name

# ==========================================
# 5. ตารางหมวดหมู่สินค้า
# ==========================================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อหมวดหมู่")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "จัดการหมวดหมู่สินค้า (Categories)"

# ==========================================
# 6. ตู้เก็บสินค้า (Product)
# ==========================================
class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อสินค้า")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="หมวดหมู่")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    
    PRODUCT_TYPES = [
        ('FG', 'สินค้าสำเร็จรูป (Finished Good)'),
        ('RM', 'วัตถุดิบ (Raw Material)'),
    ]
    product_type = models.CharField(max_length=2, choices=PRODUCT_TYPES, default='FG', verbose_name="ประเภทสินค้า")

    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ราคาทุน")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ราคาขาย")

    stock = models.IntegerField(default=0, verbose_name="จำนวนคงเหลือ")
    alert_level = models.IntegerField(default=5, verbose_name="แจ้งเตือนเมื่อต่ำกว่า")

    barcode = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name="รหัสบาร์โค้ด")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ซัพพลายเออร์")

    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="รูปสินค้า")
    is_active = models.BooleanField(default=True, verbose_name="เปิดขาย")

    def __str__(self):
        return f"{self.name} ({self.stock})"

# ==========================================
# 7. ตู้เก็บหัวบิล (Order) - POS
# ==========================================
class Order(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, verbose_name="พนักงานขาย")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="วันที่ขาย")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ยอดรวมทั้งสิ้น")

    def __str__(self):
        return f"Order #{self.id} by {self.employee.first_name}"

# ==========================================
# 8. ตู้เก็บรายการในบิล (OrderItem) - POS
# ==========================================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="สินค้า")
    quantity = models.IntegerField(default=1, verbose_name="จำนวน")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาต่อชิ้น(ตอนขาย)")

    def get_total_item_price(self):
        return self.quantity * self.price

    def __str__(self):
        if self.product:
            return f"{self.product.name} x {self.quantity}"
        return f"Unknown Product x {self.quantity}"

# ==========================================
# 9. บันทึกการเคลื่อนไหวสต็อก (StockTransaction)
# ==========================================
class StockTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', '🟢 รับเข้า (ซื้อเพิ่ม/รับคืน)'),
        ('OUT', '🔴 จ่ายออก (ขาย/เบิกใช้)'),
        ('ADJUST', '🟠 ปรับปรุง (ของหาย/นับสต็อก)'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="สินค้า")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="ประเภทรายการ")
    quantity = models.IntegerField(verbose_name="จำนวน")
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ราคาต่อหน่วย(ตอนทำรายการ)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ผู้ทำรายการ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่ทำรายการ")
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity})"

# ==========================================
# 10. ระบบจัดซื้อ (Purchasing)
# ==========================================
class PurchaseOrder(models.Model):
    PO_STATUS = [
        ('PENDING', '📝 รอดำเนินการ (Draft)'),
        ('ORDERED', '📞 สั่งของแล้ว (Ordered)'),
        ('RECEIVED', '✅ รับของแล้ว (Received)'),
        ('CANCELLED', '❌ ยกเลิก (Cancelled)'),
    ]

    po_number = models.CharField(max_length=20, unique=True, verbose_name="เลขที่ใบสั่งซื้อ")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="ซัพพลายเออร์")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ผู้สั่งซื้อ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_date = models.DateField(default=timezone.now, verbose_name="วันที่สั่ง")
    status = models.CharField(max_length=10, choices=PO_STATUS, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ยอดรวม")
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, verbose_name="จำนวน")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาต่อหน่วย (ทุน)")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ราคารวม")

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

# ==========================================
# 11. ระบบผลิต (Manufacturing System)
# ==========================================
class BOMItem(models.Model):
    """
    สูตรการผลิต (Bill of Materials)
    บอกว่า: สินค้า (FG) 1 ชิ้น ใช้วัตถุดิบ (RM) อะไรบ้าง?
    """
    finished_good = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_items', limit_choices_to={'product_type': 'FG'}, verbose_name="สินค้าที่ผลิต (FG)")
    raw_material = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in_bom', limit_choices_to={'product_type': 'RM'}, verbose_name="วัตถุดิบที่ใช้ (RM)")
    quantity = models.FloatField(default=1.0, verbose_name="จำนวนที่ใช้ (ต่อ 1 ชิ้น)")

    def __str__(self):
        return f"{self.finished_good.name} ใช้ {self.raw_material.name} ({self.quantity})"

class ProductionOrder(models.Model):
    """
    ใบสั่งผลิต (Production Order - MO)
    """
    job_number = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="เลขที่ใบงาน (JOB)")
    STATUS_CHOICES = [
        ('PENDING', 'รอผลิต'),
        ('IN_PROGRESS', 'กำลังผลิต'),
        ('COMPLETED', 'ผลิตเสร็จสิ้น (ตัดสต็อก)'),
        ('CANCELLED', 'ยกเลิก'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, limit_choices_to={'product_type': 'FG'}, verbose_name="สินค้าที่จะผลิต")
    quantity = models.PositiveIntegerField(default=1, verbose_name="จำนวนที่ผลิต")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="สถานะ")

    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ผู้สั่งผลิต")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MO-{self.id:04d} : {self.product.name} ({self.quantity})"

# ==========================================
# 12. ข้อมูลบริษัท (Global Company Info) ✅ เพิ่มใหม่
# ==========================================
class CompanyInfo(models.Model):
    name_th = models.CharField(max_length=200, verbose_name="ชื่อบริษัท (ไทย)", default="บริษัท เจซี จำกัด")
    name_en = models.CharField(max_length=200, verbose_name="ชื่อบริษัท (อังกฤษ)", blank=True)
    address = models.TextField(verbose_name="ที่อยู่บริษัท")
    tax_id = models.CharField(max_length=20, verbose_name="เลขประจำตัวผู้เสียภาษี")
    phone = models.CharField(max_length=50, verbose_name="เบอร์โทรศัพท์", blank=True)
    email = models.EmailField(verbose_name="อีเมล", blank=True)
    website = models.URLField(verbose_name="เว็บไซต์", blank=True)
    logo = models.ImageField(upload_to='company_logo/', verbose_name="โลโก้บริษัท", blank=True, null=True)

    def __str__(self):
        return self.name_th

    class Meta:
        verbose_name = "ข้อมูลบริษัท"
        verbose_name_plural = "ข้อมูลบริษัท (ตั้งค่า)"