from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import login, logout
from django.db.models import Sum, Count, F
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
# ✅ Import ครบถ้วน (เพิ่ม Supplier, StockTransaction, Forms)
from .models import Employee, Attendance, LeaveRequest, Product, Order, OrderItem, Category, Supplier, StockTransaction, PurchaseOrder, PurchaseOrderItem
from .forms import LeaveRequestForm, ProductForm, SupplierForm, PurchaseOrderForm
from django.contrib.auth.models import User

import datetime
from datetime import timedelta
import json
import requests

# ==========================================
# --- ฟังก์ชันช่วย ---
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
    LINE_TOKEN = 'R8cR4RQiDZA9sRljWNa8f6TaspfFYUxBoGaLNUAIBfaxD5iiN0jWiI2e34NAkXP36GBtALNyEk7foed2g1bdkArDqhA9NbhPeVqYqGdElngJt7+YHjdsiNv81geRXVfrKqD4UQABNNemXFfFwCW1uAdB04t89/1O/w1cDnyilFU='
    BOSS_ID = 'Ubb324ad1f45ef40d567ee70823007142'

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
# 1. Dashboard (เวอร์ชันออโต้ - รองรับทุกแผนกในอนาคต) 🚀
# ==========================================
@login_required
def dashboard(request):
    # 1. รับค่าจากปุ่มกด (ชื่อแผนกที่ส่งมา)
    view_mode = request.GET.get('view', 'all') 
    
    emp = get_employee_from_user(request.user)
    today = timezone.localtime(timezone.now()).date()
    
    # ดึงรายชื่อแผนกทั้งหมดที่มีในระบบ (เพื่อเอาไปสร้างปุ่มอัตโนมัติ)
    all_departments = Employee.objects.exclude(department__isnull=True).exclude(department__exact='').values_list('department', flat=True).distinct().order_by('department')

    # ตัวแปรควบคุมการแสดงผล
    show_sales = False
    show_hr = False
    current_dept_view = "ภาพรวมบริษัท" # ชื่อที่จะโชว์บนหัว
    
    # ตรวจสอบว่าเป็น CEO หรือไม่?
    is_ceo = request.user.username == 'jcneed1975' or request.user.is_superuser

    if is_ceo:
        # 👑 CEO Logic
        if view_mode == 'all':
            show_hr = True
            show_sales = True
            current_dept_view = "ภาพรวม (CEO Dashboard)"
        else:
            # ถ้ากดเลือกแผนกมา
            current_dept_view = f"แผนก {view_mode}"
            if view_mode == 'Human Resources': # ชื่อต้องตรงกับใน Database
                show_hr = True
            elif view_mode == 'Sales':
                show_sales = True
            # *ถ้ามีแผนก IT หรืออื่นๆ ในอนาคต ก็เพิ่มเงื่อนไขตรงนี้เพื่อโชว์กราฟเฉพาะทาง*
            
    elif emp:
        # 👔 พนักงานทั่วไป (Logic เดิม)
        dept = str(emp.department)
        if 'CEO' in emp.position or dept == 'Management':
            show_sales = True
            show_hr = True
            current_dept_view = "ผู้บริหาร"
        elif dept == 'Sales':
            show_sales = True
        elif dept == 'Human Resources':
            show_hr = True
        else:
            return redirect('employee_detail', emp_id=emp.id)

    context = {
        'role_name': "CEO / Admin" if is_ceo else emp.position,
        'current_emp_id': emp.id if emp else None,
        'today': today,
        'show_sales': show_sales,
        'show_hr': show_hr,
        'view_mode': view_mode,
        'all_departments': all_departments, # ✅ ส่งรายชื่อแผนกไปทำปุ่ม
        'current_dept_view': current_dept_view,
        
        # Default Values
        'pie_data': '[]', 'bar_labels': '[]', 'bar_data': '[]',
        'sales_chart_data': '[]', 'sales_labels': '[]',
        'top_prod_labels': '[]', 'top_prod_data': '[]',
        'total_employees': 0, 'total_salary': "0.00", 'pending_leaves': 0, 'absent_today': 0,
        'dept_summary': [], 'activities': [],
        'period_sales_amount': "0.00", 'sales_today': "0.00", 'sales_month': "0.00",
        'period_orders_count': 0, 'period_items_sold': 0, 'low_stock_count': 0, 'total_products': 0,
        'filter_start': '', 'filter_end': '',
    }

    # --- 🏢 HR Data Logic ---
    if show_hr:
        total_employees = Employee.objects.count()
        total_salary = Employee.objects.aggregate(Sum('base_allowance'))['base_allowance__sum'] or 0
        pending_leaves = LeaveRequest.objects.filter(status='PENDING').count()
        present_count = Attendance.objects.filter(date=today).count()
        absent_today = total_employees - present_count
        
        # กราฟแท่ง
        bar_labels = []
        bar_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            bar_labels.append(d.strftime('%d/%m'))
            bar_data.append(Attendance.objects.filter(date=d).count())
            
        # กราฟวงกลม
        start_work_time = datetime.time(9, 0, 0)
        late_count = Attendance.objects.filter(date=today, time_in__gt=start_work_time).count()
        on_time_count = present_count - late_count
        
        # ตารางงบประมาณ
        dept_summary = Employee.objects.values('department').annotate(
            count=Count('id'), total_salary=Sum('base_allowance')
        ).order_by('-total_salary')

        context.update({
            'total_employees': total_employees, 'total_salary': "{:,.2f}".format(total_salary),
            'pending_leaves': pending_leaves, 'absent_today': absent_today,
            'bar_labels': json.dumps(bar_labels), 'bar_data': json.dumps(bar_data),
            'pie_data': json.dumps([on_time_count, late_count, absent_today]),
            'dept_summary': dept_summary,
        })
        
        # กิจกรรม HR
        atts = Attendance.objects.filter(date=today).exclude(time_in__isnull=True)
        for a in atts:
            is_late = a.time_in > datetime.time(9, 0)
            context['activities'].append({
                'timestamp': datetime.datetime.combine(today, a.time_in),
                'time_show': a.time_in.strftime('%H:%M'),
                'icon': 'fa-fingerprint', 'color': 'text-warning' if is_late else 'text-success', 'bg': 'bg-warning-subtle' if is_late else 'bg-success-subtle',
                'title': f"{a.employee.first_name} ลงเวลา", 'detail': "⚠️ มาสาย" if is_late else "✅ ปกติ"
            })

    # --- 💰 Sales Data Logic ---
    if show_sales:
        # (ใช้ Logic เดิมในการดึงข้อมูล Sales)
        sales_start = today
        sales_end = today
        req_start = request.GET.get('sales_start')
        req_end = request.GET.get('sales_end')
        if req_start and req_end:
            try:
                sales_start = datetime.datetime.strptime(req_start, '%Y-%m-%d').date()
                sales_end = datetime.datetime.strptime(req_end, '%Y-%m-%d').date()
            except: pass
            
        context['filter_start'] = sales_start.strftime('%Y-%m-%d')
        context['filter_end'] = sales_end.strftime('%Y-%m-%d')
        
        # Query ข้อมูล
        period_sales_amount = Order.objects.filter(order_date__date__range=[sales_start, sales_end]).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        period_orders_count = Order.objects.filter(order_date__date__range=[sales_start, sales_end]).count()
        period_items_sold = OrderItem.objects.filter(order__order_date__date__range=[sales_start, sales_end]).aggregate(Sum('quantity'))['quantity__sum'] or 0
        sales_today = Order.objects.filter(order_date__date=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        sales_month = Order.objects.filter(order_date__month=today.month, order_date__year=today.year).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        low_stock_count = Product.objects.filter(stock__lte=10).count()
        total_products = Product.objects.filter(is_active=True).count()
        
        # กราฟเส้น
        sales_labels = []
        sales_chart_data = []
        delta_days = (sales_end - sales_start).days
        date_list = [sales_start + timedelta(days=i) for i in range(delta_days + 1)]
        for d in date_list:
            sales_labels.append(d.strftime('%d/%m'))
            val = Order.objects.filter(order_date__date=d).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            sales_chart_data.append(float(val))
            
        # กราฟโดนัท
        top_products = OrderItem.objects.filter(order__order_date__date__range=[sales_start, sales_end]).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]
        top_prod_labels = [item['product__name'] for item in top_products]
        top_prod_data = [item['total_qty'] for item in top_products]
        
        context.update({
            'period_sales_amount': "{:,.2f}".format(period_sales_amount), 'sales_today': "{:,.2f}".format(sales_today), 'sales_month': "{:,.2f}".format(sales_month),
            'period_orders_count': period_orders_count, 'period_items_sold': period_items_sold, 'low_stock_count': low_stock_count, 'total_products': total_products,
            'sales_labels': json.dumps(sales_labels), 'sales_chart_data': json.dumps(sales_chart_data),
            'top_prod_labels': json.dumps(top_prod_labels), 'top_prod_data': json.dumps(top_prod_data),
        })
        
        # กิจกรรม Sales
        orders = Order.objects.filter(order_date__date=today)
        for o in orders:
            context['activities'].append({
                'timestamp': o.order_date, 'time_show': timezone.localtime(o.order_date).strftime('%H:%M'),
                'icon': 'fa-cash-register', 'color': 'text-info', 'bg': 'bg-info-subtle',
                'title': f"{o.employee.first_name} ขาย (POS)", 'detail': f"💰 ฿{o.total_amount:,.0f}"
            })

    # Sort Activities
    context['activities'].sort(key=lambda x: x.get('timestamp', timezone.now()), reverse=True)
    context['activities'] = context['activities'][:10]

    return render(request, 'employees/dashboard.html', context)

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
# 5. ฟังก์ชันอื่นๆ
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
# 🛒 8. ระบบ POS (อัปเกรดแล้ว!)
# ==========================================
@login_required
def pos_home(request):
    # ✅ ดึงหมวดหมู่มาด้วย (Optimized)
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
# 📦 9. Inventory Views (ระบบจัดการคลังสินค้า) ✅ เพิ่มใหม่!
# ==========================================

