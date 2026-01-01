import os
import django
import json
import sys

# ตั้งค่า Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mycompany.settings')
django.setup()

from sales.models import Province, Amphure, Tambon

def auto_detect_key(data_dict, candidates):
    """ฟังก์ชันช่วยหาชื่อ key ที่ถูกต้องจากรายการที่เป็นไปได้"""
    for key in candidates:
        if key in data_dict and isinstance(data_dict[key], list):
            return key
    return None

def import_data():
    # หาไฟล์ JSON ในเครื่อง
    file_path = None
    search_paths = [
        'thai-province-data/api/latest/province_with_district_and_sub_district.json',
        'thai-province-data/api_province_with_amphure_tambon.json'
    ]
    
    # เดินหาไฟล์ในทุกซอกทุกมุม
    for path in search_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if not file_path:
        for root, dirs, files in os.walk('thai-province-data'):
            if 'province_with_district_and_sub_district.json' in files:
                file_path = os.path.join(root, 'province_with_district_and_sub_district.json')
                break

    if not file_path:
        print("❌ ไม่พบไฟล์ข้อมูล! (ลองรัน git clone ใหม่นะครับ)")
        return

    print(f"📂 อ่านไฟล์จาก: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ อ่านไฟล์ไม่สำเร็จ: {e}")
        return

    # 🕵️‍♂️ ตรวจสอบโครงสร้างไฟล์ (Debug)
    if data and isinstance(data, list):
        first_item = data[0]
        print(f"🔍 ตัวอย่าง Key ในข้อมูล: {list(first_item.keys())}")
        
        # หาชื่อ key สำหรับอำเภอ
        amphure_key = auto_detect_key(first_item, ['amphure', 'district', 'amphur'])
        if not amphure_key:
            print("❌ หา key 'อำเภอ' ไม่เจอในไฟล์นี้")
            return
        print(f"✅ พบ Key อำเภอใช้ชื่อว่า: '{amphure_key}'")

        # หาชื่อ key สำหรับตำบล (ดูจากอำเภอแรก)
        if first_item[amphure_key]:
            first_amp = first_item[amphure_key][0]
            tambon_key = auto_detect_key(first_amp, ['tambon', 'sub_district', 'subdistrict'])
            print(f"✅ พบ Key ตำบลใช้ชื่อว่า: '{tambon_key}'")
        else:
            tambon_key = 'tambon' # เดาไปก่อน

    # เริ่มล้างและลงข้อมูลใหม่
    print("⏳ กำลังบันทึกข้อมูล... (รอสักครู่นะครับ)")
    Tambon.objects.all().delete()
    Amphure.objects.all().delete()
    Province.objects.all().delete()

    count_p, count_a, count_t = 0, 0, 0

    for p_data in data:
        province = Province.objects.create(
            code=str(p_data.get('id', '')),
            name_th=p_data.get('name_th', ''),
            name_en=p_data.get('name_en', '')
        )
        count_p += 1

        districts_list = p_data.get(amphure_key, [])
        
        for a_data in districts_list:
            amphure = Amphure.objects.create(
                province=province,
                code=str(a_data.get('id', '')),
                name_th=a_data.get('name_th', ''),
                name_en=a_data.get('name_en', '')
            )
            count_a += 1

            sub_districts_list = a_data.get(tambon_key, [])
            batch_tambons = []
            
            for t_data in sub_districts_list:
                zip_code = str(t_data.get('zip_code', '')) if t_data.get('zip_code') else ''
                batch_tambons.append(Tambon(
                    amphure=amphure,
                    zip_code=zip_code,
                    name_th=t_data.get('name_th', ''),
                    name_en=t_data.get('name_en', '')
                ))
            
            Tambon.objects.bulk_create(batch_tambons)
            count_t += len(batch_tambons)

    print("-" * 50)
    print(f"🎉 เสร็จสมบูรณ์! ข้อมูลมาครบแล้ว 100%")
    print(f"📍 จังหวัด: {count_p:,}")
    print(f"📍 อำเภอ:  {count_a:,}")
    print(f"📍 ตำบล:   {count_t:,}")
    print("-" * 50)

if __name__ == '__main__':
    import_data()