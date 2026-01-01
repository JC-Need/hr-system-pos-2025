from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 🏠 เส้นทางหลัก (Pages)
    # ==========================================
    path('', views.quotation_list, name='quotation_list'),
    path('create/', views.quotation_create, name='quotation_create'),
    
    # หน้าแก้ไข (Working Area)
    path('edit/<int:qt_id>/', views.quotation_edit, name='quotation_edit'),
    
    # หน้าแสดงผล (Print Area)
    path('detail/<int:qt_id>/', views.quotation_detail, name='quotation_detail'),
    
    # ฟังก์ชันลบสินค้า
    path('delete-item/<int:item_id>/', views.delete_item, name='delete_item'),

    # ==========================================
    # 🔌 ส่วน API สำหรับ Dropdown ที่อยู่ (ต้องมีส่วนนี้!)
    # ==========================================
    path('api/get-provinces/', views.get_provinces, name='get_provinces'),
    path('api/get-amphures/', views.get_amphures, name='get_amphures'),
    path('api/get-tambons/', views.get_tambons, name='get_tambons'),
]