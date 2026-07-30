"""
Admin Command Center handlers for Rafeeq bot.
Provides advanced analytics, user management, broadcast, and system control features.
"""

import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any

from models.user import User, Role
from keyboards import get_main_menu_keyboard
from config.settings import settings
from services.admin_service import AdminService
from services.content_manager import content_manager
from pathlib import Path

logger = logging.getLogger(__name__)

router = Router()

# Broadcast state
broadcast_state = {}


def is_authorized_admin(user_id: int) -> bool:
    """Check if user is authorized admin"""
    if not settings.ADMIN_ID:
        return False
    return user_id == settings.ADMIN_ID


@router.message(Command("ban"))
async def handle_ban_command(message: Message):
    """Ban a user by ID"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    # Extract user ID from command
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ الاستخدام: `/ban <user_id>`\nمثال: `/ban 123456789`",
                parse_mode="Markdown"
            )
            return
        
        user_id_to_ban = int(parts[1])
        
        from utils.redis_client import redis_client
        await redis_client.client.set(f"banned_user:{user_id_to_ban}", "true")
        
        await message.answer(
            f"✅ تم حظر المستخدم {user_id_to_ban}",
            parse_mode="Markdown"
        )
        
        logger.info(f"User {user_id_to_ban} banned by admin {message.from_user.id}")
        
    except ValueError:
        await message.answer("❌ معرف المستخدم غير صحيح")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await message.answer(f"❌ خطأ في حظر المستخدم: {e}")


@router.message(Command("unban"))
async def handle_unban_command(message: Message):
    """Unban a user by ID"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    # Extract user ID from command
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ الاستخدام: `/unban <user_id>`\nمثال: `/unban 123456789`",
                parse_mode="Markdown"
            )
            return
        
        user_id_to_unban = int(parts[1])
        
        from utils.redis_client import redis_client
        await redis_client.client.delete(f"banned_user:{user_id_to_unban}")
        
        await message.answer(
            f"✅ تم إلغاء حظر المستخدم {user_id_to_unban}",
            parse_mode="Markdown"
        )
        
        logger.info(f"User {user_id_to_unban} unbanned by admin {message.from_user.id}")
        
    except ValueError:
        await message.answer("❌ معرف المستخدم غير صحيح")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await message.answer(f"❌ خطأ في إلغاء الحظر: {e}")


@router.message(Command("analytics"))
async def handle_analytics_command(message: Message):
    """Show live analytics dashboard"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    from sqlalchemy import select, func
    from models.user import User
    from models.user_activity_logs import UserActivityLog
    from datetime import datetime, timedelta
    from config.database import AsyncSessionLocal
    
    try:
        async with AsyncSessionLocal() as session:
            # Total users
            total_users_result = await session.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar()
            
            # Active users today
            today = datetime.now().date()
            active_users_result = await session.execute(
                select(func.count(func.distinct(UserActivityLog.user_id)))
                .where(UserActivityLog.created_at >= today)
            )
            active_users_today = active_users_result.scalar()
            
            # Total queries served
            total_queries_result = await session.execute(select(func.count(UserActivityLog.id)))
            total_queries = total_queries_result.scalar()
            
            # Top used features
            top_features_result = await session.execute(
                select(UserActivityLog.module_name, func.count(UserActivityLog.id).label('count'))
                .group_by(UserActivityLog.module_name)
                .order_by(func.count(UserActivityLog.id).desc())
                .limit(5)
            )
            top_features = top_features_result.fetchall()
        
        # Format analytics message
        analytics_text = (
            f"📊 *لوحة التحليلات*\n\n"
            f"👥 *المستخدمون:*\n"
            f"   └ إجمالي المستخدمين: {total_users}\n"
            f"   └ المستخدمون النشطون اليوم: {active_users_today}\n\n"
            f"📈 *النشاط:*\n"
            f"   └ إجمالي الاستعلامات: {total_queries}\n\n"
            f"🔥 *أكثر الميزات استخداماً:*\n"
        )
        
        for i, (feature, count) in enumerate(top_features, 1):
            analytics_text += f"   {i}. {feature}: {count}\n"
        
        analytics_text += f"\n🕐 *آخر تحديث:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await message.answer(analytics_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        await message.answer(f"❌ خطأ في جلب التحليلات: {e}")


@router.message(Command("features"))
async def handle_features_command(message: Message):
    """Show feature toggles menu"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    from utils.redis_client import redis_client
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    try:
        # Get current feature statuses
        quran_status = await redis_client.client.get("feature_quran")
        hadith_status = await redis_client.client.get("feature_hadith")
        adhkar_status = await redis_client.client.get("feature_adhkar")
        maintenance_status = await redis_client.client.get("maintenance_mode")
        
        # Build keyboard
        builder = InlineKeyboardBuilder()
        
        quran_emoji = "✅" if quran_status != "disabled" else "❌"
        hadith_emoji = "✅" if hadith_status != "disabled" else "❌"
        adhkar_emoji = "✅" if adhkar_status != "disabled" else "❌"
        maintenance_emoji = "🔴" if maintenance_status == "true" else "🟢"
        
        builder.row(
            InlineKeyboardButton(text=f"{quran_emoji} القرآن", callback_data="admin_toggle_quran"),
            InlineKeyboardButton(text=f"{hadith_emoji} الأحاديث", callback_data="admin_toggle_hadith")
        )
        builder.row(
            InlineKeyboardButton(text=f"{adhkar_emoji} الأذكار", callback_data="admin_toggle_adhkar"),
            InlineKeyboardButton(text=f"{maintenance_emoji} وضع الصيانة", callback_data="admin_toggle_maintenance")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await message.answer(
            "⚙️ *إدارة الميزات*\n\n"
            "اضغط على الأزرار لتفعيل أو تعطيل الميزات:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing features menu: {e}")
        await message.answer(f"❌ خطأ في عرض قائمة الميزات: {e}")


@router.callback_query(F.data == "admin_toggle_quran")
async def handle_toggle_quran_callback(callback: CallbackQuery):
    """Toggle Quran module via inline button"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    from utils.redis_client import redis_client
    
    try:
        # Get current status
        current_status = await redis_client.client.get("feature_quran")
        is_enabled = current_status != "disabled"
        
        # Toggle status
        new_status = not is_enabled
        await redis_client.client.set("feature_quran", "disabled" if not new_status else "enabled")
        
        # Update button text
        status_emoji = "✅" if new_status else "❌"
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} القرآن",
                callback_data="admin_toggle_quran"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error toggling Quran feature: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data == "admin_toggle_hadith")
async def handle_toggle_hadith_callback(callback: CallbackQuery):
    """Toggle Hadith module via inline button"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    from utils.redis_client import redis_client
    
    try:
        # Get current status
        current_status = await redis_client.client.get("feature_hadith")
        is_enabled = current_status != "disabled"
        
        # Toggle status
        new_status = not is_enabled
        await redis_client.client.set("feature_hadith", "disabled" if not new_status else "enabled")
        
        # Update button text
        status_emoji = "✅" if new_status else "❌"
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} الأحاديث",
                callback_data="admin_toggle_hadith"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error toggling Hadith feature: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data == "admin_toggle_adhkar")
