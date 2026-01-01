from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import login, logout
from django.db.models import Sum, Count, F
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from decimal import Decimal
import datetime
from datetime import timedelta
import json
import requests

# ✅ Import Models & Forms
from .models import (
    Employee, Attendance, LeaveRequest, Product, Order, OrderItem, 
    Category, Supplier, StockTransaction, PurchaseOrder, PurchaseOrderItem, 
    BOMItem, ProductionOrder
)
from .forms import (
    LeaveRequestForm, ProductForm, SupplierForm, PurchaseOrderForm, BOMForm
)

# ==========================================
# --- ฟังก์ชันช่วย (Helpers) ---
# ==========================================
def get_employee_from_user(user):
    if hasattr(user, 'employee'):
        return user.employee
    elif hasattr(user, 'employee_profile'):
        return user.employee_profile
    return None

def is_admin(user):
    return user.is_superuser

# ==========================================
# 🤖 ฟังก์ชันส่ง LINE
# ==========================================
def send_line_alert(message, target_id=None):
    # ใส่ Token ของคุณที่นี่
    LINE_TOKEN = 'YOUR_LINE_TOKEN_HERE' 
    BOSS_ID = 'YOUR_BOSS_LINE_ID'

    if target_id is None:
        target_id = BOSS_ID

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_TOKEN}'
    }
    data = {
        'to': target_id,
        'messages': [{'type': 'text', 'text': message}]
    }

    try:
        requests.post(url, headers=headers, json=data)
    except Exception as e:
        print(f"Line Error: {e}")

# ==========================================
# 0. หน้าแรก (Login)
# ==========================================
def home(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'employees/home.html', {'form': form})

# ==========================================
# 1. Dashboard (Main Router & CEO Hub)
# ==========================================
@login_required
def dashboard(request):
    emp = get_employee_from_user(request.user)
    view_mode = request.GET.get('view', 'all')

    # --- 1. ระบบ Auto-Redirect สำหรับพนักงาน ---
    is_ceo = request.user.is_superuser or (request.user.username == 'jcneed1975')

    if not is_ceo:
        if emp:
            dept = str(emp.department)
            if dept == 'Sales': return redirect('sales_dashboard')
            elif dept == 'Human Resources': return redirect('hr_dashboard')
            elif dept == 'Purchasing': return redirect('purchasing_dashboard')
            elif dept == 'Warehouse': return redirect('inventory_dashboard')
            elif dept == 'Production': return redirect('production_dept_dashboard')
            elif dept == 'Marketing': return redirect('marketing_dashboard')
            elif dept == 'Accounting': return redirect('accounting_dashboard')
            elif dept == 'Operations': return redirect('operations_dashboard')
            elif dept not in ['Management', 'CEO']:
                return redirect('employee_detail', emp_id=emp.id)

    # --- 2. ระบบ CEO กดเลือกแผนก ---
    if view_mode == 'Sales': return redirect('sales_dashboard')
    elif view_mode == 'Human Resources': return redirect('hr_dashboard')
    elif view_mode == 'Purchasing': return redirect('purchasing_dashboard')
    elif view_mode == 'Warehouse': return redirect('inventory_dashboard')
    elif view_mode == 'Production': return redirect('production_dept_dashboard')
    elif view_mode == 'Marketing': return redirect('marketing_dashboard')
    elif view_mode == 'Accounting': return redirect('accounting_dashboard')
    elif view_mode == 'Operations': return redirect('operations_dashboard')

    # --- 3. หน้าเมนูรวม (CEO Overview) ---
    today = timezone.localtime(timezone.now()).date()
    all_departments = Employee.objects.exclude(department__isnull=True).exclude(department__exact='').values_list('department', flat=True).distinct().order_by('department')

    context = {
        'today': today,
        'all_departments': all_departments,
        'current_emp_id': emp.id if emp else None,
        'role_name': "CEO / Admin" if is_ceo else emp.position,
    }
    return render(request, 'employees/dashboard.html', context)

