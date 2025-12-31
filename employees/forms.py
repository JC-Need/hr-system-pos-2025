from django import forms
from .models import Employee, Attendance, LeaveRequest, Product, Supplier, PurchaseOrder, PurchaseOrderItem, BOMItem

# ==========================================
# 🏖️ ฟอร์มใบลา (Leave Form) - ของเดิม
# ==========================================
class LeaveRequestForm(forms.ModelForm):
    start_date = forms.DateField(
        label='ลาตั้งแต่วันที่',
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'วว/ดด/ปปปป'})
    )
    end_date = forms.DateField(
        label='ถึงวันที่',
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'วว/ดด/ปปปป'})
    )

    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'เช่น ไม่สบาย, ไปทำธุระ...'}),
        }
        labels = {
            'leave_type': 'ประเภทการลา',
            'reason': 'เหตุผลการลา',
        }

# ==========================================
# 📦 ฟอร์มสินค้าและสต็อก (Inventory Forms) - ✅ ใหม่!
# ==========================================

# 1. ฟอร์มเพิ่ม/แก้ไขสินค้า (Product Form)
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'product_type', 'supplier', 'cost_price', 'price', 'stock', 'alert_level', 'barcode', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อสินค้า'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'รหัสบาร์โค้ด (ถ้ามี)'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'alert_level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'ชื่อสินค้า',
            'category': 'หมวดหมู่',
            'barcode': 'รหัสบาร์โค้ด',
            'cost_price': 'ราคาทุน (Cost)',
            'price': 'ราคาขาย (Price)',
            'stock': 'จำนวนสต็อกเริ่มต้น',
            'alert_level': 'เตือนเมื่อต่ำกว่า',
            'supplier': 'ซัพพลายเออร์',
            'image': 'รูปสินค้า',
            'is_active': 'เปิดขายทันที',
        }

# 2. ฟอร์มเพิ่มซัพพลายเออร์ (Supplier Form)
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'phone', 'line_id', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อบริษัท / ร้านค้า'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อผู้ติดต่อ'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เบอร์โทรศัพท์'}),
            'line_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Line ID'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ที่อยู่'}),
        }

# ✅ ฟอร์มใบสั่งซื้อ (Purchase Order)
class PurchaseOrderForm(forms.ModelForm):
    # กำหนดฟอร์แมตวันที่เอง (รับค่าเป็น วัน/เดือน/ปี)
    order_date = forms.DateField(
        label="วันที่สั่ง",
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'dd/mm/yyyy'})
    )

    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'order_date', 'note']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ระบุหมายเหตุ (ถ้ามี)'}),
        }

# ✅ ฟอร์มเพิ่มสินค้าในบิล (Item)
class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# --- ฟอร์มสำหรับระบบผลิต ---
class BOMForm(forms.ModelForm):
    class Meta:
        model = BOMItem
        fields = ['finished_good', 'raw_material', 'quantity']
        widgets = {
            'finished_good': forms.Select(attrs={'class': 'form-select'}),
            'raw_material': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.1', 'step': '0.1'}),
        }
