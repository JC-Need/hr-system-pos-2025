from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
            'zip_code': forms.TextInput(attrs={'id': 'input_zipcode', 'class': 'form-control'}),
            
            # ✅ เพิ่มส่วนนี้: ตั้งค่าช่องเบอร์โทรศัพท์
            'phone': forms.TextInput(attrs={
                'id': 'input_phone',          # กำหนด ID ให้ Script เรียกใช้
                'class': 'form-control',
                'placeholder': '0xx-xxx-xxxx', # แสดงตัวอย่างจางๆ
                'maxlength': '12',            # จำกัดความยาว (10 ตัวเลข + 2 ขีด)
                'pattern': '[0-9]{3}-[0-9]{3}-[0-9]{4}', # บังคับรูปแบบ (Validation)
                'title': 'กรุณากรอกเบอร์โทรศัพท์ให้ครบ 10 หลัก (0xx-xxx-xxxx)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'is_active':
                existing_classes = self.fields[field].widget.attrs.get('class', '')
                self.fields[field].widget.attrs.update({'class': existing_classes + ' form-control'})
        
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input ml-2'})