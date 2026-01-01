from .models import CompanyInfo

def company_global(request):
    # ดึงข้อมูลบริษัทรายการแรกสุดมาใช้ (ถ้าไม่มีให้เป็น None)
    info = CompanyInfo.objects.first()
    return {'company': info}