import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from models.user import User
from keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "ai_assistant")
async def show_ai_assistant(callback: CallbackQuery, db: AsyncSession):
    """Show AI Assistant menu (inline keyboard version)"""
    await callback.answer("🤖 المساعد الذكي")
    
    user_id = callback.from_user.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.message.edit_text(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_keyboard("ar")
        )
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "🤖 *المساعد الذكي*\n\n"
        "يمكنني مساعدتك في الأسئلة الإسلامية العامة.\n\n"
        "يرجى إرسال سؤالك وسأحاول الإجابة عليه.\n\n"
        "المواضيع المتاحة:\n"
        "- الصلاة\n"
        "- القرآن الكريم\n"
        "- الأحاديث النبوية\n"
        "- الصيام\n"
        "- الزكاة\n"
        "- الحج",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


# Basic Islamic knowledge base
ISLAMIC_KNOWLEDGE = {
    "prayer": {
        "keywords": ["صلاة", "prayer", "salah", "صلاة", "مواقيت"],
        "response": "الصلاة هي الركن الثاني من أركان الإسلام. يجب على المسلم أداء الصلوات الخمس في أوقاتها:\n\n- الفجر: من طلوع الفجر إلى شروق الشمس\n- الظهر: من زوال الشمس إلى دخول وقت العصر\n- العصر: من دخول وقت العصر إلى غروب الشمس\n- المغرب: من غروب الشمس إلى مغيب الشفق الأحمر\n- العشاء: من مغيب الشفق الأحمر إلى طلوع الفجر"
    },
    "quran": {
        "keywords": ["قرآن", "quran", "قرآن", "كتاب", "book"],
        "response": "القرآن الكريم هو كلام الله تعالى، أنزله على النبي محمد ﷺ بواسطة الوحي جبريل عليه السلام. هو معجزة الإسلام الخالدة، يحتوي على 114 سورة، بدءاً بسورة الفاتحة وختاماً بسورة الناس."
    },
    "hadith": {
        "keywords": ["حديث", "hadith", "أحاديث", "prophet", "نبي"],
        "response": "الحديث النبوي هو ما أضيف إلى النبي ﷺ من قول أو فعل أو تقرير أو صفة. الأحاديث تُقسم إلى صحيح وحسن وضعيف حسب سندها ومتنها."
    },
    "fasting": {
        "keywords": ["صيام", "fasting", "رمضان", "ramadan", "صوم"],
        "response": "الصيام هو الركن الرابع من أركان الإسلام. يجب صيام شهر رمضان من الفجر إلى المغرب، يمتنع المسلم فيه عن الطعام والشراب والشهوات. يُستحب صيام أيام أخرى مثل الاثنين والخميس وأيام البيض."
    },
    "zakat": {
        "keywords": ["زكاة", "zakat", "صدقة", "charity"],
        "response": "الزكاة هي الركن الثالث من أركان الإسلام. هي واجب مالي على المسلم يُدفع للفقراء والمحتاجين. تُحسب الزكاة بنسبة 2.5% من الأموال التي حال عليها الحول."
    },
    "hajj": {
        "keywords": ["حج", "hajj", "مكة", "mecca"],
        "response": "الحج هو الركن الخامس من أركان الإسلام. يجب على المسلم المستطيع أداء الحج مرة واحدة في العمر إلى مكة المكرمة. يشمل الطواف حول الكعبة والسعي بين الصفا والمروة والوقوف بعرفة."
    },
    "greeting": {
        "keywords": ["السلام", "salam", "مرحبا", "hello", "hi"],
        "response": "وعليكم السلام ورحمة الله وبركاته! كيف يمكنني مساعدتك اليوم؟"
    }
}




async def show_ai_assistant(message: Message, db: AsyncSession):
    """Show AI Assistant menu (message version for reply keyboard)"""
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await message.answer(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_reply_keyboard("ar")
        )
        return
    
    language = user.language.value if user.language else "ar"
    
    response_text = (
        "🤖 *المساعد الذكي*\n\n"
        "يمكنني مساعدتك في الأسئلة الإسلامية العامة.\n\n"
        "يرجى إرسال سؤالك وسأحاول الإجابة عليه.\n\n"
        "المواضيع المتاحة:\n"
        "- الصلاة\n"
        "- القرآن الكريم\n"
        "- الأحاديث النبوية\n"
        "- الصيام\n"
        "- الزكاة\n"
        "- الحج"
    )
    
    await message.answer(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_reply_keyboard(language)
    )


@router.message(F.text)
async def handle_ai_query(message: Message):
    """Handle AI assistant queries"""
    query = message.text.lower()
    
    # Check if the message is a search query for Adhkar or Hadith
    # Skip if it's already handled by those modules
    if any(keyword in query for keyword in ["بحث", "search"]):
        return
    
    # Find the best matching response
    best_match = None
    best_score = 0
    
    for topic, data in ISLAMIC_KNOWLEDGE.items():
        keywords = data["keywords"]
        score = sum(1 for keyword in keywords if keyword in query)
        if score > best_score:
            best_score = score
            best_match = data["response"]
    
    if best_match and best_score > 0:
        response_text = f"🤖 *إجابة المساعد:*\\n\\n{best_match}"
    else:
        response_text = (
            "🤖 *إجابة المساعد:*\\n\\n"
            "عذراً، لم أتمكن من العثور على إجابة لسؤالك.\\n\\n"
            "يمكنك طرح سؤال حول:\\n"
            "- الصلاة\\n"
            "- القرآن الكريم\\n"
            "- الأحاديث النبوية\\n"
            "- الصيام\\n"
            "- الزكاة\\n"
            "- الحج"
        )
    
    await message.answer(response_text, parse_mode="Markdown")