# ==========================================
# 📊 Sales Dashboard
# ==========================================
@login_required
def sales_dashboard(request):
    today = timezone.localtime(timezone.now()).date()
    sales_start = today
    sales_end = today
    
    req_start = request.GET.get('sales_start')
    req_end = request.GET.get('sales_end')
    if req_start and req_end:
        try:
            sales_start = datetime.datetime.strptime(req_start, '%Y-%m-%d').date()
            sales_end = datetime.datetime.strptime(req_end, '%Y-%m-%d').date()
        except: pass

    # KPIs
    period_sales = Order.objects.filter(order_date__date__range=[sales_start, sales_end]).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    period_orders = Order.objects.filter(order_date__date__range=[sales_start, sales_end]).count()
    period_items = OrderItem.objects.filter(order__order_date__date__range=[sales_start, sales_end]).aggregate(Sum('quantity'))['quantity__sum'] or 0

    # Graph
    sales_labels = []
    sales_data = []
    delta = (sales_end - sales_start).days
    for i in range(delta + 1):
        d = sales_start + timedelta(days=i)
        sales_labels.append(d.strftime('%d/%m'))
        val = Order.objects.filter(order_date__date=d).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        sales_data.append(float(val))

    top_items = OrderItem.objects.filter(order__order_date__date__range=[sales_start, sales_end]).values('product__name').annotate(qty=Sum('quantity')).order_by('-qty')[:5]
    top_labels = [i['product__name'] for i in top_items]
    top_data = [i['qty'] for i in top_items]
    recent_orders = Order.objects.filter(order_date__date=today).order_by('-order_date')[:10]

    context = {
        'today': today,
        'filter_start': sales_start.strftime('%Y-%m-%d'),
        'filter_end': sales_end.strftime('%Y-%m-%d'),
        'period_sales': "{:,.2f}".format(period_sales),
        'period_orders': period_orders,
        'period_items': period_items,
        'sales_labels': json.dumps(sales_labels),
        'sales_data': json.dumps(sales_data),
        'top_labels': json.dumps(top_labels),
        'top_data': json.dumps(top_data),
        'recent_orders': recent_orders,
    }
    return render(request, 'employees/sales_dashboard.html', context)

# ==========================================
# 🏢 HR Dashboard
# ==========================================
@login_required
def hr_dashboard(request):
    today = timezone.localtime(timezone.now()).date()
    total_emps = Employee.objects.count()
    total_salary = Employee.objects.aggregate(Sum('base_allowance'))['base_allowance__sum'] or 0
    pending_leaves = LeaveRequest.objects.filter(status='PENDING').count()

    present = Attendance.objects.filter(date=today).count()
    absent = total_emps - present
    late_count = Attendance.objects.filter(date=today, time_in__gt=datetime.time(9,0)).count()
    on_time = present - late_count

    bar_labels = []
    bar_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        bar_labels.append(d.strftime('%d/%m'))
        bar_data.append(Attendance.objects.filter(date=d).count())

    recent_atts = Attendance.objects.filter(date=today).order_by('-time_in')[:10]

    context = {
        'today': today,
        'total_emps': total_emps,
        'total_salary': "{:,.2f}".format(total_salary),
        'pending_leaves': pending_leaves,
        'absent': absent,
        'pie_data': json.dumps([on_time, late_count, absent]),
        'bar_labels': json.dumps(bar_labels),
        'bar_data': json.dumps(bar_data),
        'recent_atts': recent_atts,
    }
    return render(request, 'employees/hr_dashboard.html', context)

