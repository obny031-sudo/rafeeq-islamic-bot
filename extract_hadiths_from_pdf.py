"""
Script to extract Hadiths from PDF file and convert to JSON format.
"""

import json
import re
from pathlib import Path
import logging

# Try to import PyPDF2, if not available, we'll need to install it
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("PyPDF2 not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "PyPDF2"])
    import PyPDF2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def parse_hadiths_from_text(text: str) -> list:
    """Parse hadiths from extracted text"""
    hadiths = []
    
    # This is a basic pattern - we may need to adjust based on the actual PDF structure
    # Looking for patterns like: "الحديث الأول", "الحديث رقم 1", etc.
    lines = text.split('\n')
    
    current_hadith = None
    hadith_number = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to detect hadith number patterns
        hadith_match = re.search(r'(الحديث|حديث)\s*(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+)', line, re.IGNORECASE)
        
        if hadith_match:
            # Save previous hadith if exists
            if current_hadith:
                hadiths.append(current_hadith)
            
            hadith_number += 1
            current_hadith = {
                "hadithnumber": hadith_number,
                "arabicnumber": hadith_number,
                "text": "",
                "grades": [{"name": "صحيح", "grade": "صحيح"}],
                "reference": {"book": "المتفق عليه", "hadith": str(hadith_number)}
            }
        elif current_hadith:
            # Add text to current hadith
            if current_hadith["text"]:
                current_hadith["text"] += " " + line
            else:
                current_hadith["text"] = line
    
    # Add the last hadith
    if current_hadith:
        hadiths.append(current_hadith)
    
    return hadiths

def create_hadiths_json(hadiths: list, output_path: str):
    """Create hadiths.json file with proper structure"""
    data = {
        "metadata": {
            "name": "الأحاديث المتفق عليها سنداً ومتناً عند الإمامين البخاري ومسلم",
            "sections": {
                "0": "",
                "1": "الأحاديث المتفق عليها"
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
    pdf_path = "d:/Rafeeq/assets/data/الأحاديث-المتفق-عليها-سندا-ومتنا-عند-الامامين-البخاري-ومسلم.pdf"
    output_path = "d:/Rafeeq/assets/data/hadiths.json"
    
    logger.info(f"Extracting text from PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        logger.error("No text extracted from PDF")
        return
    
    logger.info(f"Extracted {len(text)} characters")
    
    # Save raw text for inspection
    raw_text_path = "d:/Rafeeq/assets/data/raw_hadiths_text.txt"
    with open(raw_text_path, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Saved raw text to {raw_text_path}")
    
    logger.info("Parsing hadiths from text...")
    hadiths = parse_hadiths_from_text(text)
    
    logger.info(f"Found {len(hadiths)} hadiths")
    
    if hadiths:
        create_hadiths_json(hadiths, output_path)
    else:
        logger.warning("No hadiths found. Manual parsing may be required.")

if __name__ == "__main__":
    main()
