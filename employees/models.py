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
# 🛒 ระบบขายหน้าร้าน (POS System) - อัปเกรดใหม่!
# ==========================================

# 1. ✅ (ใหม่) ตารางหมวดหมู่สินค้า
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อหมวดหมู่")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "จัดการหมวดหมู่สินค้า (Categories)"

# 2. ตู้เก็บสินค้า (Product) - อัปเกรด
class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อสินค้า")
    
    # ✅ เชื่อมกับตารางหมวดหมู่ (Category)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="หมวดหมู่")
    
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ราคาขาย")
    stock = models.IntegerField(default=0, verbose_name="จำนวนคงเหลือ")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="รูปสินค้า")
    is_active = models.BooleanField(default=True, verbose_name="เปิดขาย")
    
    def __str__(self):
        return f"{self.name} ({self.stock})"

# 3. ตู้เก็บหัวบิล (Order)
class Order(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, verbose_name="พนักงานขาย")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="วันที่ขาย")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ยอดรวมทั้งสิ้น")
    
    def __str__(self):
        return f"Order #{self.id} by {self.employee.first_name}"

# 4. ตู้เก็บรายการในบิล (OrderItem)
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