"""
Pagination helper for inline keyboards.
Provides reusable pagination functionality for browsing lists.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from typing import List, Any, Optional


class PaginationHelper:
    """Helper class for building paginated inline keyboards"""
    
    def __init__(self, items: List[Any], items_per_page: int = 10):
        self.items = items
        self.items_per_page = items_per_page
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    def get_page_items(self, page: int) -> List[Any]:
        """Get items for a specific page (1-indexed)"""
        if page < 1 or page > self.total_pages:
            return []
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.items[start_idx:end_idx]
    
    def build_keyboard(
        self,
        current_page: int,
        callback_prefix: str,
        back_callback: str = "go_main_menu"
    ) -> InlineKeyboardBuilder:
        """
        Build inline keyboard with pagination controls.
        
        Args:
            current_page: Current page number (1-indexed)
            callback_prefix: Prefix for pagination callbacks (e.g., "surah_page")
            back_callback: Callback for back button
        
        Returns:
            InlineKeyboardBuilder with pagination buttons
        """
        builder = InlineKeyboardBuilder()
        
        # Add navigation row
        nav_buttons = []
        
        # Previous button
        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀ السابق",
                    callback_data=f"{callback_prefix}_{current_page - 1}"
                )
            )
        
        # Page indicator
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"{current_page}/{self.total_pages}",
                callback_data=f"{callback_prefix}_{current_page}"
            )
        )
        
        # Next button
        if current_page < self.total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="▶ التالي",
                    callback_data=f"{callback_prefix}_{current_page + 1}"
                )
            )
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        # Add back button
        builder.row(
            InlineKeyboardButton(
                text="🔙 القائمة الرئيسية",
                callback_data=back_callback
            )
        )
        
        return builder
    
    def format_page_message(
        self,
        page: int,
        title: str,
        item_formatter: callable
    ) -> str:
        """
        Format message for a page.
        
        Args:
            page: Page number (1-indexed)
            title: Page title
            item_formatter: Function to format each item
        
        Returns:
            Formatted message string
        """
        items = self.get_page_items(page)
        text = f"{title}\n\n"
        
        for i, item in enumerate(items, 1):
            text += item_formatter(item, i)
        
        return text


def create_simple_keyboard(
    buttons: List[tuple],
    back_callback: str = "go_main_menu"
) -> InlineKeyboardBuilder:
    """
    Create a simple inline keyboard with buttons and back button.
    
    Args:
        buttons: List of (text, callback_data) tuples
        back_callback: Callback for back button
    
    Returns:
        InlineKeyboardBuilder
    """
    builder = InlineKeyboardBuilder()
    
    for text, callback in buttons:
        builder.row(
            InlineKeyboardButton(text=text, callback_data=callback)
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 القائمة الرئيسية",
            callback_data=back_callback
        )
    )
    
    return builder
