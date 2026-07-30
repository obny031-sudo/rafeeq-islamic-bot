"""
Script to extract Hadiths from PDF file using pdfplumber for better text extraction.
"""

import json
import re
from pathlib import Path
import logging

# Try to import pdfplumber, if not available, we'll need to install it
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("pdfplumber not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "pdfplumber"])
    import pdfplumber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file using pdfplumber with PyPDF2 fallback"""
    text = ""
    try:
        # Try pdfplumber first
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    # Fix RTL text direction for Arabic
                    lines = page_text.split('\n')
                    fixed_lines = []
                    for line in lines:
                        if any('\u0600' <= c <= '\u06FF' for c in line):
                            fixed_line = line[::-1]
                            fixed_lines.append(fixed_line)
                        else:
                            fixed_lines.append(line)
                    text += '\n'.join(fixed_lines) + "\n"
        
        if text:
            return text
    except Exception as e:
        logger.warning(f"pdfplumber failed for {pdf_path}, trying PyPDF2: {e}")
    
    # Fallback to PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    lines = page_text.split('\n')
                    fixed_lines = []
                    for line in lines:
                        if any('\u0600' <= c <= '\u06FF' for c in line):
                            fixed_line = line[::-1]
                            fixed_lines.append(fixed_line)
                        else:
                            fixed_lines.append(line)
                    text += '\n'.join(fixed_lines) + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF with PyPDF2: {e}")
        return ""

def parse_hadiths_from_text(text: str) -> list:
    """Parse hadiths from extracted text with better pattern matching"""
    hadiths = []
    
    # Split text into lines
    lines = text.split('\n')
    
    current_hadith = None
    hadith_number = 0
    
    # Multiple patterns to detect hadith numbers
    patterns = [
        r'^(\d+)[.\s]+',  # Numbers at start of line
        r'الحديث\s*(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+)',
        r'حديث\s*(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+)',
        r'^(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر)[.\s]',
    ]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Try to detect hadith number patterns
        is_hadith_start = False
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                is_hadith_start = True
                break
        
        if is_hadith_start:
            # Save previous hadith if exists
            if current_hadith and current_hadith.get("text"):
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
    if current_hadith and current_hadith.get("text"):
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
    pdf_files = [
        "d:/Rafeeq/assets/data/الأحاديث-المتفق-عليها-سندا-ومتنا-عند-الامامين-البخاري-ومسلم.pdf",
        "d:/Rafeeq/assets/data/Noor-Book.com  الأحاديث الصحيحة مرتبة على الأبواب الفقهية.pdf"
    ]
    output_path = "d:/Rafeeq/assets/data/hadiths.json"
    
    all_hadiths = []
    hadith_number = 0
    
    for pdf_path in pdf_files:
        logger.info(f"Extracting text from PDF: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            logger.error(f"No text extracted from PDF: {pdf_path}")
            continue
        
        logger.info(f"Extracted {len(text)} characters from {pdf_path}")
        
        # Save raw text for inspection
        pdf_name = Path(pdf_path).stem
        raw_text_path = f"d:/Rafeeq/assets/data/raw_hadiths_text_{pdf_name}.txt"
        with open(raw_text_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(text)
        logger.info(f"Saved raw text to {raw_text_path}")
        
        logger.info(f"Parsing hadiths from {pdf_path}...")
        hadiths = parse_hadiths_from_text(text)
        
        logger.info(f"Found {len(hadiths)} hadiths from {pdf_path}")
        
        # Renumber hadiths to continue from previous
        for hadith in hadiths:
            hadith_number += 1
            hadith["hadithnumber"] = hadith_number
            hadith["arabicnumber"] = hadith_number
            hadith["reference"]["hadith"] = str(hadith_number)
        
        all_hadiths.extend(hadiths)
    
    logger.info(f"Total hadiths from all PDFs: {len(all_hadiths)}")
    
    # Show first few hadiths for inspection
    for i, hadith in enumerate(all_hadiths[:3]):
        logger.info(f"Hadith {i+1}: {hadith['text'][:100]}...")
    
    if all_hadiths:
        create_hadiths_json(all_hadiths, output_path)
    else:
        logger.warning("No hadiths found. Manual parsing may be required.")

if __name__ == "__main__":
    main()
