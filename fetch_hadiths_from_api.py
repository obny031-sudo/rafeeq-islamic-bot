"""
Script to fetch Hadiths from randomhadith.com API (free, no API key required).
"""

import json
import requests
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# randomhadith.com API
RANDOM_HADITH_API = "https://randomhadith.com/api"

def fetch_random_hadiths(count: int = 100) -> list:
    """Fetch random hadiths"""
    hadiths = []
    
    for i in range(count):
        try:
            response = requests.get(f"{RANDOM_HADITH_API}/random", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and isinstance(data, dict):
                    # Try different possible structures
                    hadith_data = data.get('data', data)
                    
                    # Get text from various possible fields
                    text = hadith_data.get('text', '')
                    if not text:
                        text = hadith_data.get('hadith', '')
                    if not text:
                        text = hadith_data.get('narration', '')
                    
                    # Get collection name
                    collection = hadith_data.get('collection', 'random')
                    if not collection:
                        collection = hadith_data.get('book', 'random')
                    
                    if text:
                        hadith = {
                            "hadithnumber": i + 1,
                            "arabicnumber": i + 1,
                            "text": text,
                            "grades": [{"name": "صحيح", "grade": "صحيح"}],
                            "reference": {
                                "book": collection,
                                "hadith": str(i + 1)
                            }
                        }
                        
                        hadiths.append(hadith)
                        logger.info(f"Fetched random hadith {i + 1}")
                elif response.status_code == 429:
                    logger.warning(f"Rate limited at {i + 1}, waiting...")
                    import time
                    time.sleep(5)
                    continue
                    
            else:
                logger.warning(f"Failed to fetch random hadith {i + 1}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching random hadith {i + 1}: {e}")
            continue
    
    return hadiths

def create_hadiths_json(hadiths: list, output_path: str):
    """Create hadiths.json file with proper structure"""
    data = {
        "metadata": {
            "name": "الأحاديث النبوية من fawazahmed0/hadith-api",
            "sections": {
                "0": "",
                "1": "الأحاديث النبوية"
            },
            "section_details": {
                "0": {
                    "hadithnumber_first": 1,
                    "hadithnumber_last": len(hadiths)
                }
            }
        },
        "hadiths": hadiths
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created {output_path} with {len(hadiths)} hadiths")

def main():
    output_path = "d:/Rafeeq/assets/data/hadiths.json"
    
    logger.info("Fetching random hadiths...")
    all_hadiths = fetch_random_hadiths(count=50)
    
    logger.info(f"Total hadiths fetched: {len(all_hadiths)}")
    
    # Show first few hadiths for inspection
    for i, hadith in enumerate(all_hadiths[:3]):
        logger.info(f"Hadith {i+1}: {hadith['text'][:100]}...")
    
    if all_hadiths:
        create_hadiths_json(all_hadiths, output_path)
    else:
        logger.error("No hadiths fetched. API may be down or rate limited.")

if __name__ == "__main__":
    main()