# ==========================================
# 2. หน้าประวัติพนักงาน
# ==========================================
@login_required
def employee_detail(request, emp_id):
    employee = get_object_or_404(Employee, pk=emp_id)
    attendance_list = Attendance.objects.filter(employee=employee).order_by('-date')
    leave_list = LeaveRequest.objects.filter(employee=employee).order_by('-start_date')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        attendance_list = attendance_list.filter(date__range=[start_date, end_date])
        leave_list = leave_list.filter(start_date__gte=start_date, start_date__lte=end_date)

    start_work_time = datetime.time(9, 0, 0)
    for att in attendance_list:
        if att.time_in:
            check_time = att.time_in
            if isinstance(check_time, datetime.datetime): check_time = check_time.time()
            if check_time > start_work_time:
                att.status_label = "มาสาย ⚠️"
                att.status_color = "warning"
            else:
                att.status_label = "ปกติ ✅"
                att.status_color = "success"
        else:
            att.status_label = "ขาดงาน ❌"
            att.status_color = "danger"

    base_bonus = 10000
    sick_count = LeaveRequest.objects.filter(employee=employee, leave_type='SICK', status='APPROVED').count()
    business_count = LeaveRequest.objects.filter(employee=employee, leave_type='BUSINESS', status='APPROVED').count()
    total_deduct = (sick_count * 500) + (business_count * 1000)
    final_bonus_val = max(0, base_bonus - total_deduct)

    return render(request, 'employees/employee_detail.html', {
        'employee': employee,
        'attendance_list': attendance_list,
        'leave_list': leave_list,
        'formatted_bonus': "{:,.2f}".format(final_bonus_val),
        'total_deduct': "{:,.0f}".format(total_deduct),
        'base_bonus': "{:,.0f}".format(base_bonus),
        'sick_count': sick_count,
        'sick_deduct': "{:,.0f}".format(sick_count * 500),
        'business_count': business_count,
        'business_deduct': "{:,.0f}".format(business_count * 1000),
        'filter_start': start_date,
        'filter_end': end_date,
    })

# ==========================================
# 3. ระบบลางาน
# ==========================================
@login_required
def leave_create(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            emp = get_employee_from_user(request.user)
            if emp:
                leave.employee = emp
                leave.save()
                try:
                    msg = f"🔔 มีคำขอลาใหม่!\nคุณ: {emp.first_name} {emp.last_name}\nประเภท: {leave.leave_type}\nวันที่: {leave.start_date} ถึง {leave.end_date}\nเหตุผล: {leave.reason}"
                    send_line_alert(msg)
                except: pass
                messages.success(request, 'ส่งใบลาเรียบร้อยแล้ว')
                return redirect('employee_detail', emp_id=emp.id)
    else:
        form = LeaveRequestForm()
    return render(request, 'employees/leave_form.html', {'form': form})

# ==========================================
# 4. ฟังก์ชันจัดการของ Admin
# ==========================================
@login_required
@user_passes_test(is_admin)
def leave_approval(request):
    leaves = LeaveRequest.objects.filter(status='PENDING').order_by('-created_at')
    return render(request, 'employees/leave_approval.html', {'leaves': leaves})

@login_required
@user_passes_test(is_admin)
def approve_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, pk=leave_id)
    leave.status = 'APPROVED'
    leave.save()
    try:
        if leave.employee.line_user_id:
            msg = f"✅ อนุมัติแล้ว!\n------------------\nถึง: {leave.employee.first_name}\nวันที่ลา: {leave.start_date}"
            send_line_alert(msg, leave.employee.line_user_id)
    except: pass
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
def reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, pk=leave_id)
    leave.status = 'REJECTED'
    leave.save()
    try:
        if leave.employee.line_user_id:
            msg = f"❌ ไม่อนุมัติ\n------------------\nถึง: {leave.employee.first_name}\nโปรดติดต่อหัวหน้างาน"
            send_line_alert(msg, leave.employee.line_user_id)
    except: pass
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
def calculate_bonus(request):
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
def delete_employee(request, emp_id):
    emp = get_object_or_404(Employee, pk=emp_id)
    emp.delete()
    return redirect('dashboard')

# ==========================================
# 5. ฟังก์ชันอื่นๆ (Payslip, Attendance, Dept)
# ==========================================
@login_required
def employee_payslip(request, emp_id):
    employee = get_object_or_404(Employee, pk=emp_id)
    salary = float(employee.base_allowance)
    sso_val = min(salary * 0.05, 750.0)
    total_income = salary
    net_salary = total_income - sso_val
    return render(request, 'employees/payslip.html', {
        'employee': employee,
        'salary': "{:,.2f}".format(salary),
        'total_income': "{:,.2f}".format(total_income),
        'sso': "{:,.2f}".format(sso_val),
        'net_salary': "{:,.2f}".format(net_salary),
        'today': timezone.now(),
    })