@login_required
def inventory_dashboard(request):
    # รับค่าประเภทคลังจาก Link (ถ้าไม่ระบุ ให้เป็น 'FG' คือสินค้าขายก่อน)
    view_type = request.GET.get('type', 'FG')

    if view_type == 'RM':
        # 🪵 โหมดคลังวัตถุดิบ
        products = Product.objects.filter(product_type='RM').order_by('name')
        page_title = " คลังวัตถุดิบ (Raw Materials)"
        theme_color = "warning" # สีส้ม
    else:
        # 📦 โหมดคลังสินค้าขาย (Default)
        products = Product.objects.filter(product_type='FG').order_by('name')
        page_title = "คลังสินค้าสำเร็จรูป (Finished Goods)"
        theme_color = "success" # สีเขียว

    # การแจ้งเตือนสินค้าใกล้หมด (Low Stock) เฉพาะในคลังนั้นๆ
    low_stock_products = [p for p in products if p.stock <= p.alert_level]

    context = {
        'products': products,
        'low_stock_products': low_stock_products,
        'page_title': page_title,
        'theme_color': theme_color,
        'view_type': view_type, # ส่งค่าประเภทกลับไปที่หน้าจอด้วย
    }
    return render(request, 'employees/inventory_dashboard.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            # บันทึก Transaction แรกรับ (Opening Stock)
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
# 🛒 10. ระบบจัดซื้อ (Purchasing System)
# ==========================================
from .forms import PurchaseOrderForm, PurchaseItemForm

@login_required
def po_list(request):
    # แสดงรายการใบสั่งซื้อทั้งหมด
    pos = PurchaseOrder.objects.all().order_by('-created_at')
    return render(request, 'employees/po_list.html', {'pos': pos})

@login_required
def po_create(request):
    # สร้างใบสั่งซื้อใหม่ (เฉพาะหัวบิลก่อน)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            return redirect('po_detail', po_id=po.id)
    else:
        form = PurchaseOrderForm()
    return render(request, 'employees/po_form.html', {'form': form, 'title': 'เปิดใบสั่งซื้อใหม่ (Create PO)'})

@login_required
def po_detail(request, po_id):
    # หน้ารายละเอียด + เพิ่มสินค้าในบิล
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    
    # คำนวณยอดรวมใหม่ทุกครั้งที่เปิดดู
    total = sum(item.total_price for item in po.items.all())
    po.total_amount = total
    po.save()

    if request.method == 'POST':
        # ฟอร์มเพิ่มสินค้า
        form = PurchaseItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.purchase_order = po
            item.save()
            return redirect('po_detail', po_id=po.id)
    else:
        form = PurchaseItemForm()

    return render(request, 'employees/po_detail.html', {'po': po, 'form': form})

@login_required
def po_receive(request, po_id):
    # ✨ ปุ่มวิเศษ: รับของเข้าสต็อก!
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    
    if po.status != 'RECEIVED':
        # วนลูปสินค้าทุกตัวในบิล แล้วเอาไปบวกในสต็อกจริง
        for item in po.items.all():
            product = item.product
            product.stock += item.quantity # 📈 เพิ่มสต็อก
            # product.cost_price = item.unit_price # (Option: อัปเดตราคาต้นทุนล่าสุดถ้ายอมรับได้)
            product.save()
            
            # บันทึก Transaction เพื่อตรวจสอบย้อนหลัง
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

@login_required
def po_delete_item(request, item_id):
    item = get_object_or_404(PurchaseOrderItem, pk=item_id)
    po_id = item.purchase_order.id
    item.delete()
    return redirect('po_detail', po_id=po_id)

# ==========================================
# 🛒 ระบบจัดซื้อ (Purchasing System)
# ==========================================

@login_required
def po_list(request):
    # แสดงรายการใบสั่งซื้อทั้งหมด เรียงจากใหม่ไปเก่า
    orders = PurchaseOrder.objects.all().order_by('-created_at')
    return render(request, 'employees/po_list.html', {'orders': orders})

@login_required
def po_create(request):
    # สร้างใบสั่งซื้อใหม่ (Header)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            messages.success(request, f"สร้างใบสั่งซื้อ {po.po_number} แล้ว! กรุณาเพิ่มรายการสินค้า")
            return redirect('po_detail', po_id=po.id) # ไปหน้าเพิ่มสินค้าต่อเลย
    else:
        form = PurchaseOrderForm()
    return render(request, 'employees/po_form.html', {'form': form, 'title': 'เปิดใบสั่งซื้อใหม่'})

@login_required
def po_detail(request, po_id):
    # หน้ารายละเอียด PO (จุดที่ใช้เพิ่มสินค้า และกดรับของ)
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    products = Product.objects.all().order_by('name') # ดึงสินค้ามาให้เลือก

    if request.method == 'POST' and po.status == 'PENDING':
        # รับค่าจากฟอร์มเพิ่มสินค้า (แบบง่าย)
        product_id = request.POST.get('product_id')
        quantity = float(request.POST.get('quantity'))
        price = float(request.POST.get('price'))

        product = Product.objects.get(id=product_id)
        
        # บันทึกลงตารางลูก (Item)
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=product,
            quantity=quantity,
            unit_price=price
        )
        # อัปเดตยอดรวมใบสั่งซื้อ
        po.total_amount += (quantity * price)
        po.save()
        messages.success(request, f"เพิ่ม {product.name} เรียบร้อย")
        return redirect('po_detail', po_id=po.id)

    return render(request, 'employees/po_detail.html', {'po': po, 'products': products})

@login_required
def po_receive(request, po_id):
    # ฟังก์ชันสำหรับ "ลุงป้อม" กดรับของ (สำคัญมาก!)
    po = get_object_or_404(PurchaseOrder, pk=po_id)

    if po.status == 'PENDING':
        # 1. วนลูปสินค้าทุกตัวในบิล เพื่อเอาเข้าสต็อก
        for item in po.items.all():
            product = item.product
            
            # เพิ่มสต็อกจริง!
            product.stock += item.quantity 
            product.save()

            # 2. บันทึกประวัติ Transaction (Log)
            StockTransaction.objects.create(
                product=product,
                transaction_type='IN',
                quantity=item.quantity,
                price_at_time=item.unit_price,
                created_by=request.user,
                note=f"รับของจาก PO: {po.po_number}"
            )

        # 3. เปลี่ยนสถานะบิลเป็น "ได้รับแล้ว"
        po.status = 'RECEIVED'
        po.save()
        messages.success(request, f"✅ รับของเข้าคลังเรียบร้อย! (PO: {po.po_number})")
    
    return redirect('po_list')

