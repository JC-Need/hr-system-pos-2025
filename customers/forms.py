from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
            'zip_code': forms.TextInput(attrs={'id': 'input_zipcode', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'id': 'input_phone',
                'class': 'form-control',
                'placeholder': '0xx-xxx-xxxx',
                'maxlength': '12'
            }),
            # ✅ เพิ่มส่วนนี้: ช่อง Location
            'location': forms.TextInput(attrs={
                'id': 'input_location',
                'class': 'form-control',
                'placeholder': 'เช่น 13.7563, 100.5018 หรือ ลิงก์ Google Maps'
            }),
        }

    # ... (ส่วน __init__ เหมือนเดิม) ...
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'is_active':
                existing_classes = self.fields[field].widget.attrs.get('class', '')
                self.fields[field].widget.attrs.update({'class': existing_classes + ' form-control'})
        
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input ml-2'})