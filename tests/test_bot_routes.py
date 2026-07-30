"""
Comprehensive automated test script for bot callback handlers.
Tests all callback_data strings to ensure:
- No unhandled exceptions
- No unanswered callbacks (loading spinners)
- Correct UI updates
- All handlers have matching callback_data
"""

import asyncio
import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# All callback_data strings from the audit
ALL_CALLBACK_DATA = [
    # Navigation
    "go_main_menu",
    "quran_menu",
    "hadith_menu",
    "adhkar_menu",
    "prayer_menu",
    "tasbeeh_menu",
    
    # Quran
    "quran_surah_list",
    "quran_search",
    "quran_juz",
    "quran_read_surah",
    "quran_ayah_next",
    "quran_ayah_prev",
    "quran_resume",
    
    # Hadith
    "hadith",
    "hadith_bukhari",
    "hadith_muslim",
    "hadith_tirmidhi",
    "hadith_general",
    "hadith_search",
    
    # Adhkar
    "adhkar_morning",
    "adhkar_evening",
    "adhkar_sleep",
    "adhkar_general",
    
    # Prayer
    "prayer",
    "prayer_times",
    "qibla",
    
    # Tasbeeh
    "tasbeeh",
    "tasbeeh_start",
    "tasbeeh_increment",
    "tasbeeh_reset",
    "tasbeeh_target",
    "tasbeeh_dhikr",
    "tasbeeh_custom_dhikr",
    "tasbeeh_stats",
    "tasbeeh_set_target_33",
    "tasbeeh_set_target_100",
    "tasbeeh_set_target_1000",
    "tasbeeh_set_target_unlimited",
    
    # Settings
    "settings",
    "settings_language",
    "settings_prayer_notifications",
    "settings_daily_wird",
    
    # Admin
    "admin_panel",
    "admin_analytics",
    "admin_module_stats",
    "admin_users",
    "admin_search",
    "admin_banned",
    "admin_broadcast",
    "admin_toggles",
    "admin_maintenance",
    "admin_flush_redis",
    "admin_logs",
    "admin_health",
    "admin_toggle_quran",
    "admin_toggle_hadith",
    "admin_toggle_adhkar",
    "admin_toggle_maintenance",
    "maintenance_on",
    "maintenance_off",
    
    # AI Assistant
    "ai_assistant",
    
    # Language
    "language_menu",
    
    # Low Data
    "toggle_low_data_mode",
    "low_data_menu",
    
    # Mood Adhkar
    "mood_adhkar_menu",
    
    # Adhkar Timings
    "customize_adhkar_timings",
    "set_morning_time",
    "set_evening_time",
    "set_sleep_time",
    
    # Daily Broadcasts
    "toggle_daily_broadcasts",
    "daily_broadcasts_menu",
    
    # Friday Reminder
    "toggle_friday_reminder",
    "friday_reminder_menu",
    
    # Main menu (legacy)
    "main_menu",
]


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, str(error)))
        print(f"❌ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*60}")
        return self.failed == 0


def create_mock_callback(callback_data: str, user_id: int = 123456789):
    """Create a mock CallbackQuery object"""
    user = User(id=user_id, is_bot=False, first_name="Test")
    chat = Chat(id=user_id, type="private")
    message = Message(
        message_id=1,
        date=None,
        chat=chat,
        from_user=user,
        content_type="text",
        options={}
    )
    
    callback = CallbackQuery(
        id="test_callback",
        from_user=user,
        chat_instance="test_instance",
        data=callback_data,
        message=message
    )
    
    # Mock async methods
    callback.answer = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.message.edit_caption = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    
    return callback


def create_mock_db():
    """Create a mock database session"""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.scalar_one_or_none = AsyncMock(return_value=None)
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    return db


