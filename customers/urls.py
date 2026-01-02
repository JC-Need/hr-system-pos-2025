from django.urls import path
from . import views

urlpatterns = [
    # หน้ารายการลูกค้า
    path('', views.customer_list, name='customer_list'),
    
    # หน้าเพิ่มลูกค้าใหม่
    path('create/', views.customer_create, name='customer_create'),
    
    # ✅ หน้าแก้ไขข้อมูลลูกค้า (บรรทัดนี้คือตัวแก้ปัญหาครับ!)
    path('edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    
    # หน้าลบลูกค้า
    path('delete/<int:pk>/', views.customer_delete, name='customer_delete'),
]