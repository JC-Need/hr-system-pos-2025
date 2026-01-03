from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import datetime
from decimal import Decimal
from django.http import JsonResponse

# ✅ เพิ่ม imports สำคัญสำหรับการค้นหาและแบ่งหน้า
from django.core.paginator import Paginator
from django.db.models import Q

from employees.models import Product, Employee, Category
from customers.models import Customer
from .models import Quotation, QuotationItem, Province, Amphure, Tambon
from .forms import QuotationForm

# ==========================================
# 1. หน้ารายการ (List) - อัปเกรดแล้ว
# ==========================================
@login_required
def quotation_list(request):
    # 1. เริ่มต้นดึงข้อมูลทั้งหมด เรียงจากใหม่ไปเก่า
    queryset = Quotation.objects.all().order_by('-created_at')

    # 2. ระบบค้นหา (Search Logic)
    search_query = request.GET.get('q')
    if search_query:
        queryset = queryset.filter(
            Q(qt_number__icontains=search_query) |  # ค้นหาจากเลขที่
            Q(customer_name__icontains=search_query) # หรือ ค้นหาจากชื่อลูกค้า
        )

    # 3. ระบบแบ่งหน้า (Pagination)
    # แบ่งแสดงหน้าละ 10 รายการ
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sales/quotation_list.html', {
        'page_obj': page_obj,        # ส่ง object ที่แบ่งหน้าแล้วไปที่ template
        'search_query': search_query # ส่งคำที่ค้นหากลับไปแสดงค้างไว้ในช่อง
    })

# ==========================================
# 2. สร้างใบเสนอราคา (Create)
# ==========================================
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
                try:
                    seq = int(last.qt_number.split('-')[-1]) + 1
                except:
                    seq = 1
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

    customers = Customer.objects.filter(is_active=True)

    return render(request, 'sales/quotation_form.html', {
        'form': form,
        'customers': customers
    })

# ==========================================
# 3. แก้ไขใบเสนอราคา (Edit)
# ==========================================
@login_required
def quotation_edit(request, qt_id):
    qt = get_object_or_404(Quotation, pk=qt_id)
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    customers = Customer.objects.filter(is_active=True)

    item_total = sum(i.total_price for i in qt.items.all())

    if request.method == 'POST':
        # --- กรณี 1: ดึงข้อมูลลูกค้า ---
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
                qt.customer_zip = getattr(cust, 'zip_code', getattr(cust, 'postal_code', ''))

                qt.save()
                messages.success(request, f"ดึงข้อมูลลูกค้า {cust.name} เรียบร้อย")
            return redirect('quotation_edit', qt_id=qt.id)

        # --- กรณี 2: เพิ่มสินค้า ---
        elif 'add_item' in request.POST:
            try:
                p_id = request.POST.get('product')
                if p_id:
                    p = Product.objects.get(pk=p_id)
                    qty = int(request.POST.get('quantity', 1))
                    price = Decimal(request.POST.get('price', 0))

                    QuotationItem.objects.create(quotation=qt, product=p, quantity=qty, unit_price=price)
                    calculate_totals(qt)
                    messages.success(request, f"เพิ่ม {p.name} เรียบร้อย")
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาด: {e}")
            return redirect('quotation_edit', qt_id=qt.id)

        # --- กรณี 3: บันทึกหัวเอกสาร (ลูกค้า) ---
        elif 'save_header' in request.POST:
            qt.customer_name = request.POST.get('customer_name')
            qt.customer_tax_id = request.POST.get('customer_tax_id')
            qt.customer_phone = request.POST.get('customer_phone')
            qt.customer_address = request.POST.get('customer_address')
            qt.customer_sub_district = request.POST.get('customer_sub_district')
            qt.customer_district = request.POST.get('customer_district')
            qt.customer_province = request.POST.get('customer_province')
            qt.customer_zip = request.POST.get('customer_zip')
            qt.date = request.POST.get('date')
            qt.valid_until = request.POST.get('valid_until')
            qt.save()
            messages.success(request, "บันทึกข้อมูลลูกค้าเรียบร้อย")
            return redirect('quotation_edit', qt_id=qt.id)

        # --- กรณี 4: บันทึกยอดเงินท้ายบิล ---
        elif 'update_totals' in request.POST:
            try:
                discount_str = request.POST.get('discount', '0').replace(',', '')
                shipping_str = request.POST.get('shipping_cost', '0').replace(',', '')

                qt.discount = Decimal(discount_str or 0)
                qt.shipping_cost = Decimal(shipping_str or 0)
                qt.note = request.POST.get('note', '')

                calculate_totals(qt)

                # ✅ เช็คว่ากดมาจากปุ่มไหน เพื่อเปลี่ยนข้อความ
                if 'save_note' in request.POST:
                    messages.success(request, "บันทึกหมายเหตุเรียบร้อย")
                else:
                    messages.success(request, "บันทึกและคำนวณยอดเงินเรียบร้อย")

            except Exception as e:
                pass

            return redirect('quotation_edit', qt_id=qt.id)

    return render(request, 'sales/quotation_edit.html', {
        'qt': qt,
        'products': products,
        'categories': categories,
        'customers': customers,
        'item_total': item_total
    })

# ==========================================
# 4. ดูรายละเอียด / พิมพ์ (Detail)
# ==========================================
@login_required
def quotation_detail(request, qt_id):
    qt = get_object_or_404(Quotation, pk=qt_id)
    from employees.models import CompanyInfo
    company = CompanyInfo.objects.first()

    # โค้ดค้นหาลูกค้า (ที่เราเพิ่มไปก่อนหน้านี้)
    customer_obj = None
    if qt.customer_tax_id:
        customer_obj = Customer.objects.filter(tax_id=qt.customer_tax_id).first()
    if not customer_obj and qt.customer_name:
        customer_obj = Customer.objects.filter(name=qt.customer_name).first()

    # ✅ เพิ่มบรรทัดนี้: คำนวณยอดรวมสินค้า (Item Total)
    item_total = sum(i.total_price for i in qt.items.all())

    return render(request, 'sales/quotation_detail.html', {
        'qt': qt,
        'company': company,
        'customer_obj': customer_obj,
        'item_total': item_total # ✅ ส่งค่าไปที่หน้าจอ
    })

# ==========================================
# 5. ลบรายการสินค้า (Delete Item)
# ==========================================
@login_required
def delete_item(request, item_id):
    item = get_object_or_404(QuotationItem, pk=item_id)
    qt = item.quotation
    item.delete()
    calculate_totals(qt)
    messages.success(request, "ลบรายการเรียบร้อย")
    return redirect('quotation_edit', qt_id=qt.id)

# ฟังก์ชันคำนวณยอดเงินรวม
def calculate_totals(qt):
    item_sum = sum(i.total_price for i in qt.items.all())
    shipping = qt.shipping_cost if qt.shipping_cost else Decimal(0)
    discount = qt.discount if qt.discount else Decimal(0)

    grand_total = (item_sum + shipping) - discount
    if grand_total < Decimal(0):
        grand_total = Decimal(0)

    qt.subtotal = grand_total / Decimal('1.07')
    qt.vat_amount = grand_total - qt.subtotal
    qt.grand_total = grand_total
    qt.save()

# ==========================================
# 6. API Views (สำหรับ Dropdown ที่อยู่)
# ==========================================
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