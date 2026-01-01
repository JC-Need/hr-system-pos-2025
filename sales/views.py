from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import datetime

from employees.models import Product, Employee
from .models import Quotation, QuotationItem
from .forms import QuotationForm

@login_required
def quotation_list(request):
    qts = Quotation.objects.all().order_by('-created_at')
    return render(request, 'sales/quotation_list.html', {'qts': qts})

@login_required
def quotation_create(request):
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        if form.is_valid():
            qt = form.save(commit=False)
            qt.created_by = request.user
            if hasattr(request.user, 'employee'):
                qt.sales_person = request.user.employee

            now = datetime.datetime.now()
            prefix = f"QT-{now.strftime('%y%m')}"
            last = Quotation.objects.filter(qt_number__startswith=prefix).order_by('qt_number').last()
            seq = int(last.qt_number.split('-')[-1]) + 1 if last else 1
            qt.qt_number = f"{prefix}-{seq:03d}"

            qt.save()
            return redirect('quotation_detail', qt_id=qt.id)
    else:
        form = QuotationForm(initial={'date': timezone.now().date(), 'valid_until': timezone.now().date() + timedelta(days=7)})
    return render(request, 'sales/quotation_form.html', {'form': form})

@login_required
def quotation_detail(request, qt_id):
    qt = get_object_or_404(Quotation, pk=qt_id)
    products = Product.objects.filter(is_active=True)

    if request.method == 'POST':
        if 'add_item' in request.POST:
            p = Product.objects.get(pk=request.POST.get('product'))
            qty = int(request.POST.get('quantity'))
            price = float(request.POST.get('price'))
            QuotationItem.objects.create(quotation=qt, product=p, quantity=qty, unit_price=price)
            messages.success(request, f"เพิ่ม {p.name} แล้ว")

        elif 'save_qt' in request.POST:
            total = sum(i.total_price for i in qt.items.all())
            qt.subtotal = total
            qt.vat_amount = total * 0.07
            qt.grand_total = total + qt.vat_amount
            qt.save()

        return redirect('quotation_detail', qt_id=qt.id)

    return render(request, 'sales/quotation_detail.html', {'qt': qt, 'products': products})