import json
import urllib.request
import os

output_dir = os.path.join("assets", "data")
os.makedirs(output_dir, exist_ok=True)

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

print("🚀 جاري تحميل وتنظيم كافة بيانات البوت المكتملة (100%)...\n")

# 1️⃣ تحميل القرآن الكريم كاملاً (114 سورة)
try:
    print("⏳ [1/3] جاري تأكيد ملف القرآن الكريم (114 سورة)...")
    quran_url = "https://api.alquran.cloud/v1/quran/quran-uthmani"
    quran_raw = fetch_json(quran_url)
    surahs = []
    for s in quran_raw['data']['surahs']:
        surahs.append({
            "id": s['number'],
            "name": s['name'],
            "englishName": s['englishName'],
            "revelationType": s['revelationType'],
            "total_verses": len(s['ayahs']),
            "verses": [{"id": a['numberInSurah'], "text": a['text']} for a in s['ayahs']]
        })
    with open(os.path.join(output_dir, "quran.json"), "w", encoding="utf-8") as f:
        json.dump(surahs, f, ensure_ascii=False, indent=2)
    print("✅ تم تجهيز quran.json بنجاح!")
except Exception as e:
    print(f"❌ خطأ في القرآن: {e}")

# 2️⃣ تحميل الأحاديث النبوية كاملة (الأربعين النووية)
try:
    print("⏳ [2/3] جاري تحميل الأحاديث النبوية كاملة...")
    hadith_url = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions/ara-nawawi.json"
    hadith_data = fetch_json(hadith_url)
    with open(os.path.join(output_dir, "hadiths.json"), "w", encoding="utf-8") as f:
        json.dump(hadith_data, f, ensure_ascii=False, indent=2)
    print("✅ تم تجهيز hadiths.json بنجاح!")
except Exception as e:
    print(f"❌ خطأ في الأحاديث: {e}")

# 3️⃣ تحميل كتاب الأذكار كاملاً (حصن المسلم)
try:
    print("⏳ [3/3] جاري تحميل الأذكار والأدعية كاملة (حصن المسلم)...")
    azkar_url = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions/ara-hisn.json"
    azkar_data = fetch_json(azkar_url)
    with open(os.path.join(output_dir, "azkar.json"), "w", encoding="utf-8") as f:
        json.dump(azkar_data, f, ensure_ascii=False, indent=2)
    print("✅ تم تجهيز azkar.json بنجاح!")
except Exception as e:
    print(f"❌ خطأ في الأذكار: {e}")

print("\n🎉 مبروك! تمت العملية بنجاح وبقت كل البيانات المكتملة جاهزة في assets/data/")