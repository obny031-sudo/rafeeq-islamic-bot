"""
Mood-based Adhkar selector handler.
Allows users to select Adhkar based on their current mood/emotional state.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

logger = logging.getLogger(__name__)

router = Router()

# Simple Adhkar data for mood-based selection
MOOD_ADHKAR_DATA = {
    "morning": [
        {"arabic": "سُبْحَانَ اللهِ وَبِحَمْدِهِ", "translation": "Glory be to Allah and praise be to Him", "count": "100 مرة"},
        {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى وَالتُّقَى وَالْعَفَافَ وَالْغِنَى", "translation": "O Allah, I ask You for guidance, piety, chastity and self-sufficiency", "count": ""},
        {"arabic": "اللَّهُمَّ بَارِكْ لِي فِي أَصْبَاحِي", "translation": "O Allah, bless my morning", "count": ""}
    ],
    "evening": [
        {"arabic": "أَسْتَغْفِرُ اللهَ وَأَتُوبُ إِلَيْهِ", "translation": "I seek forgiveness from Allah and repent to Him", "count": "100 مرة"},
        {"arabic": "اللَّهُمَّ بَارِكْ لِي فِي أَمْسَائِي", "translation": "O Allah, bless my evening", "count": ""},
        {"arabic": "اللَّهُمَّ أَسْأَلُكَ الْجَنَّةَ وَأَعُوذُ بِكَ مِنَ النَّارِ", "translation": "O Allah, I ask You for Paradise and seek refuge in You from the Fire", "count": ""}
    ],
    "sleep": [
        {"arabic": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "translation": "In Your name, O Allah, I die and I live", "count": ""},
        {"arabic": "اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ", "translation": "O Allah, protect me from Your punishment on the Day You resurrect Your servants", "count": ""},
        {"arabic": "سُبْحَانَ اللهِ", "translation": "Glory be to Allah", "count": "33 مرة"}
    ],
    "general": [
        {"arabic": "لَا إِلَهَ إِلَّا اللهُ", "translation": "There is no god but Allah", "count": ""},
        {"arabic": "الْحَمْدُ لِلَّهِ", "translation": "Praise be to Allah", "count": ""},
        {"arabic": "اللَّهُ أَكْبَرُ", "translation": "Allah is the Greatest", "count": ""},
        {"arabic": "أَسْتَغْفِرُ اللهَ", "translation": "I seek forgiveness from Allah", "count": ""}
    ]
}


# Mood categories with corresponding Adhkar types
MOOD_CATEGORIES = {
    "happy": {
        "emoji": "😊",
        "name": "سعيد",
        "description": "أذكار الشكر والاستغفار",
        "adhkar_type": "general"
    },
    "sad": {
        "emoji": "😢",
        "name": "حزين",
        "description": "أذكار الاستعانة والصبر",
        "adhkar_type": "general"
    },
    "anxious": {
        "emoji": "😰",
        "name": "قلق",
        "description": "أذكار الطمأنينة والسكينة",
        "adhkar_type": "general"
    },
    "grateful": {
        "emoji": "🙏",
        "name": "شاكر",
        "description": "أذكار الشكر والحمد",
        "adhkar_type": "morning"
    },
    "seeking_peace": {
        "emoji": "🕊️",
        "name": "باحث عن السلام",
        "description": "أذكار السكينة والطمأنينة",
        "adhkar_type": "evening"
    },
    "tired": {
        "emoji": "😴",
        "name": "متعب",
        "description": "أذكار النوم والراحة",
        "adhkar_type": "sleep"
    }
}


@router.callback_query(F.data == "mood_adhkar_menu")
async def handle_mood_adhkar_menu(callback: CallbackQuery):
    """Show mood-based Adhkar selection menu"""
    await callback.answer("🎭 اختيار المزاج")
    
    builder = InlineKeyboardBuilder()
    
    # Build mood selection buttons
    for mood_key, mood_info in MOOD_CATEGORIES.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{mood_info['emoji']} {mood_info['name']}",
                callback_data=f"mood_select_{mood_key}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "🎭 *اختر حالتك المزاجية*\n\n"
        "سقترح لك أذكار مناسبة لحالتك الحالية:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("mood_select_"))
async def handle_mood_selection(callback: CallbackQuery):
    """Handle mood selection and show appropriate Adhkar"""
    await callback.answer()
    
    mood_key = callback.data.replace("mood_select_", "")
    
    if mood_key not in MOOD_CATEGORIES:
        await callback.message.edit_text("❌ اختيار غير صحيح")
        return
    
    mood_info = MOOD_CATEGORIES[mood_key]
    await callback.answer(f"{mood_info['emoji']} {mood_info['name']}")
    
    try:
        # Get appropriate Adhkar based on mood
        adhkar_type = mood_info["adhkar_type"]
        adhkar_list = MOOD_ADHKAR_DATA.get(adhkar_type, [])
        
        if not adhkar_list:
            await callback.message.edit_text(
                f"❌ لم يتم العثور على أذكار مناسبة لهذه الحالة.",
                parse_mode="Markdown"
            )
            return
        
        # Select relevant Adhkar based on mood
        selected_adhkar = []
        
        if mood_key == "happy":
            # Select gratitude Adhkar
            selected_adhkar = [a for a in adhkar_list if "شكر" in a.get("arabic", "") or "حمد" in a.get("arabic", "")][:3]
        elif mood_key == "sad":
            # Select comfort Adhkar
            selected_adhkar = [a for a in adhkar_list if "استغفر" in a.get("arabic", "") or "صبر" in a.get("arabic", "")][:3]
        elif mood_key == "anxious":
            # Select peace Adhkar
            selected_adhkar = [a for a in adhkar_list if "اللهم" in a.get("arabic", "")][:3]
        elif mood_key == "grateful":
            # Select morning Adhkar (gratitude)
            selected_adhkar = adhkar_list[:3]
        elif mood_key == "seeking_peace":
            # Select evening Adhkar (peace)
            selected_adhkar = adhkar_list[:3]
        elif mood_key == "tired":
            # Select sleep Adhkar
            selected_adhkar = adhkar_list[:3]
        
        # Fallback to first 3 if no specific matches
        if not selected_adhkar:
            selected_adhkar = adhkar_list[:3]
        
        # Build response text
        response_text = (
            f"{mood_info['emoji']} *أذكار للحالة: {mood_info['name']}*\n\n"
            f"{mood_info['description']}\n\n"
        )
        
        for i, adhkar in enumerate(selected_adhkar, 1):
            arabic = adhkar.get("arabic", "")
            translation = adhkar.get("translation", "")
            count = adhkar.get("count", "")
            
            response_text += f"**{i}. {arabic}**\n"
            if translation:
                response_text += f"{translation}\n"
            if count:
                response_text += f"التكرار: {count}\n"
            response_text += "\n"
        
        # Build keyboard
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 تغيير المزاج", callback_data="mood_adhkar_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            response_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error handling mood selection: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)
