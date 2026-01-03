from django import forms
from .models import Quotation

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        # ✅ เพิ่ม 'customer_phone' เข้าไปในรายการ fields
        fields = ['date', 'valid_until', 'customer_name', 'customer_tax_id', 'customer_phone', 'customer_address', 'note']
        widgets = {
            'date': forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control datepicker', 'placeholder': 'dd/mm/yyyy'}),
            'valid_until': forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control datepicker', 'placeholder': 'dd/mm/yyyy'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุชื่อลูกค้า'}),
            'customer_tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เลขประจำตัวผู้เสียภาษี'}),
            # ✅ เพิ่ม Widget สำหรับเบอร์โทร
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0xx-xxx-xxxx'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }