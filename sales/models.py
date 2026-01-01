from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from employees.models import Employee, Product 

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

    customer_name = models.CharField(max_length=200, verbose_name="ชื่อลูกค้า")
    customer_address = models.TextField(blank=True, null=True, verbose_name="ที่อยู่")
    customer_tax_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="เลขผู้เสียภาษี")

    sales_person = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.qt_number

class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)