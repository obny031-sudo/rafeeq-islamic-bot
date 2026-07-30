"""
Extract Adhkar PDF pages to images using PyMuPDF.
This script converts each page of adhkar.pdf to a high-quality JPEG image.
"""

import fitz  # PyMuPDF
import os
import json
from pathlib import Path

# Paths
PDF_PATH = "d:/Rafeeq/assets/data/adhkar.pdf"
OUTPUT_DIR = "d:/Rafeeq/assets/images/adhkar"
MAPPING_FILE = "d:/Rafeeq/assets/data/adhkar_map.json"

def extract_pdf_to_images():
    """Extract PDF pages to JPEG images"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Open PDF
    pdf_document = fitz.open(PDF_PATH)
    
    # Mapping data
    adhkar_mapping = []
    
    # Extract each page
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        
        # Convert page to image
        # zoom=2 for higher quality (300 DPI equivalent)
        mat = fitz.Matrix(2, 2)  
        pix = page.get_pixmap(matrix=mat)
        
        # Save as JPEG
        image_path = os.path.join(OUTPUT_DIR, f"page_{page_num + 1}.jpg")
        pix.save(image_path)
        
        # Determine category based on page number
        # Assuming first half is morning, second half is evening
        total_pages = len(pdf_document)
        if page_num < total_pages // 2:
            category = "morning_adhkar"
            category_id = f"morning_{page_num + 1:02d}"
        else:
            category = "evening_adhkar"
            category_id = f"evening_{page_num + 1 - total_pages // 2:02d}"
        
        # Add to mapping
        adhkar_mapping.append({
            "id": category_id,
            "path": f"assets/images/adhkar/page_{page_num + 1}.jpg",
            "category": category,
            "page_number": page_num + 1
        })
        
        print(f"Extracted page {page_num + 1} to {image_path}")
    
    # Close PDF
    pdf_document.close()
    
    # Save mapping file
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(adhkar_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Extracted {len(adhkar_mapping)} pages to {OUTPUT_DIR}")
    print(f"✅ Created mapping file: {MAPPING_FILE}")
    
    return adhkar_mapping

if __name__ == "__main__":
    print("Starting PDF extraction...")
    extract_pdf_to_images()
    print("Done!")