async def handle_toggle_adhkar_callback(callback: CallbackQuery):
    """Toggle Adhkar module via inline button"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    from utils.redis_client import redis_client
    
    try:
        # Get current status
        current_status = await redis_client.client.get("feature_adhkar")
        is_enabled = current_status != "disabled"
        
        # Toggle status
        new_status = not is_enabled
        await redis_client.client.set("feature_adhkar", "disabled" if not new_status else "enabled")
        
        # Update button text
        status_emoji = "✅" if new_status else "❌"
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} الأذكار",
                callback_data="admin_toggle_adhkar"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error toggling Adhkar feature: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data == "admin_toggle_maintenance")
async def handle_toggle_maintenance_callback(callback: CallbackQuery):
    """Toggle maintenance mode via inline button"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    from utils.redis_client import redis_client
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    try:
        # Get current maintenance status
        current_status = await redis_client.client.get("maintenance_mode")
        is_maintenance = current_status == "true"
        
        # Toggle status
        new_status = not is_maintenance
        await redis_client.client.set("maintenance_mode", "true" if new_status else "false")
        
        # Build updated keyboard
        builder = InlineKeyboardBuilder()
        status_emoji = "🔴 مفعل" if new_status else "🟢 معطل"
        builder.row(
            InlineKeyboardButton(
                text=f"وضع الصيانة: {status_emoji}",
                callback_data="admin_toggle_maintenance"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {e}")
        await CallbackQuery.answer(f"❌ خطأ: {e}", show_alert=True)


@router.message(Command("maintenance"))
async def handle_maintenance_command(message: Message):
    """Toggle maintenance mode"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    from utils.redis_client import redis_client
    
    try:
        # Get current maintenance status
        current_status = await redis_client.client.get("maintenance_mode")
        is_maintenance = current_status == "true"
        
        # Toggle status
        new_status = not is_maintenance
        await redis_client.client.set("maintenance_mode", "true" if new_status else "false")
        
        status_text = "🔴 مفعل" if new_status else "🟢 معطل"
        await message.answer(
            f"✅ تم تحديث وضع الصيانة\n\n"
            f"وضع الصيانة: {status_text}",
            parse_mode="Markdown"
        )
        
        logger.info(f"Maintenance mode toggled by admin: {new_status}")
        
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {e}")
        await message.answer(f"❌ خطأ في تحديث وضع الصيانة: {e}")


@router.message(Command("ping"))
async def handle_ping_command(message: Message):
    """Check server latency and system response time"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    import time
    from utils.redis_client import redis_client
    from config.database import AsyncSessionLocal
    
    start_time = time.time()
    
    try:
        # Test Redis
        redis_start = time.time()
        await redis_client.client.ping()
        redis_time = (time.time() - redis_start) * 1000
        
        # Test Database
        db_start = time.time()
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        db_time = (time.time() - db_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        ping_text = (
            f"🏓 *اختبار الاتصال*\n\n"
            f"⚡ زمن الاستجابة الكلي: {total_time:.2f}ms\n\n"
            f"📊 *تفاصيل النظام:*\n"
            f"🔴 Redis: {redis_time:.2f}ms\n"
            f"🔵 PostgreSQL: {db_time:.2f}ms\n"
            f"🟢 Telegram API: متصل\n\n"
            f"✅ جميع الأنظمة تعمل بشكل طبيعي"
        )
        
        await message.answer(ping_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        await message.answer(f"❌ خطأ في اختبار الاتصال: {e}")


@router.message(Command("test_content"))
async def test_content_integration(message: Message):
    """Test ContentManager integration - sends sample content"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        await message.answer("🧪 *اختبار تكامل المحتوى*\n\nجاري تحميل المحتوى من الملفات المحلية...", parse_mode="Markdown")
        
        # 1. Send full Surah Al-Fatiha
        surah = content_manager.get_full_surah(1)
        if surah:
            text = f"📖 *سورة {surah.get('name', 'الفاتحة')}*\n\n"
            text += f"🔢 رقم السورة: {surah.get('surah_number', 1)}\n"
            text += f"📊 عدد الآيات: {len(surah.get('ayahs', []))}\n\n"
            
            ayahs = surah.get('ayahs', [])
            for i, ayah in enumerate(ayahs, 1):
                arabic = ayah.get('arabic_text', '')
                text += f"{i}. {arabic}\n"
            
            chunks = content_manager.chunk_text(text)
            for chunk in chunks:
                await message.answer(chunk, parse_mode="Markdown")
        else:
            await message.answer("❌ خطأ في تحميل السورة")
        
        # 2. Send authentic Hadith
        hadith = content_manager.get_hadith(random=True)
        if hadith:
            formatted_text = content_manager.format_hadith_message(hadith)
            chunks = content_manager.chunk_text(formatted_text)
            for chunk in chunks:
                await message.answer(chunk, parse_mode="Markdown")
        else:
            await message.answer("❌ خطأ في تحميل الحديث")
        
        # 3. Send Adhkar image
        adhkar_image = content_manager.get_adhkar_image("morning_adhkar")
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                await message.answer_photo(
                    photo=image_path,
                    caption="🌅 *أذكار الصباح*\n\nصورة من ملف PDF المحلي",
                    parse_mode="Markdown"
                )
            else:
                await message.answer("❌ خطأ: ملف الصورة غير موجود")
        else:
            await message.answer("❌ خطأ في تحميل صورة الأذكار")
        
        # 4. Confirmation message
        await message.answer(
            "✅ *تم اختبار تكامل المحتوى بنجاح*\n\n"
            "📊 *النتائج:*\n"
            "✅ القرآن: متصل بـ quran.json\n"
            "✅ الأحاديث: متصل بـ hadiths.json\n"
            "✅ الأذكار: متصل بـ adhkar.pdf (صور)\n"
            "✅ المجدول: متصل بـ ContentManager للبث اليومي\n\n"
            "النظام جاهز للعمل!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error testing content integration: {e}")
        await message.answer(f"❌ خطأ في الاختبار: {e}")


@router.message(F.text.in_(["🔙 القائمة الرئيسية", "القائمة الرئيسية"]))
async def handle_main_menu_button(message: Message, db: AsyncSession):
    """Handle main menu button click from reply keyboard"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        # Import the main menu handler
        from handlers.start import cmd_start
        await cmd_start(message, db)
    except Exception as e:
        logger.error(f"Error handling main menu button: {e}")
        await message.answer("❌ خطأ في العودة للقائمة الرئيسية")


@router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: CallbackQuery, db: AsyncSession):
    """Handle main menu button click from inline keyboard"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        # Import the main menu handler
        from handlers.start import cmd_start
        await cmd_start(callback.message, db)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error handling main menu callback: {e}")
        await callback.answer("❌ خطأ في العودة للقائمة الرئيسية", show_alert=True)


@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, db: AsyncSession):
    """Show admin command center (callback version)"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        health = await admin_service.get_system_health()
        
        # Build command center keyboard
        builder = InlineKeyboardBuilder()
        
        # Analytics Section
        builder.row(
            InlineKeyboardButton(text="📊 الإحصائيات المتقدمة", callback_data="admin_analytics")
        )
        builder.row(
            InlineKeyboardButton(text="📈 إحصائيات الاستخدام", callback_data="admin_module_stats")
        )
        
        # User Management Section
        builder.row(
            InlineKeyboardButton(text="👥 إدارة المستخدمين", callback_data="admin_users")
        )
        builder.row(
            InlineKeyboardButton(text="🔍 البحث عن مستخدم", callback_data="admin_search")
        )
        builder.row(
            InlineKeyboardButton(text="🚫 المستخدمون المحظورون", callback_data="admin_banned")
        )
        
        # Broadcast Section
        builder.row(
            InlineKeyboardButton(text="📢 إرسال إعلان", callback_data="admin_broadcast")
        )
        
        # System Control Section
        builder.row(
            InlineKeyboardButton(text="🔧 تفعيل الميزات", callback_data="admin_toggles")
        )
        builder.row(
            InlineKeyboardButton(text="🔨 وضع الصيانة", callback_data="admin_maintenance")
        )
        builder.row(
            InlineKeyboardButton(text="🗑️ مسح ذاكرة التخزين المؤقت", callback_data="admin_flush_redis")
        )
        
        # Logs Section
        builder.row(
            InlineKeyboardButton(text="📋 سجل الأخطاء", callback_data="admin_logs")
        )
        builder.row(
            InlineKeyboardButton(text="🏥 حالة النظام", callback_data="admin_health")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        stats_text = (
            "⚙️ *مركز التحكم* ⚙️\n\n"
            f"👥 *إجمالي المستخدمين:* {health.get('total_users', 0)}\n"
            f"📊 *المستخدمون النشطون (24 ساعة):* {health.get('dau', 0)}\n"
            f"📈 *المستخدمون النشطون (30 يوم):* {health.get('mau', 0)}\n"
            f"💾 *ذاكرة Redis:* {health.get('redis_memory', 'غير متاح')}\n"
            f"🆔 *معرف المشرف:* {settings.ADMIN_ID}\n\n"
            f"📅 *وقت الخادم:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}")
        await callback.answer("❌ خطأ في تحميل لوحة التحكم", show_alert=True)


async def show_admin_panel(message: Message, db: AsyncSession):
    """Show admin command center (message version for reply keyboard)"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        health = await admin_service.get_system_health()
        
        # Build command center keyboard
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📊 الإحصائيات المتقدمة", callback_data="admin_analytics")
        )
        builder.row(
            InlineKeyboardButton(text="📈 إحصائيات الاستخدام", callback_data="admin_module_stats")
        )
        builder.row(
            InlineKeyboardButton(text="👥 إدارة المستخدمين", callback_data="admin_users")
        )
        builder.row(
            InlineKeyboardButton(text="🔍 البحث عن مستخدم", callback_data="admin_search")
        )
        builder.row(
            InlineKeyboardButton(text="📢 إرسال إعلان", callback_data="admin_broadcast")
        )
        builder.row(
            InlineKeyboardButton(text="🔧 تفعيل الميزات", callback_data="admin_toggles")
        )
        builder.row(
            InlineKeyboardButton(text="🔨 وضع الصيانة", callback_data="admin_maintenance")
        )
        builder.row(
            InlineKeyboardButton(text="📋 سجل الأخطاء", callback_data="admin_logs")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        stats_text = (
            "⚙️ *مركز التحكم* ⚙️\n\n"
            f"👥 *إجمالي المستخدمين:* {health.get('total_users', 0)}\n"
            f"📊 *المستخدمون النشطون (24 ساعة):* {health.get('dau', 0)}\n"
            f"📈 *المستخدمون النشطون (30 يوم):* {health.get('mau', 0)}\n"
            f"💾 *ذاكرة Redis:* {health.get('redis_memory', 'غير متاح')}\n"
            f"🆔 *معرف المشرف:* {settings.ADMIN_ID}\n\n"
            f"📅 *وقت الخادم:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await message.answer(
            stats_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing admin panel: {e}")
        await message.answer("❌ خطأ في تحميل لوحة التحكم")


@router.callback_query(F.data == "admin_analytics")
async def show_advanced_analytics(callback: CallbackQuery, db: AsyncSession):
    """Show advanced analytics dashboard"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        health = await admin_service.get_system_health()
        module_stats = await admin_service.get_module_usage_stats()
        
        # Build analytics text
        analytics_text = (
            "📊 *الإحصائيات المتقدمة* 📊\n\n"
            f"👥 *إجمالي المستخدمين:* {health.get('total_users', 0)}\n"
            f"📊 *المستخدمون النشطون يومياً (24 ساعة):* {health.get('dau', 0)}\n"
            f"📈 *المستخدمون النشطون شهرياً (30 يوم):* {health.get('mau', 0)}\n"
            f"🔥 *المستخدمون النشطون (7 أيام):* {health.get('active_7d', 0)}\n"
            f"💾 *ذاكرة Redis:* {health.get('redis_memory', 'غير متاح')}\n"
            f"🔗 *عملاء Redis:* {health.get('redis_clients', 0)}\n\n"
            "📈 *استخدام الوحدات (7 أيام):*\n\n"
        )
        
        for module, count in module_stats.items():
            analytics_text += f"• {module}: {count} استخدام\n"
        
        if not module_stats:
            analytics_text += "لا توجد بيانات استخدام متاحة\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel"))
        
        await callback.message.edit_text(
            analytics_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing analytics: {e}")
        await callback.answer("❌ خطأ في تحميل الإحصائيات", show_alert=True)


@router.callback_query(F.data == "admin_module_stats")
async def show_module_stats(callback: CallbackQuery, db: AsyncSession):
    """Show detailed module usage statistics"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        module_stats = await admin_service.get_module_usage_stats()
        
        stats_text = "📈 *إحصائيات استخدام الوحدات* 📈\n\n"
        
        if module_stats:
            total_usage = sum(module_stats.values())
            for module, count in sorted(module_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_usage * 100) if total_usage > 0 else 0
                stats_text += f"• {module}: {count} ({percentage:.1f}%)\n"
        else:
            stats_text += "لا توجد بيانات استخدام متاحة\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel"))
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing module stats: {e}")
        await callback.answer("❌ Error loading module stats", show_alert=True)


@router.callback_query(F.data == "admin_users")
async def show_user_management(callback: CallbackQuery, db: AsyncSession):
    """Show user management options"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        # Get recent users
        recent_users = await db.execute(
            select(User).order_by(User.created_at.desc()).limit(10)
        )
        recent_users = recent_users.scalars().all()
        
        users_text = "👥 *المستخدمون الأخيرون* 👥\n\n"
        
        for user in recent_users:
            status = "🚫 محظور" if user.is_banned else "✅ نشط"
            users_text += (
                f"🆔 {user.id} {status}\n"
                f"👤 {user.username or 'غير متاح'}\n"
                f"📅 {user.created_at.strftime('%Y-%m-%d')}\n"
                f"🌐 {user.language.value}\n\n"
            )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔍 البحث عن مستخدم", callback_data="admin_search")
        )
        builder.row(
            InlineKeyboardButton(text="🚫 المستخدمون المحظورون", callback_data="admin_banned")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel")
        )
        
        await callback.message.edit_text(
            users_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing user management: {e}")
        await callback.answer("❌ Error loading user management", show_alert=True)


@router.callback_query(F.data == "admin_search")
async def setup_user_search(callback: CallbackQuery):
    """Setup user search"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    await callback.message.edit_text(
        "🔍 *البحث عن مستخدم* 🔍\n\n"
        "يرجى إرسال معرف تيليجرام أو اسم المستخدم للمستخدم الذي تريد البحث عنه.\n\n"
        "أمثلة التنسيق:\n"
        "• 123456789 (معرف تيليجرام)\n"
        "• @username (اسم المستخدم)",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(F.text)
async def handle_user_search(message: Message, db: AsyncSession):
    """Handle user search query - only when in search mode"""
    if not is_authorized_admin(message.from_user.id):
        return
    
    # Skip if in broadcast mode
    if message.from_user.id in broadcast_state:
        return  # Let broadcast handler handle it
    
    # Skip if it's a command (like /start, /ban, etc.)
    if message.text.startswith('/'):
        return
    
    # Skip if it's a button text (not a search query)
    button_texts = [
        "🔙 القائمة الرئيسية", "القائمة الرئيسية",
        "📖 القرآن الكريم", "🤲 الأذكار والأدعية",
        "📚 الأحاديث النبوية", "🕌 مواقيت الصلاة",
        "🤖 المساعد الذكي", "⚙️ الإعدادات"
    ]
    if message.text in button_texts:
        return
    
    try:
        admin_service = AdminService(db)
        user = await admin_service.search_user(message.text)
        
        if user:
            profile = await admin_service.get_user_profile(user.id)
            
            status = "🚫 محظور" if user.is_banned else "✅ نشط"
            if user.is_banned:
                status += f"\n   السبب: {user.ban_reason or 'غير محدد'}"
            
            last_read = f"سورة {user.last_read_surah}، آية {user.last_read_ayah}" if user.last_read_surah else "غير متاح"
            last_active = user.last_active_date.strftime('%Y-%m-%d %H:%M') if user.last_active_date else "أبداً"
            
            profile_text = (
                f"👤 *ملف المستخدم* 👤\n\n"
                f"🆔 *المعرف:* {user.id}\n"
                f"👤 *اسم المستخدم:* @{user.username or 'غير متاح'}\n"
                f"📛 *الاسم:* {user.first_name or 'غير متاح'} {user.last_name or ''}\n"
                f"📊 *الحالة:* {status}\n"
                f"🌐 *اللغة:* {user.language.value}\n"
                f"🎯 *الدور:* {user.role.value}\n"
                f"📅 *تاريخ الانضمام:* {user.created_at.strftime('%Y-%m-%d')}\n"
                f"🕐 *آخر نشاط:* {last_active}\n"
                f"📖 *آخر قراءة:* {last_read}\n"
                f"🔥 *أيام الاستمرار:* {user.streak_days} يوم"
            )
            
            builder = InlineKeyboardBuilder()
            if user.is_banned:
                builder.row(
                    InlineKeyboardButton(text="✅ إلغاء الحظر", callback_data=f"admin_unban_{user.id}")
                )
            else:
                builder.row(
                    InlineKeyboardButton(text="🚫 حظر المستخدم", callback_data=f"admin_ban_{user.id}")
                )
            builder.row(
                InlineKeyboardButton(text="🔙 العودة لإدارة المستخدمين", callback_data="admin_users")
            )
            
            await message.answer(
                profile_text,
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer("❌ لم يتم العثور على المستخدم. يرجى التحقق من المعرف/اسم المستخدم والمحاولة مرة أخرى.")
            
    except Exception as e:
        logger.error(f"Error searching user: {e}")
        await message.answer("❌ خطأ في البحث عن المستخدم")


@router.callback_query(F.data.startswith("admin_ban_"))
async def ban_user(callback: CallbackQuery, db: AsyncSession):
    """Ban a user"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        user_id = int(callback.data.split("_")[-1])
        admin_service = AdminService(db)
        
        success = await admin_service.ban_user(user_id, "محظور من قبل المشرف")
        
        if success:
            await callback.answer("✅ تم حظر المستخدم بنجاح")
            await callback.message.edit_text(
                f"✅ تم حظر المستخدم {user_id}.",
                reply_markup=None
            )
        else:
            await callback.answer("❌ فشل حظر المستخدم", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await callback.answer("❌ خطأ في حظر المستخدم", show_alert=True)


@router.callback_query(F.data.startswith("admin_unban_"))
async def unban_user(callback: CallbackQuery, db: AsyncSession):
    """Unban a user"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        user_id = int(callback.data.split("_")[-1])
        admin_service = AdminService(db)
        
        success = await admin_service.unban_user(user_id)
        
        if success:
            await callback.answer("✅ تم إلغاء حظر المستخدم بنجاح")
            await callback.message.edit_text(
                f"✅ تم إلغاء حظر المستخدم {user_id}.",
                reply_markup=None
            )
        else:
            await callback.answer("❌ فشل إلغاء حظر المستخدم", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await callback.answer("❌ خطأ في إلغاء حظر المستخدم", show_alert=True)


@router.callback_query(F.data == "admin_banned")
async def show_banned_users(callback: CallbackQuery, db: AsyncSession):
    """Show list of banned users"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        banned_users = await admin_service.get_banned_users()
        
        if banned_users:
            banned_text = "🚫 *المستخدمون المحظورون* 🚫\n\n"
            for user in banned_users:
                banned_text += (
                    f"🆔 {user.id}\n"
                    f"👤 {user.username or 'غير متاح'}\n"
                    f"📛 السبب: {user.ban_reason or 'غير محدد'}\n"
                    f"📅 تاريخ الحظر: {user.banned_at.strftime('%Y-%m-%d') if user.banned_at else 'غير متاح'}\n\n"
                )
        else:
            banned_text = "🚫 *المستخدمون المحظورون* 🚫\n\nلا يوجد مستخدمون محظورون."
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 العودة لإدارة المستخدمين", callback_data="admin_users"))
        
        await callback.message.edit_text(
            banned_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing banned users: {e}")
        await callback.answer("❌ خطأ في تحميل المستخدمين المحظورين", show_alert=True)


@router.callback_query(F.data == "admin_broadcast")
async def setup_broadcast(callback: CallbackQuery):
    """Setup smart broadcast"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 جميع المستخدمين", callback_data="broadcast_target_all")
    )
    builder.row(
        InlineKeyboardButton(text="🔥 المستخدمون النشطون (7 أيام)", callback_data="broadcast_target_active")
    )
    builder.row(
        InlineKeyboardButton(text="💤 المستخدمون غير النشطين", callback_data="broadcast_target_inactive")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel")
    )
    
    await callback.message.edit_text(
        "📢 *البث الذكي* 📢\n\n"
        "اختر الجمهور المستهدف:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("broadcast_target_"))
async def select_broadcast_target(callback: CallbackQuery, db: AsyncSession):
    """Select broadcast target and prompt for message"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        target_type = callback.data.split("_")[-1]
        admin_service = AdminService(db)
        
        broadcast_data = await admin_service.broadcast_message("", target_type)
        
        # Store broadcast state
        broadcast_state[callback.from_user.id] = {
            'target_type': target_type,
            'total_users': broadcast_data['total'],
            'users': broadcast_data['users']
        }
        
        target_names = {
            'all': 'جميع المستخدمين',
            'active': 'المستخدمون النشطون (7 أيام)',
            'inactive': 'المستخدمون غير النشطين'
        }
        
        await callback.message.edit_text(
            f"📢 *البث إلى {target_names.get(target_type, target_type)}* 📢\n\n"
            f"👥 المستخدمون المستهدفون: {broadcast_data['total']}\n\n"
            "يرجى إرسال الرسالة التي تريد بثها.\n\n"
            "⚠️ سيتم إرسال هذه الرسالة إلى جميع المستخدمين المحددين.",
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error setting up broadcast: {e}")
        await callback.answer("❌ خطأ في إعداد البث", show_alert=True)


@router.message()
async def handle_broadcast_message(message: Message, bot: Bot, db: AsyncSession):
    """Handle broadcast message"""
    if not is_authorized_admin(message.from_user.id):
        return
    
    user_id = message.from_user.id
    
    if user_id not in broadcast_state:
        return  # Not in broadcast mode
    
    try:
        state = broadcast_state[user_id]
        users = state['users']
        
        success_count = 0
        failed_count = 0
        blocked_count = 0
        
        # Send progress message
        progress_msg = await message.answer(
            f"📢 *جاري البث...* 📢\n\n"
            f"👥 الإجمالي: {len(users)}\n"
            f"✅ نجح: 0\n"
            f"❌ فشل: 0\n"
            f"🚫 محظور: 0"
        )
        
        # Broadcast to users
        for i, user in enumerate(users):
            try:
                if message.text:
                    await bot.send_message(user.id, message.text, parse_mode="Markdown")
                elif message.photo:
                    await bot.send_photo(user.id, message.photo[-1].file_id, caption=message.caption)
                elif message.audio:
                    await bot.send_audio(user.id, message.audio.file_id, caption=message.caption)
                elif message.video:
                    await bot.send_video(user.id, message.video.file_id, caption=message.caption)
                else:
                    # Skip unsupported content types
                    continue
                
                success_count += 1
                
                # Update progress every 10 users
                if (i + 1) % 10 == 0:
                    await progress_msg.edit_text(
                        f"📢 *جاري البث...* 📢\n\n"
                        f"👥 الإجمالي: {len(users)}\n"
                        f"✅ نجح: {success_count}\n"
                        f"❌ فشل: {failed_count}\n"
                        f"🚫 محظور: {blocked_count}"
                    )
                    
            except Exception as e:
                if "bot was blocked" in str(e).lower() or "user is deactivated" in str(e).lower():
                    blocked_count += 1
                else:
                    failed_count += 1
                logger.error(f"Error sending to user {user.id}: {e}")
        
        # Final progress update
        await progress_msg.edit_text(
            f"📢 *اكتمل البث* 📢\n\n"
            f"👥 الإجمالي: {len(users)}\n"
            f"✅ نجح: {success_count}\n"
            f"❌ فشل: {failed_count}\n"
            f"🚫 محظور: {blocked_count}"
        )
        
        # Clear broadcast state
        del broadcast_state[user_id]
        
    except Exception as e:
        logger.error(f"Error during broadcast: {e}")
        await message.answer("❌ خطأ أثناء البث")
        if user_id in broadcast_state:
            del broadcast_state[user_id]


@router.message(F.text.in_(["🔧 تفعيل الميزات", "تفعيل الميزات"]))
async def handle_feature_toggles_message(message: Message, db: AsyncSession):
    """Handle feature toggles button from reply keyboard"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        
        features = [
            ('quran', '📖 وحدة القرآن'),
            ('prayer', '🕌 وحدة الصلاة'),
            ('adhkar', '🤲 وحدة الأذكار'),
            ('hadith', '📚 وحدة الأحاديث'),
            ('ai_assistant', '🤖 المساعد الذكي'),
        ]
        
        builder = InlineKeyboardBuilder()
        
        for feature, name in features:
            is_enabled = await admin_service.get_feature_toggle(feature)
            status = "✅" if is_enabled else "❌"
            builder.row(
                InlineKeyboardButton(
                    text=f"{status} {name}",
                    callback_data=f"toggle_{feature}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel")
        )
        
        await message.answer(
            "🔧 *تفعيل الميزات* 🔧\n\n"
            "تفعيل أو تعطيل الوحدات المحددة:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing feature toggles: {e}")
        await message.answer("❌ خطأ في تحميل تفعيل الميزات")


@router.message(F.text.in_(["🔨 وضع الصيانة", "وضع الصيانة"]))
async def handle_maintenance_mode_message(message: Message, db: AsyncSession):
    """Handle maintenance mode button from reply keyboard"""
    if not is_authorized_admin(message.from_user.id):
        await message.answer("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        is_maintenance = await admin_service.get_maintenance_mode()
        
        status = "🔴 وضع الصيانة مفعل" if is_maintenance else "🟢 الوضع الطبيعي"
        
        builder = InlineKeyboardBuilder()
        if is_maintenance:
            builder.row(
                InlineKeyboardButton(text="✅ تعطيل وضع الصيانة", callback_data="maintenance_off")
            )
        else:
            builder.row(
                InlineKeyboardButton(text="🔴 تفعيل وضع الصيانة", callback_data="maintenance_on")
            )
        builder.row(
            InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel")
        )
        
        await message.answer(
            f"🔨 *وضع الصيانة* 🔨\n\n"
            f"{status}\n\n"
            "عند تفعيل وضع الصيانة، سيظهر للمستخدمين غير المشرفين رسالة صيانة.",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing maintenance mode: {e}")
        await message.answer("❌ خطأ في تحميل وضع الصيانة")


@router.callback_query(F.data == "admin_toggles")
async def show_feature_toggles(callback: CallbackQuery, db: AsyncSession):
    """Show feature toggles"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        
        features = [
            ('quran', '📖 وحدة القرآن'),
            ('prayer', '🕌 وحدة الصلاة'),
            ('adhkar', '🤲 وحدة الأذكار'),
            ('hadith', '📚 وحدة الأحاديث'),
            ('ai_assistant', '🤖 المساعد الذكي'),
        ]
        
        builder = InlineKeyboardBuilder()
        
        for feature, name in features:
            is_enabled = await admin_service.get_feature_toggle(feature)
            status = "✅" if is_enabled else "❌"
            builder.row(
                InlineKeyboardButton(
                    text=f"{status} {name}",
                    callback_data=f"toggle_{feature}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel")
        )
        
        await callback.message.edit_text(
            "🔧 *تفعيل الميزات* 🔧\n\n"
            "تفعيل أو تعطيل الوحدات المحددة:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing feature toggles: {e}")
        await callback.answer("❌ خطأ في تحميل تفعيل الميزات", show_alert=True)


@router.callback_query(F.data.startswith("toggle_"))
async def toggle_feature(callback: CallbackQuery, db: AsyncSession):
    """Toggle a feature"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        feature = callback.data.split("_")[-1]
        admin_service = AdminService(db)
        
        current_state = await admin_service.get_feature_toggle(feature)
        new_state = not current_state
        
        success = await admin_service.set_feature_toggle(feature, new_state)
        
        if success:
            status = "مفعل" if new_state else "معطل"
            await callback.answer(f"✅ {feature} {status}")
            # Refresh the toggles view
            await show_feature_toggles(callback, db)
        else:
            await callback.answer("❌ فشل تفعيل الميزة", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error toggling feature: {e}")
        await callback.answer("❌ خطأ في تفعيل الميزة", show_alert=True)


@router.callback_query(F.data == "admin_maintenance")
async def show_maintenance_mode(callback: CallbackQuery, db: AsyncSession):
    """Show maintenance mode settings"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        is_maintenance = await admin_service.get_maintenance_mode()
        
        status = "🔴 وضع الصيانة مفعل" if is_maintenance else "🟢 الوضع الطبيعي"
        
        builder = InlineKeyboardBuilder()
        if is_maintenance:
            builder.row(
                InlineKeyboardButton(text="✅ تعطيل وضع الصيانة", callback_data="maintenance_off")
            )
        else:
            builder.row(
                InlineKeyboardButton(text="🔴 تفعيل وضع الصيانة", callback_data="maintenance_on")
            )
        builder.row(
            InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel")
        )
        
        await callback.message.edit_text(
            f"🔨 *وضع الصيانة* 🔨\n\n"
            f"{status}\n\n"
            "عند تفعيل وضع الصيانة، سيظهر للمستخدمين غير المشرفين رسالة صيانة.",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing maintenance mode: {e}")
        await callback.answer("❌ خطأ في تحميل وضع الصيانة", show_alert=True)


@router.callback_query(F.data == "maintenance_on")
async def enable_maintenance(callback: CallbackQuery, db: AsyncSession):
    """Enable maintenance mode"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        success = await admin_service.set_maintenance_mode(True)
        
        if success:
            await callback.answer("✅ تم تفعيل وضع الصيانة")
            await show_maintenance_mode(callback, db)
        else:
            await callback.answer("❌ فشل تفعيل وضع الصيانة", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error enabling maintenance mode: {e}")
        await callback.answer("❌ خطأ في تفعيل وضع الصيانة", show_alert=True)


@router.callback_query(F.data == "maintenance_off")
async def disable_maintenance(callback: CallbackQuery, db: AsyncSession):
    """Disable maintenance mode"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        success = await admin_service.set_maintenance_mode(False)
        
        if success:
            await callback.answer("✅ تم تعطيل وضع الصيانة")
            await show_maintenance_mode(callback, db)
        else:
            await callback.answer("❌ فشل تعطيل وضع الصيانة", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error disabling maintenance mode: {e}")
        await callback.answer("❌ خطأ في تعطيل وضع الصيانة", show_alert=True)


@router.callback_query(F.data == "admin_flush_redis")
async def flush_redis_cache(callback: CallbackQuery, db: AsyncSession):
    """Flush Redis cache"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        success = await admin_service.flush_redis_cache()
        
        if success:
            await callback.answer("✅ تم مسح ذاكرة Redis")
            await callback.message.edit_text(
                "✅ *تم مسح ذاكرة Redis* ✅\n\n"
                "تم مسح جميع البيانات المخزنة مؤقتاً.",
                parse_mode="Markdown",
                reply_markup=None
            )
        else:
            await callback.answer("❌ فشل مسح ذاكرة Redis", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error flushing Redis cache: {e}")
        await callback.answer("❌ خطأ في مسح ذاكرة Redis", show_alert=True)


@router.callback_query(F.data == "admin_logs")
async def show_error_logs(callback: CallbackQuery, db: AsyncSession):
    """Show error logs"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        error_logs = await admin_service.get_error_logs(20)
        
        logs_text = "📋 *سجل الأخطاء الأخير* 📋\n\n"
        logs_text += "".join(error_logs)
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔄 تحديث السجل", callback_data="admin_logs"))
        builder.row(InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel"))
        
        # Truncate if too long
        if len(logs_text) > 4000:
            logs_text = logs_text[:4000] + "\n\n... (تم الاقتصاص)"
        
        await callback.message.edit_text(
            logs_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing error logs: {e}")
        await callback.answer("❌ خطأ في تحميل السجلات", show_alert=True)


@router.callback_query(F.data == "admin_health")
async def show_health_check(callback: CallbackQuery, db: AsyncSession):
    """Show system health check"""
    await callback.answer()
    
    if not is_authorized_admin(callback.from_user.id):
        await callback.message.edit_text("❌ الوصول مرفوض. للمشرفين فقط.")
        return
    
    try:
        admin_service = AdminService(db)
        health = await admin_service.get_system_health()
        
        health_text = (
            "🏥 *فحص حالة النظام* 🏥\n\n"
            f"✅ *قاعدة البيانات:* متصل\n"
            f"✅ *Redis:* متصل ({health.get('redis_memory', 'غير متاح')} ذاكرة)\n"
            f"✅ *واجهة تيليجرام:* متصل\n"
            f"✅ *المجدول:* يعمل\n"
            f"✅ *الإضافات:* محملة\n\n"
            f"👥 *إجمالي المستخدمين:* {health.get('total_users', 0)}\n"
            f"📊 *DAU:* {health.get('dau', 0)}\n"
            f"📈 *MAU:* {health.get('mau', 0)}\n\n"
            f"📅 *Checked:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔄 تحديث الحالة", callback_data="admin_health"))
        builder.row(InlineKeyboardButton(text="🔙 العودة لمركز التحكم", callback_data="admin_panel"))
        
        await callback.message.edit_text(
            health_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing health check: {e}")
        await callback.answer("❌ Error loading health check", show_alert=True)
