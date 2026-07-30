import json
import urllib.request
import os

# إنشاء المجلد لو مش موجود
os.makedirs("assets/data", exist_ok=True)

print("⏳ جاري تحميل القرآن الكريم كاملاً (114 سورة)...")

# رابط API مباشر ومفتوح المصدر يرجع القرآن كاملاً باللغة العربية
url = "https://api.alquran.cloud/v1/quran/quran-uthmani"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
        surahs = []
        for surah in data['data']['surahs']:
            surah_data = {
                "id": surah['number'],
                "name": surah['name'],
                "englishName": surah['englishName'],
                "revelationType": surah['revelationType'],
                "total_verses": len(surah['ayahs']),
                "verses": [
                    {
                        "id": ayah['numberInSurah'],
                        "text": ayah['text']
                    } for ayah in surah['ayahs']
                ]
            }
            surahs.append(surah_data)
            
        with open("assets/data/quran.json", "w", encoding="utf-8") as f:
            json.dump(surahs, f, ensure_ascii=False, indent=2)
            
    print("✅ تم تحميل 114 سورة بنجاح وتخزينها في assets/data/quran.json!")
except Exception as e:
    print(f"❌ حدث خطأ أثناء التحميل: {e}")