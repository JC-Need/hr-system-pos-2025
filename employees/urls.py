from django.urls import path
from . import views

urlpatterns = [
    # 🏠 1. หน้าแรก (Landing Page)
    path('', views.home, name='home'),

    # 📊 2. หน้า Dashboard รวม (CEO/HR/Sales)
    path('dashboard/', views.dashboard, name='dashboard'),

    # 3. หน้าประวัติ & สลิปเงินเดือน
    path('employee/<int:emp_id>/', views.employee_detail, name='employee_detail'),
    path('employee/<int:emp_id>/payslip/', views.employee_payslip, name='employee_payslip'),

    # 4. ระบบลา (Leave System)
    path('leave/create/', views.leave_create, name='leave_create'),
    path('leave/approval/', views.leave_approval, name='leave_approval'),
    path('leave/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('leave/reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),

    # 5. คำนวณโบนัส
    path('bonus/calculate/', views.calculate_bonus, name='calculate_bonus'),

    # 6. ฟังก์ชันจัดการพนักงาน & การลงเวลา
    path('employee/delete/<int:emp_id>/', views.delete_employee, name='delete_employee'),
    path('attendance/<int:emp_id>/', views.attendance_action, name='attendance_action'),

    # 7. หน้ารายละเอียดแผนก
    path('department/<str:dept_name>/', views.department_detail, name='department_detail'),

    # 8. Webhook (LINE Bot)
    path('webhook/', views.line_webhook, name='line_webhook'),

    # 9. จัดการ User & รีเซ็ตรหัสผ่าน
    path('users/manage/', views.user_list, name='user_list'),
    path('users/reset-password/<int:user_id>/', views.admin_reset_password, name='admin_reset_password'),

    # 🛒 10. ระบบขายหน้าร้าน (POS System)
    path('pos/', views.pos_home, name='pos_home'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),

    # ==========================================
    # 📦 11. ระบบคลังสินค้า (Inventory System)
    # ==========================================
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/add/', views.product_create, name='product_create'),
    path('inventory/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('inventory/suppliers/', views.supplier_list, name='supplier_list'),
    path('inventory/suppliers/add/', views.supplier_create, name='supplier_create'),

    # ==========================================
    # 🚛 12. ระบบจัดซื้อ (Purchasing System)
    # ==========================================
    # 👉 ทางเข้า Dashboard จัดซื้อ (ที่เพิ่มใหม่)
    path('purchasing/dashboard/', views.purchasing_dashboard, name='purchasing_dashboard'),

    # ทางเข้าจัดการ PO (เดิม)
    path('purchase/', views.po_list, name='po_list'),
    path('purchase/new/', views.po_create, name='po_create'),
    path('purchase/<int:po_id>/', views.po_detail, name='po_detail'),
    path('purchase/<int:po_id>/receive/', views.po_receive, name='po_receive'),
    path('manufacturing/', views.manufacturing_dashboard, name='manufacturing_dashboard'),
    path('manufacturing/create/', views.mo_create, name='mo_create'),
    path('manufacturing/complete/<int:mo_id>/', views.mo_complete, name='mo_complete'),
    path('manufacturing/delete/<int:mo_id>/', views.mo_delete, name='mo_delete'),
    path('manufacturing/create-product/<str:p_type>/', views.quick_create_product, name='quick_create_product'),
    path('manufacturing/create-bom/', views.quick_create_bom, name='quick_create_bom'),
    path('dashboard/production/', views.production_dept_dashboard, name='production_dept_dashboard'),
    path('dashboard/hr/', views.hr_dashboard, name='hr_dashboard'),
    path('dashboard/sales/', views.sales_dashboard, name='sales_dashboard'),

    # 13. ออกจากระบบ
    path('logout/', views.logout_view, name='logout'),
]