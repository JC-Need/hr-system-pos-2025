import os
import django
import json
import sys

# ตั้งค่า Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycompany.settings')
django.setup()

from sales.models import Province, Amphure, Tambon

def import_data():
    # กำหนดไฟล์เป้าหมาย (ลองหาทั้ง V1 และ V2)
    possible_files = [
        'thai-province-data/api/latest/province_with_district_and_sub_district.json', # V2
        'thai-province-data/api_province_with_amphure_tambon.json' # V1
    ]
    
    file_path = None
    for path in possible_files:
        if os.path.exists(path):
            file_path = path
            break
            
    if not file_path:
        # ถ้าหาไม่เจอ ลองค้นหาในทุกโฟลเดอร์
        for root, dirs, files in os.walk('thai-province-data'):
            if 'province_with_district_and_sub_district.json' in files:
                file_path = os.path.join(root, 'province_with_district_and_sub_district.json')
                break
            if 'api_province_with_amphure_tambon.json' in files:
                file_path = os.path.join(root, 'api_province_with_amphure_tambon.json')
                break

    if not file_path:
        print("❌ ไม่พบไฟล์ข้อมูล! กรุณารันคำสั่ง: git clone https://github.com/kongvut/thai-province-data.git")
        return

    print(f"📂 อ่านไฟล์จาก: {file_path}")
    print("⏳ กำลังบันทึกข้อมูล... (รอสักครู่นะครับ)")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ อ่านไฟล์ไม่สำเร็จ: {e}")
        return

    # เคลียร์ข้อมูลเก่า
    Tambon.objects.all().delete()
    Amphure.objects.all().delete()
    Province.objects.all().delete()

    count_p, count_a, count_t = 0, 0, 0

    for p_data in data:
        province = Province.objects.create(
            code=str(p_data['id']),
            name_th=p_data['name_th'],
            name_en=p_data['name_en']
        )
        count_p += 1

        # ✅ Hybrid Check: รองรับทั้ง 'district' (V2) และ 'amphure' (V1)
        districts = p_data.get('district') or p_data.get('amphure') or []
        
        for a_data in districts:
            amphure = Amphure.objects.create(
                province=province,
                code=str(a_data['id']),
                name_th=a_data['name_th'],
                name_en=a_data['name_en']
            )
            count_a += 1

            # ✅ Hybrid Check: รองรับทั้ง 'sub_district' (V2) และ 'tambon' (V1)
            sub_districts = a_data.get('sub_district') or a_data.get('tambon') or []
            
            batch_tambons = []
            for t_data in sub_districts:
                zip_code = str(t_data.get('zip_code', '')) if t_data.get('zip_code') else ''
                batch_tambons.append(Tambon(
                    amphure=amphure,
                    zip_code=zip_code,
                    name_th=t_data['name_th'],
                    name_en=t_data['name_en']
                ))
            
            Tambon.objects.bulk_create(batch_tambons)
            count_t += len(batch_tambons)

    print("-" * 50)
    print(f"🎉 เสร็จสมบูรณ์! ข้อมูลมาครบแล้วครับ")
    print(f"📍 จังหวัด: {count_p:,}")
    print(f"📍 อำเภอ:  {count_a:,}  <-- (ต้องไม่เป็น 0)")
    print(f"📍 ตำบล:   {count_t:,}  <-- (ต้องไม่เป็น 0)")
    print("-" * 50)

if __name__ == '__main__':
    import_data()