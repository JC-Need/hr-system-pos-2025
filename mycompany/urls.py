from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. หน้า Admin (ระบบหลังบ้าน)
    path('admin/', admin.site.urls),

    # 2. ระบบ Login / Logout
    path('accounts/login/', auth_views.LoginView.as_view(template_name='employees/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # 3. ระบบหลัก (Dashboard, พนักงาน, ฯลฯ)
    path('', include('employees.urls')),

    # 4. ✅ ระบบฝ่ายขายใหม่ (Sales App) - เพิ่มบรรทัดนี้ครับ
    path('sales/', include('sales.urls')),
]

# ส่วนนี้ช่วยให้แสดงรูปภาพได้ตอนรันบนเครื่อง (Debug Mode)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)