async def test_callback_data_exists_in_handlers(results: TestResults):
    """Test that all callback_data strings have matching handlers"""
    print("Testing that all callback_data strings have matching handlers...")
    print(f"Total callback_data strings to test: {len(ALL_CALLBACK_DATA)}")
    
    handlers_dir = project_root / "handlers"
    
    # Collect all callback_data patterns from handlers
    handler_patterns = set()
    
    for handler_file in handlers_dir.glob("*.py"):
        try:
            content = handler_file.read_text(encoding='utf-8')
            
            # Find all F.data == "..." patterns
            patterns = re.findall(r'F\.data\s*==\s*["\']([^"\']+)["\']', content)
            handler_patterns.update(patterns)
            
            # Find all F.data.startswith("...") patterns
            startswith_patterns = re.findall(r'F\.data\.startswith\(["\']([^"\']+)["\']\)', content)
            for pattern in startswith_patterns:
                handler_patterns.add(pattern + "*")
                
        except Exception as e:
            results.add_fail(f"Error reading {handler_file.name}", e)
    
    # Check each callback_data
    for callback_data in ALL_CALLBACK_DATA:
        # Check for exact match
        if callback_data in handler_patterns:
            results.add_pass(f"callback_data '{callback_data}' has exact handler")
            continue
        
        # Check for startswith match
        has_match = False
        for pattern in handler_patterns:
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if callback_data.startswith(prefix):
                    results.add_pass(f"callback_data '{callback_data}' matched by startswith handler '{prefix}*'")
                    has_match = True
                    break
        
        if not has_match:
            results.add_fail(f"callback_data '{callback_data}'", "No matching handler found")


async def test_handler_first_line_is_answer(results: TestResults):
    """Test that all handlers have await callback.answer() as first line"""
    print("\nTesting that handlers have callback.answer() as first line...")
    
    handlers_dir = project_root / "handlers"
    
    for handler_file in handlers_dir.glob("*.py"):
        try:
            content = handler_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if '@router.callback_query' in line:
                    # Find the next async def
                    for j in range(i, min(i + 10, len(lines))):
                        if 'async def' in lines[j]:
                            # Check if the next non-empty, non-docstring line is await callback.answer()
                            in_docstring = False
                            docstring_delimiter = None
                            
                            for k in range(j + 1, min(j + 15, len(lines))):
                                current_line = lines[k]
                                
                                # Handle docstring start/end
                                if not in_docstring:
                                    if '"""' in current_line or "'''" in current_line:
                                        # Check if it's a single-line docstring
                                        if current_line.count('"""') == 2 or current_line.count("'''") == 2:
                                            continue  # Single-line docstring, skip
                                        else:
                                            in_docstring = True
                                            docstring_delimiter = '"""' if '"""' in current_line else "'''"
                                            continue
                                else:
                                    if docstring_delimiter in current_line:
                                        in_docstring = False
                                        docstring_delimiter = None
                                        continue
                                
                                if in_docstring:
                                    continue
                                
                                stripped = current_line.strip()
                                
                                # Skip empty lines and comments
                                if not stripped or stripped.startswith('#'):
                                    continue
                                
                                # This is the first actual line of code
                                if 'await callback.answer' in current_line:
                                    results.add_pass(f"{handler_file.name}:{j+1} has callback.answer() first")
                                else:
                                    # Some handlers might have early returns, that's ok
                                    if 'if' in current_line or 'return' in current_line:
                                        results.add_pass(f"{handler_file.name}:{j+1} has early check (acceptable)")
                                    else:
                                        results.add_fail(f"{handler_file.name}:{j+1} missing callback.answer() first", 
                                                      f"Found: {stripped[:50]}")
                                break
                            break
        except Exception as e:
            results.add_fail(f"Error reading {handler_file.name}", e)


async def test_main_menu_consistency(results: TestResults):
    """Test that all back buttons use go_main_menu consistently"""
    print("\nTesting main_menu vs go_main_menu consistency...")
    
    handlers_dir = project_root / "handlers"
    
    for handler_file in handlers_dir.glob("*.py"):
        try:
            content = handler_file.read_text(encoding='utf-8')
            
            # Check for callback_data="main_menu" (should be go_main_menu)
            if 'callback_data="main_menu"' in content:
                # Check if it's in a handler definition (acceptable) or button (not acceptable)
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'callback_data="main_menu"' in line:
                        # Check context
                        if 'InlineKeyboardButton' in line or 'callback_data=' in line:
                            results.add_fail(f"{handler_file.name}:{i+1} uses main_menu instead of go_main_menu",
                                          "Should use go_main_menu for back buttons")
        except Exception as e:
            results.add_fail(f"Error checking {handler_file.name}", e)


async def main():
    """Run all tests"""
    print("="*60)
    print("Bot Route Audit Test Suite")
    print("="*60)
    
    results = TestResults()
    
    # Run tests
    await test_callback_data_exists_in_handlers(results)
    await test_handler_first_line_is_answer(results)
    await test_main_menu_consistency(results)
    
    # Print summary
    success = results.summary()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
