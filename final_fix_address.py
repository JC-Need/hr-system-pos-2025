import os
import django
import json
import sys

# ตั้งค่า Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycompany.settings')
django.setup()

from sales.models import Province, Amphure, Tambon

def import_data():
    # หาไฟล์ข้อมูล
    possible_paths = [
        'thai-province-data/api/latest/province_with_district_and_sub_district.json',
        'thai-province-data/api_province_with_amphure_tambon.json'
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
            
    if not file_path:
        # ลองค้นหาในโฟลเดอร์เผื่อโครงสร้างเปลี่ยน
        for root, dirs, files in os.walk('thai-province-data'):
            if 'province_with_district_and_sub_district.json' in files:
                file_path = os.path.join(root, 'province_with_district_and_sub_district.json')
                break

    if not file_path:
        print("❌ ไม่พบไฟล์ข้อมูล! กรุณารัน: git clone https://github.com/kongvut/thai-province-data.git")
        return

    print(f"📂 อ่านไฟล์จาก: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ อ่านไฟล์ไม่สำเร็จ: {e}")
        return

    print("⏳ กำลังล้างข้อมูลเก่าและบันทึกใหม่... (รอแป๊บนะครับ)")
    
    # ล้างข้อมูลเก่า
    Tambon.objects.all().delete()
    Amphure.objects.all().delete()
    Province.objects.all().delete()

    count_p, count_a, count_t = 0, 0, 0

    for p_data in data:
        province = Province.objects.create(
            code=str(p_data.get('id')),
            name_th=p_data.get('name_th'),
            name_en=p_data.get('name_en')
        )
        count_p += 1

        # ✅ แก้ไขจุดตาย: เพิ่ม 'districts' (มี s) เข้าไปในรายการค้นหา
        districts = p_data.get('districts') or p_data.get('district') or p_data.get('amphure') or []
        
        for a_data in districts:
            amphure = Amphure.objects.create(
                province=province,
                code=str(a_data.get('id')),
                name_th=a_data.get('name_th'),
                name_en=a_data.get('name_en')
            )
            count_a += 1

            # ✅ แก้ไขจุดตาย: เพิ่ม 'sub_districts' (มี s) เข้าไปในรายการค้นหา
            sub_districts = a_data.get('sub_districts') or a_data.get('sub_district') or a_data.get('tambon') or []
            
            batch_tambons = []
            for t_data in sub_districts:
                zip_code = str(t_data.get('zip_code', '')) if t_data.get('zip_code') else ''
                batch_tambons.append(Tambon(
                    amphure=amphure,
                    zip_code=zip_code,
                    name_th=t_data.get('name_th'),
                    name_en=t_data.get('name_en')
                ))
            
            Tambon.objects.bulk_create(batch_tambons)
            count_t += len(batch_tambons)

    print("-" * 50)
    print(f"🎉 เสร็จสมบูรณ์! (ยอดต้องขึ้นครบ)")
    print(f"📍 จังหวัด: {count_p:,}")
    print(f"📍 อำเภอ:  {count_a:,}")
    print(f"📍 ตำบล:   {count_t:,}")
    print("-" * 50)

if __name__ == '__main__':
    import_data()