@login_required
def attendance_action(request, emp_id):
    employee = get_object_or_404(Employee, pk=emp_id)
    now_local = timezone.localtime(timezone.now())
    today = now_local.date()
    now_time = now_local.time()

    attendance, created = Attendance.objects.get_or_create(employee=employee, date=today)

    if not attendance.time_in:
        attendance.time_in = now_time
    elif not attendance.time_out:
        attendance.time_out = now_time

    attendance.save()
    return redirect('employee_detail', emp_id=emp_id)

@login_required
def department_detail(request, dept_name):
    employees = Employee.objects.filter(department=dept_name)
    return render(request, 'employees/department_detail.html', {'dept_name': dept_name, 'employees': employees})

# ==========================================
# 6. Webhook
# ==========================================
@csrf_exempt
def line_webhook(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            print("Webhook Payload:", payload)
        except: pass
        return HttpResponse("OK", status=200)
    return HttpResponse("Line Webhook", status=200)

# ==========================================
# 7. User Management
# ==========================================
@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('id')
    return render(request, 'employees/user_list.html', {'users': users})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
@user_passes_test(is_admin)
def admin_reset_password(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = SetPasswordForm(target_user)
    return render(request, 'employees/password_reset.html', {'form': form, 'target_user': target_user})

# ==========================================
# 🛒 8. ระบบ POS
# ==========================================
@login_required
def pos_home(request):
    products = Product.objects.filter(is_active=True, stock__gt=0).select_related('category')
    categories = Category.objects.all()
    return render(request, 'employees/pos.html', {
        'products': products,
        'categories': categories
    })

@login_required
def pos_checkout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart', [])
            total_amount = data.get('total_amount', 0)
            emp = get_employee_from_user(request.user)
            order = Order.objects.create(employee=emp, total_amount=total_amount)

            for item in cart:
                product = Product.objects.get(id=item['id'])
                quantity = item['quantity']
                if product.stock >= quantity:
                    OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)
                    product.stock -= quantity
                    product.save()
            return JsonResponse({'success': True, 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid Request'})

# ==========================================
# 📦 9. Inventory Views (จัดการคลังสินค้า)
# ==========================================
@login_required
def inventory_dashboard(request):
    view_type = request.GET.get('type', 'FG')

    if view_type == 'RM':
        products = Product.objects.filter(product_type='RM').order_by('name')
        page_title = "คลังวัตถุดิบ (Raw Materials)"
        theme_color = "warning"
        bg_gradient = "linear-gradient(135deg, #f6c23e 0%, #dda20a 100%)"
        icon = "fa-layer-group"
    else:
        products = Product.objects.filter(product_type='FG').order_by('name')
        page_title = "คลังสินค้าสำเร็จรูป (Finished Goods)"
        theme_color = "success"
        bg_gradient = "linear-gradient(135deg, #1cc88a 0%, #13855c 100%)"
        icon = "fa-box-open"

    total_items = products.count()
    low_stock_items = [p for p in products if p.stock <= 10]
    low_stock_count = len(low_stock_items)
    total_value = sum(p.stock * p.price for p in products)

    recent_transactions = StockTransaction.objects.filter(product__product_type=view_type).order_by('-created_at')[:20]
    categories = Category.objects.all()

    context = {
        'products': products,
        'view_type': view_type,
        'page_title': page_title,
        'theme_color': theme_color,
        'bg_gradient': bg_gradient,
        'icon': icon,
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'total_value': total_value,
        'recent_transactions': recent_transactions,
        'categories': categories,
    }
    return render(request, 'employees/inventory_dashboard.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            if product.stock > 0:
                StockTransaction.objects.create(
                    product=product,
                    transaction_type='IN',
                    quantity=product.stock,
                    price_at_time=product.cost_price,
                    created_by=request.user,
                    note="สินค้าตั้งต้น (Initial Stock)"
                )
            return redirect('inventory_dashboard')
    else:
        form = ProductForm()
    return render(request, 'employees/product_form.html', {'form': form, 'title': 'เพิ่มสินค้าใหม่'})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('inventory_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'employees/product_form.html', {'form': form, 'title': f'แก้ไข: {product.name}'})

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'employees/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'employees/product_form.html', {'form': form, 'title': 'เพิ่มซัพพลายเออร์'})

# ==========================================
# 🛒 10. ระบบจัดซื้อ & Dashboard
# ==========================================
@login_required
def purchasing_dashboard(request):
    total_spend = PurchaseOrder.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_pos = PurchaseOrder.objects.filter(status='PENDING').count()
    low_stock_rm = Product.objects.filter(product_type='RM', stock__lte=10).order_by('stock')[:5]
    low_stock_fg = Product.objects.filter(product_type='FG', stock__lte=10).order_by('stock')[:5]
    recent_orders = PurchaseOrder.objects.all().order_by('-created_at')[:5]

    context = {
        'total_spend': total_spend,
        'pending_pos': pending_pos,
        'low_stock_rm': low_stock_rm,
        'low_stock_fg': low_stock_fg,
        'recent_orders': recent_orders,
    }
    return render(request, 'employees/purchasing_dashboard.html', context)

@login_required
def po_list(request):
    orders = PurchaseOrder.objects.all().order_by('-created_at')
    return render(request, 'employees/po_list.html', {'orders': orders})

@login_required
def po_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            messages.success(request, f"สร้างใบสั่งซื้อ {po.po_number} แล้ว! กรุณาเพิ่มรายการสินค้า")
            return redirect('po_detail', po_id=po.id)
    else:
        form = PurchaseOrderForm()
    return render(request, 'employees/po_form.html', {'form': form, 'title': 'เปิดใบสั่งซื้อใหม่'})

@login_required
def po_detail(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    products = Product.objects.all().order_by('name')

    if request.method == 'POST' and po.status == 'PENDING':
        product_id = request.POST.get('product_id')
        quantity = float(request.POST.get('quantity'))
        price = float(request.POST.get('price'))

        product = Product.objects.get(id=product_id)

        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=product,
            quantity=quantity,
            unit_price=price
        )
        po.total_amount += (quantity * price)
        po.save()
        messages.success(request, f"เพิ่ม {product.name} เรียบร้อย")
        return redirect('po_detail', po_id=po.id)

    return render(request, 'employees/po_detail.html', {'po': po, 'products': products})

@login_required
def po_receive(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)

    if po.status == 'PENDING':
        for item in po.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

            StockTransaction.objects.create(
                product=product,
                transaction_type='IN',
                quantity=item.quantity,
                price_at_time=item.unit_price,
                created_by=request.user,
                note=f"รับของจาก PO: {po.po_number}"
            )

        po.status = 'RECEIVED'
        po.save()
        messages.success(request, f"✅ รับของเข้าคลังเรียบร้อย! (PO: {po.po_number})")

    return redirect('po_list')

# ==========================================
# 🏭 11. ระบบผลิต (Manufacturing System)
# ==========================================
@login_required
def manufacturing_dashboard(request):
    pending_orders = ProductionOrder.objects.filter(status='PENDING').count()
    in_progress_orders = ProductionOrder.objects.filter(status='IN_PROGRESS').count()
    completed_today = ProductionOrder.objects.filter(status='COMPLETED', updated_at__date=timezone.now().date()).count()
    orders = ProductionOrder.objects.all().order_by('-created_at')
    producible_products = Product.objects.filter(product_type='FG', bom_items__isnull=False).distinct()
    all_fgs = Product.objects.filter(product_type='FG')
    all_rms = Product.objects.filter(product_type='RM')
    all_categories = Category.objects.all()

    context = {
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_today': completed_today,
        'orders': orders,
        'producible_products': producible_products,
        'all_fgs': all_fgs,
        'all_rms': all_rms,
        'all_categories': all_categories,
    }
    return render(request, 'employees/manufacturing_dashboard.html', context)

@login_required
def mo_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id)

        now = datetime.datetime.now()
        thai_year = (now.year + 543) % 100
        month = now.strftime('%m')
        prefix = f"JOB{thai_year}{month}"

        last_job = ProductionOrder.objects.filter(job_number__startswith=prefix).order_by('job_number').last()

        if last_job and last_job.job_number:
            try:
                last_seq = int(last_job.job_number[-3:])
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1

        new_job_number = f"{prefix}{new_seq:03d}"

        ProductionOrder.objects.create(
            job_number=new_job_number,
            product=product,
            quantity=quantity,
            created_by=request.user,
            status='PENDING',
            note="สั่งผลิตผ่าน Dashboard"
        )

        messages.success(request, f"✅ เปิดใบงาน {new_job_number} สำเร็จ!")
        return redirect('manufacturing_dashboard')

    return redirect('manufacturing_dashboard')

@login_required
def mo_complete(request, mo_id):
    mo = get_object_or_404(ProductionOrder, pk=mo_id)

    if mo.status == 'COMPLETED':
        messages.warning(request, "ใบงานนี้ผลิตเสร็จไปแล้ว!")
        return redirect('manufacturing_dashboard')

    bom_items = BOMItem.objects.filter(finished_good=mo.product)

    if not bom_items.exists():
        messages.error(request, f"❌ ไม่พบสูตรการผลิตสำหรับ {mo.product.name} กรุณาตั้งค่า BOM ในหน้า Admin ก่อน")
        return redirect('manufacturing_dashboard')

    for item in bom_items:
        required_qty = item.quantity * mo.quantity
        if item.raw_material.stock < required_qty:
            messages.error(request, f"❌ วัตถุดิบไม่พอ! ({item.raw_material.name} ขาด {required_qty - item.raw_material.stock})")
            return redirect('manufacturing_dashboard')

    for item in bom_items:
        required_qty = item.quantity * mo.quantity
        item.raw_material.stock -= required_qty
        item.raw_material.save()

        StockTransaction.objects.create(
            product=item.raw_material,
            transaction_type='OUT',
            quantity=required_qty,
            created_by=request.user,
            note=f"ใช้ผลิต {mo.product.name} (MO-{mo.id})"
        )

    mo.product.stock += mo.quantity
    mo.product.save()

    StockTransaction.objects.create(
        product=mo.product,
        transaction_type='IN',
        quantity=mo.quantity,
        created_by=request.user,
        note=f"ผลิตเสร็จสิ้น (MO-{mo.id})"
    )

    mo.status = 'COMPLETED'
    mo.updated_at = timezone.now()
    mo.save()

    messages.success(request, f"🎉 ผลิตเสร็จสิ้น! ได้รับ {mo.product.name} {mo.quantity} ชิ้น")
    return redirect('manufacturing_dashboard')

@login_required
def mo_delete(request, mo_id):
    mo = get_object_or_404(ProductionOrder, pk=mo_id)
    if mo.status == 'COMPLETED':
        messages.error(request, "ไม่สามารถลบงานที่ผลิตเสร็จแล้วได้ (สต็อกตัดไปแล้ว)")
    else:
        mo.delete()
        messages.success(request, "ลบใบสั่งผลิตเรียบร้อย")
    return redirect('manufacturing_dashboard')

@login_required
def quick_create_product(request, p_type):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price', 0)
        stock = request.POST.get('stock', 0)

        Product.objects.create(
            name=name,
            category_id=category_id if category_id else None,
            price=price,
            stock=stock,
            product_type=p_type,
            is_active=True
        )
        type_name = "สินค้า (FG)" if p_type == 'FG' else "วัตถุดิบ (RM)"
        messages.success(request, f"✅ สร้าง {type_name}: {name} เรียบร้อย!")

    return redirect('manufacturing_dashboard')

@login_required
def quick_create_bom(request):
    if request.method == 'POST':
        finished_good_id = request.POST.get('finished_good')
        finished_good = get_object_or_404(Product, pk=finished_good_id)

        rm_ids = request.POST.getlist('raw_material[]')
        quantities = request.POST.getlist('quantity[]')

        saved_count = 0

        for i in range(len(rm_ids)):
            rm_id = rm_ids[i]
            qty = quantities[i]

            if rm_id and float(qty) > 0:
                raw_material = Product.objects.get(pk=rm_id)
                BOMItem.objects.create(
                    finished_good=finished_good,
                    raw_material=raw_material,
                    quantity=qty
                )
                saved_count += 1

        if saved_count > 0:
            messages.success(request, f"✅ บันทึกสูตรสำหรับ '{finished_good.name}' เรียบร้อย ({saved_count} วัตถุดิบ)")
        else:
            messages.warning(request, "⚠️ ไม่มีการบันทึกข้อมูล (กรุณาเลือกวัตถุดิบ)")

    return redirect('manufacturing_dashboard')

@login_required
def production_dept_dashboard(request):
    today = timezone.localtime(timezone.now()).date()

    prod_emps = Employee.objects.filter(department='Production')
    prod_total = prod_emps.count()
    prod_present = Attendance.objects.filter(date=today, employee__department='Production').count()
    prod_absent = prod_total - prod_present
    absent_employees = prod_emps.exclude(id__in=Attendance.objects.filter(date=today).values('employee_id'))

    jobs_pending = ProductionOrder.objects.filter(status='PENDING').count()
    jobs_wip = ProductionOrder.objects.filter(status='IN_PROGRESS').count()
    jobs_done_today = ProductionOrder.objects.filter(status='COMPLETED', updated_at__date=today).count()
    recent_jobs = ProductionOrder.objects.all().order_by('-updated_at')[:10]

    low_materials = Product.objects.filter(product_type='RM', stock__lte=10)
    low_material_count = low_materials.count()

    context = {
        'today': today,
        'prod_total': prod_total,
        'prod_present': prod_present,
        'prod_absent': prod_absent,
        'absent_employees': absent_employees,
        'jobs_pending': jobs_pending,
        'jobs_wip': jobs_wip,
        'jobs_done_today': jobs_done_today,
        'recent_jobs': recent_jobs,
        'low_materials': low_materials,
        'low_material_count': low_material_count,
    }
    return render(request, 'employees/production_dept_dashboard.html', context)

# ==========================================
# 📣 12. Marketing Dashboard (ฝ่ายการตลาด)
# ==========================================
@login_required
def marketing_dashboard(request):
    today = timezone.localtime(timezone.now()).date()

    # Mock Data
    ad_budget_used = 15000
    total_leads = 350
    conversion_rate = 12.5
    roi_percent = 320

    lead_labels = [(today - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    lead_data = [45, 50, 38, 60, 55, 42, 60]

    channel_labels = ['Facebook', 'TikTok', 'Google', 'LINE OA', 'Walk-in']
    channel_data = [50, 25, 10, 10, 5]

    active_campaigns = [
        {'name': '🔥 Promotion 10.10 ลดจัดหนัก', 'platform': 'Facebook', 'status': 'Running', 'budget': 5000, 'leads': 120, 'cpl': 41.6},
        {'name': '🎥 คลิปไวรัล: เบื้องหลังการผลิต', 'platform': 'TikTok', 'status': 'Running', 'budget': 2000, 'leads': 85, 'cpl': 23.5},
        {'name': '🔍 Search: รับผลิตสินค้า OEM', 'platform': 'Google', 'status': 'Learning', 'budget': 3000, 'leads': 15, 'cpl': 200.0},
    ]

    recent_activities = [
        {'time': '10:30', 'icon': 'fa-comment-dots', 'title': 'Inbox ใหม่ (FB)', 'detail': 'คุณสมชาย สอบถามราคาส่ง'},
        {'time': '10:15', 'icon': 'fa-thumbs-up', 'title': 'ยอดไลก์พุ่ง!', 'detail': 'โพสต์ "กาแฟลาเต้" ถึง 1,000 ไลก์'},
        {'time': '09:45', 'icon': 'fa-file-invoice-dollar', 'title': 'ปิดการขายสำเร็จ', 'detail': 'แอดมินส้ม ปิดยอด ฿5,500 ผ่าน LINE'},
    ]

    context = {
        'today': today,
        'ad_budget_used': "{:,.0f}".format(ad_budget_used),
        'total_leads': total_leads,
        'conversion_rate': conversion_rate,
        'roi_percent': roi_percent,
        'lead_labels': json.dumps(lead_labels),
        'lead_data': json.dumps(lead_data),
        'channel_labels': json.dumps(channel_labels),
        'channel_data': json.dumps(channel_data),
        'active_campaigns': active_campaigns,
        'recent_activities': recent_activities,
    }
    return render(request, 'employees/marketing_dashboard.html', context)

# ==========================================
# 💰 13. Accounting Dashboard (ฝ่ายบัญชี)
# ==========================================
@login_required
def accounting_dashboard(request):
    today = timezone.localtime(timezone.now()).date()

    # Mock Data
    cash_on_hand = 1500000
    cash_in_month = 450000
    cash_out_month = 280000
    net_profit = cash_in_month - cash_out_month
    total_ar = 320000
    total_ap = 180000

    chart_labels = ['ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.', 'ม.ค.']
    income_data = [300000, 350000, 320000, 400000, 420000, 450000]
    expense_data = [200000, 220000, 210000, 250000, 260000, 280000]

    recent_invoices = [
        {'no': 'INV-2601001', 'customer': 'บจก. กาแฟดี', 'amount': 15000, 'due': '2026-01-15', 'status': 'Pending'},
        {'no': 'INV-2601002', 'customer': 'ร้านป้าสมร', 'amount': 5500, 'due': '2026-01-18', 'status': 'Overdue'},
    ]

    recent_bills = [
        {'no': 'PO-2601005', 'supplier': 'โรงคั่วกาแฟหอม', 'amount': 25000, 'due': '2026-01-20', 'status': 'Unpaid'},
        {'no': 'PO-2601006', 'supplier': 'Office Mate', 'amount': 3200, 'due': '2026-01-22', 'status': 'Unpaid'},
    ]

    context = {
        'today': today,
        'cash_on_hand': "{:,.2f}".format(cash_on_hand),
        'net_profit': "{:,.2f}".format(net_profit),
        'total_ar': "{:,.2f}".format(total_ar),
        'total_ap': "{:,.2f}".format(total_ap),
        'chart_labels': json.dumps(chart_labels),
        'income_data': json.dumps(income_data),
        'expense_data': json.dumps(expense_data),
        'recent_invoices': recent_invoices,
        'recent_bills': recent_bills,
    }
    return render(request, 'employees/accounting_dashboard.html', context)

# ==========================================
# ⚙️ 14. Operations Dashboard (ฝ่ายปฏิบัติการ)
# ==========================================
@login_required
def operations_dashboard(request):
    today = timezone.localtime(timezone.now()).date()

    # 1. Production Overview
    active_jobs = ProductionOrder.objects.filter(status__in=['PENDING', 'IN_PROGRESS']).count()
    completed_today = ProductionOrder.objects.filter(status='COMPLETED', updated_at__date=today).count()
    daily_target = 10
    production_progress = min(int((completed_today / daily_target) * 100), 100)

    # 2. Inventory Health
    all_products = Product.objects.all()
    inventory_value = sum(p.stock * p.price for p in all_products)
    low_stock_items = Product.objects.filter(stock__lte=10).count()

    # 3. Supply Chain
    pending_po_count = PurchaseOrder.objects.filter(status='PENDING').count()

    # 4. Quality Control (Mock)
    qc_stats = {
        'pass_rate': 98.5,
        'defect_count': 3,
        'last_incident': 'รอยขีดข่วน (Job-6812001)'
    }

    # 5. Maintenance (Mock)
    machines = [
        {'name': 'CNC-01', 'status': 'Running', 'uptime': '99%'},
        {'name': 'CNC-02', 'status': 'Maintenance', 'uptime': '85%'},
        {'name': 'Assembly-A', 'status': 'Running', 'uptime': '100%'},
    ]

    context = {
        'today': today,
        'active_jobs': active_jobs,
        'completed_today': completed_today,
        'daily_target': daily_target,
        'production_progress': production_progress,
        'inventory_value': "{:,.2f}".format(inventory_value),
        'low_stock_items': low_stock_items,
        'pending_po_count': pending_po_count,
        'qc_stats': qc_stats,
        'machines': machines,
    }
    return render(request, 'employees/operations_dashboard.html', context)