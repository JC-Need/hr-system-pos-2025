from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from employees.models import Employee, Product

# ==========================================
# 🇹🇭 1. ตารางคลังข้อมูลที่อยู่ (Master Data)
# ==========================================
class Province(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name_th = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)

    def __str__(self):
        return self.name_th

class Amphure(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='amphures')
    code = models.CharField(max_length=10)
    name_th = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)

    def __str__(self):
        return self.name_th

class Tambon(models.Model):
    amphure = models.ForeignKey(Amphure, on_delete=models.CASCADE, related_name='tambons')
    zip_code = models.CharField(max_length=10)
    name_th = models.CharField(max_length=150)
    name_en = models.CharField(max_length=150)

    def __str__(self):
        return self.name_th

# ==========================================
# 👥 2. ตารางฐานข้อมูลลูกค้า (CRM)
# ==========================================
class Customer(models.Model):
    # ข้อมูลหลัก
    name = models.CharField(max_length=200, verbose_name="ชื่อลูกค้า / ชื่อบริษัท")
    branch = models.CharField(max_length=100, blank=True, null=True, default="สำนักงานใหญ่", verbose_name="สาขา")
    tax_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="เลขผู้เสียภาษี")
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="ชื่อผู้ติดต่อ")

    # ที่อยู่ละเอียด
    address = models.CharField(max_length=255, verbose_name="ที่อยู่ (เลขที่/หมู่บ้าน/ถนน/ซอย)", blank=True, null=True)
    sub_district = models.CharField(max_length=100, verbose_name="ตำบล/แขวง", blank=True, null=True)
    district = models.CharField(max_length=100, verbose_name="อำเภอ/เขต", blank=True, null=True)
    province = models.CharField(max_length=100, verbose_name="จังหวัด", blank=True, null=True)
    postal_code = models.CharField(max_length=10, verbose_name="รหัสไปรษณีย์", blank=True, null=True)

    # การตลาด
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    email = models.EmailField(blank=True, null=True, verbose_name="อีเมล")
    line_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Line ID")
    facebook = models.CharField(max_length=100, blank=True, null=True, verbose_name="Facebook")
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ/ความสนใจ")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.province})"

    @property
    def full_address(self):
        parts = [self.address, self.sub_district, self.district, self.province, self.postal_code]
        return " ".join([p for p in parts if p])

    class Meta:
        verbose_name = "ฐานข้อมูลลูกค้า"
        verbose_name_plural = "ฐานข้อมูลลูกค้า (Customers)"

# ==========================================
# 📄 3. ใบเสนอราคา (Quotation)
# ==========================================
class Quotation(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'ร่างเอกสาร'),
        ('SENT', 'ส่งให้ลูกค้าแล้ว'),
        ('APPROVED', 'อนุมัติ/สั่งซื้อแล้ว'),
        ('REJECTED', 'ปฏิเสธ'),
    ]

    qt_number = models.CharField(max_length=20, unique=True, verbose_name="เลขที่ QT")
    date = models.DateField(default=timezone.now, verbose_name="วันที่")
    valid_until = models.DateField(verbose_name="ยืนยันราคาถึง")

    # ข้อมูลลูกค้าในใบเสนอราคา
    customer_name = models.CharField(max_length=200, verbose_name="ชื่อลูกค้า")
    customer_tax_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="เลขผู้เสียภาษี")
    customer_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    
    # ที่อยู่แยกส่วน
    customer_address = models.CharField(max_length=255, verbose_name="ที่อยู่ (เลขที่/หมู่บ้าน)", blank=True, null=True)
    customer_sub_district = models.CharField(max_length=100, verbose_name="ตำบล/แขวง", blank=True, null=True)
    customer_district = models.CharField(max_length=100, verbose_name="อำเภอ/เขต", blank=True, null=True)
    customer_province = models.CharField(max_length=100, verbose_name="จังหวัด", blank=True, null=True)
    customer_zip = models.CharField(max_length=10, verbose_name="รหัสไปรษณีย์", blank=True, null=True)

    sales_person = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # ✅ เพิ่ม 2 บรรทัดนี้ (ค่าขนส่ง และ ส่วนลด)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="ค่าขนส่ง")
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="ส่วนลด")

    # ตัวเลขคำนวณ
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.qt_number
        
    @property
    def full_address_display(self):
        parts = [
            self.customer_address,
            f"ต.{self.customer_sub_district}" if self.customer_sub_district else "",
            f"อ.{self.customer_district}" if self.customer_district else "",
            f"จ.{self.customer_province}" if self.customer_province else "",
            self.customer_zip,
            f"(โทร: {self.customer_phone})" if self.customer_phone else ""
        ]
        return " ".join([p for p in parts if p])

class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)