from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Customer
from .forms import CustomerForm

@login_required
def customer_list(request):
    query = request.GET.get('q')
    if query:
        # ค้นหาจาก ชื่อ, รหัส, หรือ เบอร์โทร
        customers = Customer.objects.filter(
            Q(name__icontains=query) | 
            Q(code__icontains=query) |
            Q(phone__icontains=query)
        ).order_by('-created_at')
    else:
        customers = Customer.objects.all().order_by('-created_at')
    
    return render(request, 'customers/customer_list.html', {'customers': customers, 'query': query})

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            cust = form.save()
            messages.success(request, f"เพิ่มลูกค้า {cust.name} เรียบร้อย")
            return redirect('customer_list')
    else:
        # สร้างรหัสลูกค้าอัตโนมัติแบบง่ายๆ (CUS-YYMM-XXX)
        import datetime
        now = datetime.datetime.now()
        prefix = f"CUS-{now.strftime('%y%m')}"
        last = Customer.objects.filter(code__startswith=prefix).last()
        if last:
            try:
                seq = int(last.code.split('-')[-1]) + 1
            except:
                seq = 1
        else:
            seq = 1
        
        initial_data = {'code': f"{prefix}-{seq:03d}"}
        form = CustomerForm(initial=initial_data)

    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'เพิ่มลูกค้าใหม่'})

@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"อัปเดตข้อมูล {customer.name} เรียบร้อย")
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'แก้ไขข้อมูลลูกค้า'})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    messages.success(request, "ลบลูกค้าเรียบร้อย")
    return redirect('customer_list')