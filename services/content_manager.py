"""
ContentManager - Single Source of Truth for all Islamic content.
Loads and serves content from local JSON files and extracted images.
Ensures strict UTF-8 encoding and no data truncation.
"""

import json
import random
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from utils.media_cache import media_cache

logger = logging.getLogger(__name__)


class ContentManager:
    """Manages all Islamic content from local files"""
    
    def __init__(self, base_path: str = "d:/Rafeeq/assets"):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.images_path = self.base_path / "images"
        
        # Load data files
        logger.info("Starting to load data files...")
        self.quran_data = self._load_json_file(self.data_path / "quran.json")
        logger.info(f"Quran data loaded: {type(self.quran_data)}, length: {len(self.quran_data) if hasattr(self.quran_data, '__len__') else 'N/A'}")
        
        self.hadith_data = self._load_json_file(self.data_path / "hadiths.json")
        logger.info(f"Hadith data loaded: {type(self.hadith_data)}, length: {len(self.hadith_data) if hasattr(self.hadith_data, '__len__') else 'N/A'}")
        
        self.adhkar_mapping = self._load_json_file(self.data_path / "adhkar_map.json")
        logger.info(f"Adhkar mapping loaded: {type(self.adhkar_mapping)}, length: {len(self.adhkar_mapping) if hasattr(self.adhkar_mapping, '__len__') else 'N/A'}")
        
        logger.info(f"ContentManager initialized with {len(self.quran_data)} Quran entries, "
                   f"{len(self.hadith_data)} Hadith entries, "
                   f"{len(self.adhkar_mapping)} Adhkar images")
    
    def _load_json_file(self, file_path: Path) -> Dict:
        """Load JSON file with UTF-8 encoding"""
        try:
            logger.info(f"Loading file: {file_path}")
            logger.info(f"File exists: {file_path.exists()}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Raw data type: {type(data)}, value: {data if not isinstance(data, (list, dict)) else '...'}")
            
            # Handle different structures
            if isinstance(data, dict):
                # If it's a dict with metadata, extract the actual data
                if 'hadiths' in data:
                    data = data['hadiths']
                elif 'surahs' in data:
                    data = data['surahs']
                elif 'metadata' in data:
                    # For hadiths.json which has metadata + hadiths
                    if 'hadiths' in data:
                        data = data['hadiths']
            elif isinstance(data, bool):
                logger.error(f"Data is boolean: {data}, returning empty list")
                return []
            
            # Validate that data is a list or dict
            if not isinstance(data, (list, dict)):
                logger.error(f"Data is not a list or dict: {type(data)}, returning empty list")
                return []
            
            logger.info(f"Loaded {file_path.name}: {len(data)} entries, type: {type(data)}")
            return data
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}", exc_info=True)
            return []
    
    def get_full_surah(self, surah_number: int) -> Optional[Dict]:
        """Get full Surah data by number"""
        try:
            # Try to find surah by id (1-based)
            for surah in self.quran_data:
                if surah.get('id') == surah_number:
                    return surah
            
            # If not found by id, try by index (0-based)
            if 0 <= surah_number - 1 < len(self.quran_data):
                return self.quran_data[surah_number - 1]
            
            logger.warning(f"Surah {surah_number} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting Surah {surah_number}: {e}")
            return None
    
    def get_surah_ayah(self, surah_number: int, ayah_number: int) -> Optional[Dict]:
        """Get specific Ayah from Surah"""
        try:
            surah = self.get_full_surah(surah_number)
            if not surah:
                return None
            
            # Try to find ayah by id
            verses = surah.get('verses', [])
            for verse in verses:
                if verse.get('id') == ayah_number:
                    return verse
            
            # If not found by id, try by index
            if 0 <= ayah_number - 1 < len(verses):
                return verses[ayah_number - 1]
            
            logger.warning(f"Ayah {ayah_number} in Surah {surah_number} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting Ayah {ayah_number}:{surah_number}: {e}")
            return None
    
    def get_random_ayah(self) -> Optional[Dict]:
        """Get a random Ayah from Quran"""
        try:
            # Get random surah
            random_surah = random.choice(self.quran_data)
            verses = random_surah.get('verses', [])
            
            if verses:
                random_ayah = random.choice(verses)
                # Add surah context
                random_ayah['surah_name'] = random_surah.get('name', '')
                random_ayah['surah_number'] = random_surah.get('id', 0)
                return random_ayah
            
            return None
        except Exception as e:
            logger.error(f"Error getting random Ayah: {e}")
            return None
    
    def get_hadith(self, hadith_id: Optional[int] = None, random: bool = False) -> Optional[Dict]:
        """Get Hadith by ID or random"""
        try:
            if random:
                return random.choice(self.hadith_data) if self.hadith_data else None
            
            if hadith_id is not None:
                # Try to find by hadithnumber
                for hadith in self.hadith_data:
                    if hadith.get('hadithnumber') == hadith_id:
                        return hadith
                
                # If not found by hadithnumber, try by arabicnumber
                for hadith in self.hadith_data:
                    if hadith.get('arabicnumber') == hadith_id:
                        return hadith
                
                # If not found by either, try by index
                if 0 <= hadith_id - 1 < len(self.hadith_data):
                    return self.hadith_data[hadith_id - 1]
            
            return None
        except Exception as e:
            logger.error(f"Error getting Hadith {hadith_id}: {e}")
            return None
    
    def get_adhkar_image(self, category: str = "morning_adhkar") -> Optional[Dict]:
        """Get Adhkar image path by category"""
        try:
            # Filter by category
            category_images = [img for img in self.adhkar_mapping 
                             if img.get('category') == category]
            
            if not category_images:
                logger.warning(f"No images found for category: {category}")
                return None
            
            # Return random image from category
            return random.choice(category_images)
        except Exception as e:
            logger.error(f"Error getting Adhkar image for {category}: {e}")
            return None
    
    def get_adhkar_image_by_id(self, image_id: str) -> Optional[Dict]:
        """Get specific Adhkar image by ID"""
        try:
            for img in self.adhkar_mapping:
                if img.get('id') == image_id:
                    return img
            return None
        except Exception as e:
            logger.error(f"Error getting Adhkar image {image_id}: {e}")
            return None
    
    def search_quran(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search Quran for Arabic or English keywords.
        
        Args:
            query: Search keyword (Arabic or English)
            max_results: Maximum results to return
        
        Returns:
            List of matching Ayahs with Surah context
        """
        try:
            results = []
            query_lower = query.lower()
            
            for surah in self.quran_data:
                surah_name = surah.get('name', '').lower()
                surah_number = surah.get('surah_number', 0)
                
                for ayah in surah.get('ayahs', []):
                    arabic_text = ayah.get('arabic_text', '').lower()
                    translation_en = ayah.get('translation_en', '').lower()
                    translation_ar = ayah.get('translation_ar', '').lower()
                    
                    # Search in Arabic text
                    if query_lower in arabic_text:
                        ayah_copy = ayah.copy()
                        ayah_copy['surah_name'] = surah.get('name', '')
                        ayah_copy['surah_number'] = surah_number
                        results.append(ayah_copy)
                        continue
                    
                    # Search in translations
                    if query_lower in translation_en or query_lower in translation_ar:
                        ayah_copy = ayah.copy()
                        ayah_copy['surah_name'] = surah.get('name', '')
                        ayah_copy['surah_number'] = surah_number
                        results.append(ayah_copy)
                        continue
                
                # Search in Surah name
                if query_lower in surah_name:
                    # Return first few ayahs of matching Surah
                    ayahs = surah.get('ayahs', [])[:3]
                    for ayah in ayahs:
                        ayah_copy = ayah.copy()
                        ayah_copy['surah_name'] = surah.get('name', '')
                        ayah_copy['surah_number'] = surah_number
                        results.append(ayah_copy)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching Quran: {e}")
            return []
    
    def search_hadith(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search Hadith for Arabic or English keywords.
        
        Args:
            query: Search keyword (Arabic or English)
            max_results: Maximum results to return
        
        Returns:
            List of matching Hadiths
        """
        try:
            results = []
            query_lower = query.lower()
            
            for hadith in self.hadith_data:
                arabic_text = hadith.get('arabic_text', '').lower()
                translation_en = hadith.get('translation_en', '').lower()
                translation_ar = hadith.get('translation_ar', '').lower()
                narrator = hadith.get('narrator', '').lower()
                collection = hadith.get('collection', '').lower()
                
                # Search in all fields
                if (query_lower in arabic_text or 
                    query_lower in translation_en or 
                    query_lower in translation_ar or
                    query_lower in narrator or
                    query_lower in collection):
                    results.append(hadith)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching Hadith: {e}")
            return []
    
    def find_surah_by_name(self, name: str) -> Optional[Dict]:
        """
        Find Surah by Arabic name (exact or fuzzy match).
        
        Args:
            name: Surah name in Arabic
        
        Returns:
            Surah data or None if not found
        """
        try:
            name_lower = name.lower()
            
            # Try exact match first
            for surah in self.quran_data:
                if surah.get('name', '').lower() == name_lower:
                    return surah
            
            # Try fuzzy match (contains)
            for surah in self.quran_data:
                if name_lower in surah.get('name', '').lower():
                    return surah
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding Surah by name: {e}")
            return None
    
    def chunk_text(self, text: str, max_length: int = 4096) -> List[str]:
        """Safely chunk text without breaking words"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        words = text.split()
        
        for word in words:
            # Check if adding this word would exceed limit
            if len(current_chunk) + len(word) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def format_ayah_message(self, ayah: Dict) -> str:
        """Format Ayah for Telegram message"""
        text = f"📖 *آية من القرآن الكريم*\n\n"
        text += f"📚 السورة: {ayah.get('surah_name', 'غير معروف')}\n"
        text += f"🔢 الآية: {ayah.get('id', 'غير معروف')}\n\n"
        text += f"📜 *النص العربي:*\n{ayah.get('text', '')}\n\n"
        
        return text
    
    def format_hadith_message(self, hadith: Dict) -> str:
        """Format Hadith for Telegram message"""
        text = f"📚 *حديث شريف*\n\n"
        
        if hadith.get('hadithnumber'):
            text += f"� رقم الحديث: {hadith.get('hadithnumber')}\n"
        
        if hadith.get('arabicnumber'):
            text += f"🔢 الرقم العربي: {hadith.get('arabicnumber')}\n\n"
        
        text += f"📜 *النص العربي:*\n{hadith.get('text', '')}\n\n"
        
        if hadith.get('reference'):
            ref = hadith.get('reference', {})
            if ref.get('book'):
                text += f"📔 الكتاب: {ref.get('book')}\n"
            if ref.get('hadith'):
                text += f"📖 الحديث: {ref.get('hadith')}\n"
        
        return text


# Global instance
content_manager = ContentManager()
