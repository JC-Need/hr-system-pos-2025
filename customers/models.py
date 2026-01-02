from django.db import models

class Customer(models.Model):
    # --- ข้อมูลพื้นฐาน ---
    code = models.CharField(max_length=20, unique=True, verbose_name="รหัสลูกค้า", help_text="เช่น CUS-001")
    name = models.CharField(max_length=200, verbose_name="ชื่อลูกค้า / บริษัท")
    branch = models.CharField(max_length=100, default="สำนักงานใหญ่", blank=True, verbose_name="สาขา")
    tax_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="เลขผู้เสียภาษี")
    
    # --- การติดต่อ ---
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="ชื่อผู้ติดต่อ")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    email = models.EmailField(blank=True, null=True, verbose_name="อีเมล")
    line_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Line ID")
    
    # --- ที่อยู่ (แยกส่วนเพื่อความละเอียด) ---
    address = models.CharField(max_length=255, verbose_name="ที่อยู่ (เลขที่/หมู่บ้าน/ถนน)")
    sub_district = models.CharField(max_length=100, blank=True, null=True, verbose_name="ตำบล/แขวง")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="อำเภอ/เขต")
    province = models.CharField(max_length=100, blank=True, null=True, verbose_name="จังหวัด")
    zip_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="รหัสไปรษณีย์")
    
    # --- อื่นๆ ---
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="วงเงินเครดิต")
    credit_term = models.IntegerField(default=0, verbose_name="เครดิต (วัน)")
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    is_active = models.BooleanField(default=True, verbose_name="สถานะใช้งาน")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ลูกค้า"
        verbose_name_plural = "ฐานข้อมูลลูกค้า"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_address(self):
        # รวมที่อยู่เป็นข้อความเดียวสวยๆ
        parts = [self.address, self.sub_district, self.district, self.province, self.zip_code]
        return " ".join([p for p in parts if p])