"""
Safe text chunking utility for Telegram messages.
Ensures messages don't exceed 4096 character limit without breaking words or Markdown tags.
"""

import re
from typing import List


def chunk_text_safely(text: str, max_length: int = 4096) -> List[str]:
    """
    Safely chunk text into multiple messages without breaking words or Markdown tags.
    
    Args:
        text: The text to chunk
        max_length: Maximum length per chunk (Telegram limit is 4096)
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    words = text.split()
    
    for word in words:
        # Check if adding this word would exceed limit
        potential_chunk = current_chunk + (" " if current_chunk else "") + word
        
        if len(potential_chunk) > max_length:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                # Single word is too long, force split
                chunks.append(word[:max_length])
                current_chunk = word[max_length:]
        else:
            current_chunk = potential_chunk
    
    # Add remaining content
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def chunk_markdown_safely(text: str, max_length: int = 4096) -> List[str]:
    """
    Chunk text while preserving Markdown formatting.
    Ensures no unclosed Markdown tags in chunks.
    
    Args:
        text: The Markdown text to chunk
        max_length: Maximum length per chunk
    
    Returns:
        List of Markdown-safe chunks
    """
    # Markdown patterns to track
    markdown_patterns = [
        (r'\*\*', '**'),  # Bold
        (r'\*', '*'),     # Italic
        (r'`', '`'),       # Code
        (r'__', '__'),     # Underline
        (r'~', '~'),       # Strikethrough
        (r'\[', ']'),      # Links
    ]
    
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Check if we're at a Markdown opening
        for pattern, closing in markdown_patterns:
            if text.startswith(pattern, i):
                # Find the closing
                closing_pos = text.find(closing, i + len(pattern))
                if closing_pos != -1:
                    # Include the entire formatted section
                    section = text[i:closing_pos + len(closing)]
                    if len(current_chunk) + len(section) > max_length:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = section
                        else:
                            # Section is too long, force split
                            chunks.append(section[:max_length])
                            current_chunk = section[max_length:]
                    else:
                        current_chunk += section
                    i = closing_pos + len(closing)
                    break
        else:
            # Regular character
            if len(current_chunk) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = char
            else:
                current_chunk += char
            i += 1
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def ensure_markdown_closed(text: str) -> str:
    """
    Ensure all Markdown tags are properly closed in text.
    
    Args:
        text: Text with potential unclosed Markdown
    
    Returns:
        Text with closed Markdown tags
    """
    # Count opening and closing tags
    bold_open = text.count('**') // 2
    italic_open = text.count('*') - (bold_open * 2)
    code_open = text.count('`')
    
    # Close unclosed tags
    result = text
    if code_open % 2 == 1:
        result += '`'
    if italic_open % 2 == 1:
        result += '*'
    
    return result
