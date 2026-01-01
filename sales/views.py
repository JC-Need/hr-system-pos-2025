from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import datetime
from decimal import Decimal
from django.http import JsonResponse  # ✅ 1. ต้องมีตัวนี้เพื่อส่งข้อมูลกลับ

from employees.models import Product, Employee, Category
# ✅ 2. บรรทัดนี้สำคัญที่สุด! ต้องดึงตารางที่อยู่มาใช้
from .models import Quotation, QuotationItem, Customer, Province, Amphure, Tambon
from .forms import QuotationForm

# ==========================================
# 1. ส่วนงานขาย (List / Create / Edit)
# ==========================================
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
            if last:
                seq = int(last.qt_number.split('-')[-1]) + 1
            else:
                seq = 1
            qt.qt_number = f"{prefix}-{seq:03d}"

            qt.save()
            return redirect('quotation_edit', qt_id=qt.id)
    else:
        form = QuotationForm(initial={
            'date': timezone.now().date(),
            'valid_until': timezone.now().date() + timedelta(days=7)
        })
    return render(request, 'sales/quotation_form.html', {'form': form})

@login_required
def quotation_edit(request, qt_id):
    qt = get_object_or_404(Quotation, pk=qt_id)
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    customers = Customer.objects.all()

    if request.method == 'POST':
        if 'select_customer' in request.POST:
            cust_id = request.POST.get('customer_id')
            if cust_id:
                cust = Customer.objects.get(pk=cust_id)
                qt.customer_name = cust.name
                qt.customer_tax_id = cust.tax_id
                qt.customer_phone = cust.phone
                qt.customer_address = cust.address
                qt.customer_sub_district = cust.sub_district
                qt.customer_district = cust.district
                qt.customer_province = cust.province
                qt.customer_zip = cust.postal_code
                qt.save()
                messages.success(request, f"ดึงข้อมูลลูกค้า {cust.name} เรียบร้อย")
            return redirect('quotation_edit', qt_id=qt.id)

        elif 'add_item' in request.POST:
            try:
                p = Product.objects.get(pk=request.POST.get('product'))
                qty = int(request.POST.get('quantity'))
                price = Decimal(request.POST.get('price'))
                QuotationItem.objects.create(quotation=qt, product=p, quantity=qty, unit_price=price)
                calculate_totals(qt)
                messages.success(request, f"เพิ่ม {p.name} เรียบร้อย")
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาด: {e}")
            return redirect('quotation_edit', qt_id=qt.id)

        elif 'save_header' in request.POST:
            qt.customer_name = request.POST.get('customer_name')
            qt.customer_tax_id = request.POST.get('customer_tax_id')
            qt.customer_phone = request.POST.get('customer_phone')
            qt.customer_address = request.POST.get('customer_address')
            qt.customer_sub_district = request.POST.get('customer_sub_district')
            qt.customer_district = request.POST.get('customer_district')
            qt.customer_province = request.POST.get('customer_province')
            qt.customer_zip = request.POST.get('customer_zip')
            qt.save()
            messages.success(request, "บันทึกข้อมูลลูกค้าเรียบร้อย")
            return redirect('quotation_edit', qt_id=qt.id)

    return render(request, 'sales/quotation_edit.html', {
        'qt': qt, 'products': products, 'categories': categories, 'customers': customers
    })

@login_required
def quotation_detail(request, qt_id):
    qt = get_object_or_404(Quotation, pk=qt_id)
    return render(request, 'sales/quotation_detail.html', {'qt': qt})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(QuotationItem, pk=item_id)
    qt = item.quotation
    item.delete()
    calculate_totals(qt)
    messages.success(request, "ลบรายการเรียบร้อย")
    return redirect('quotation_edit', qt_id=qt.id)

def calculate_totals(qt):
    total = sum(i.total_price for i in qt.items.all())
    qt.subtotal = total
    qt.vat_amount = total * Decimal('0.07')
    qt.grand_total = total + qt.vat_amount
    qt.save()

# ... (โค้ดอื่นๆ ด้านบน) ...

# ========================================================
# 🔌 ต้องวางส่วนนี้ไว้ล่างสุด และชิดขอบซ้าย ห้ามย่อหน้า!
# ========================================================
def get_provinces(request):
    provinces = list(Province.objects.values('id', 'name_th').order_by('name_th'))
    return JsonResponse(provinces, safe=False)

def get_amphures(request):
    p_name = request.GET.get('province')
    amphures = []
    if p_name:
        amphures = list(Amphure.objects.filter(province__name_th=p_name).values('id', 'name_th').order_by('name_th'))
    return JsonResponse(amphures, safe=False)

def get_tambons(request):
    a_name = request.GET.get('name')
    p_name = request.GET.get('province')
    tambons = []
    if a_name and p_name:
        tambons = list(Tambon.objects.filter(
            amphure__name_th=a_name,
            amphure__province__name_th=p_name
        ).values('id', 'name_th', 'zip_code').order_by('name_th'))
    return JsonResponse(tambons, safe=False)