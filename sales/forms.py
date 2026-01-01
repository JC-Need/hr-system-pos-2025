from django import forms
from .models import Quotation

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['date', 'valid_until', 'customer_name', 'customer_address', 'customer_tax_id', 'note']
        widgets = {
            'date': forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control datepicker', 'placeholder': 'dd/mm/yyyy'}),
            'valid_until': forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control datepicker', 'placeholder': 'dd/mm/yyyy'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุชื่อลูกค้า'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'customer_tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }