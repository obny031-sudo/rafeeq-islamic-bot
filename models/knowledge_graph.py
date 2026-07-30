"""
Knowledge Graph models for Rafeeq Enterprise Islamic OS.
Connects Quranic Ayahs, Hadith, Tafsir, and Stories with relationships.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from models.base import Base


class ContentType(str):
    """Content type enumeration"""
    QURAN_AYAH = "quran_ayah"
    HADITH = "hadith"
    TAFSIR = "tafsir"
    ADHKAR = "adhkar"
    STORY = "story"
    TOPIC = "topic"
    THEME = "theme"


class ContentNode(Base):
    """
    Base content node in the knowledge graph.
    Represents any piece of Islamic content.
    """
    __tablename__ = "content_nodes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_type = Column(String(50), nullable=False, index=True)
    source_id = Column(String(100), nullable=False, index=True)  # External source ID (e.g., "quran_2:255")
    
    # Content data
    title = Column(String(500), nullable=True)
    text_arabic = Column(Text, nullable=True)
    text_transliteration = Column(Text, nullable=True)
    text_translation = Column(Text, nullable=True)
    
    # Metadata
    source_name = Column(String(100), nullable=True)  # e.g., "Sahih Bukhari", "Ibn Kathir"
    reference = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags
    themes = Column(JSON, nullable=True)  # List of theme IDs
    
    # Analytics
    view_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    outgoing_edges = relationship("ContentEdge", foreign_keys="ContentEdge.source_node_id", back_populates="source")
    incoming_edges = relationship("ContentEdge", foreign_keys="ContentEdge.target_node_id", back_populates="target")
    
    def __repr__(self):
        return f"<ContentNode(id={self.id}, type={self.content_type}, source_id={self.source_id})>"


class EdgeType(str):
    """Relationship type enumeration"""
    RELATED_TO = "related_to"
    EXPLAINS = "explains"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    PART_OF = "part_of"
    CONTAINS = "contains"
    THEME_OF = "theme_of"
    SIMILAR_TO = "similar_to"
    FOLLOWS = "follows"
    PRECEDES = "precedes"


class ContentEdge(Base):
    """
    Edge connecting two content nodes in the knowledge graph.
    Represents relationships between content pieces.
    """
    __tablename__ = "content_edges"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, index=True)
    target_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, index=True)
    edge_type = Column(String(50), nullable=False, index=True)
    
    # Edge metadata
    weight = Column(Float, default=1.0)  # Relationship strength (0.0 to 1.0)
    description = Column(Text, nullable=True)
    edge_metadata = Column(JSON, nullable=True)  # Additional relationship data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source = relationship("ContentNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target = relationship("ContentNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
    
    def __repr__(self):
        return f"<ContentEdge(source={self.source_node_id}, target={self.target_node_id}, type={self.edge_type})>"


class QuranAyah(Base):
    """
    Specific Quran Ayah data.
    Extends content node with Quran-specific fields.
    """
    __tablename__ = "quran_ayahs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, unique=True)
    
    # Quran-specific fields
    surah_number = Column(Integer, nullable=False, index=True)
    ayah_number = Column(Integer, nullable=False)
    juz_number = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    
    # Revelation info
    revelation_place = Column(String(50), nullable=True)  # Mecca/Medina
    revelation_order = Column(Integer, nullable=True)
    
    # Tafsir references
    tafsir_ibn_kathir = Column(Text, nullable=True)
    tafsir_al_sadi = Column(Text, nullable=True)
    tafsir_al_tabari = Column(Text, nullable=True)
    
    # Relationships
    content_node = relationship("ContentNode")
    
    def __repr__(self):
        return f"<QuranAyah(surah={self.surah_number}, ayah={self.ayah_number})>"


class Hadith(Base):
    """
    Specific Hadith data.
    Extends content node with Hadith-specific fields.
    """
    __tablename__ = "hadiths"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, unique=True)
    
    # Hadith-specific fields
    collection = Column(String(100), nullable=False, index=True)  # e.g., "Sahih Bukhari"
    book_number = Column(Integer, nullable=True)
    hadith_number = Column(String(50), nullable=True)
    
    # Narrator chain (isnad)
    narrator_arabic = Column(Text, nullable=True)
    narrator_english = Column(Text, nullable=True)
    
    # Classification
    authenticity = Column(String(50), nullable=True)  # Sahih, Hasan, Da'if
    narrator_count = Column(Integer, nullable=True)  # Mutawatir, Mashhur, etc.
    
    # Relationships
    content_node = relationship("ContentNode")
    
    def __repr__(self):
        return f"<Hadith(collection={self.collection}, number={self.hadith_number})>"


class Tafsir(Base):
    """
    Specific Tafsir (interpretation) data.
    """
    __tablename__ = "tafsirs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, unique=True)
    
    # Tafsir-specific fields
    scholar_name = Column(String(100), nullable=False, index=True)  # e.g., "Ibn Kathir"
    scholar_period = Column(String(50), nullable=True)  # e.g., "7th century AH"
    methodology = Column(String(100), nullable=True)  # e.g., "Narrative-based", "Opinion-based"
    
    # Reference to what this tafsir explains
    ref_content_type = Column(String(50), nullable=True)  # e.g., "quran_ayah"
    ref_source_id = Column(String(100), nullable=True)  # e.g., "quran_2:255"
    
    # Relationships
    content_node = relationship("ContentNode")
    
    def __repr__(self):
        return f"<Tafsir(scholar={self.scholar_name})>"


class Story(Base):
    """
    Islamic stories and historical events.
    """
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, unique=True)
    
    # Story-specific fields
    story_type = Column(String(50), nullable=True, index=True)  # e.g., "prophetic", "historical", "moral"
    time_period = Column(String(100), nullable=True)  # e.g., "Pre-Islamic", "Prophetic Era"
    location = Column(String(100), nullable=True)
    main_characters = Column(JSON, nullable=True)  # List of character names
    
    # Relationships
    content_node = relationship("ContentNode")
    
    def __repr__(self):
        return f"<Story(type={self.story_type}, title={self.title})>"


class Theme(Base):
    """
    Themes and topics for content categorization.
    """
    __tablename__ = "themes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    name_arabic = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    parent_theme_id = Column(Integer, ForeignKey("themes.id"), nullable=True)
    
    # Analytics
    content_count = Column(Integer, default=0)
    popularity_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Self-referential relationship for hierarchical themes
    parent = relationship("Theme", remote_side=[id])
    children = relationship("Theme", overlaps="parent")
    
    def __repr__(self):
        return f"<Theme(name={self.name})>"


class ContentTheme(Base):
    """
    Many-to-many relationship between content and themes.
    """
    __tablename__ = "content_themes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, index=True)
    theme_id = Column(Integer, ForeignKey("themes.id"), nullable=False, index=True)
    relevance_score = Column(Float, default=1.0)  # How relevant this theme is to the content
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ContentTheme(content={self.content_node_id}, theme={self.theme_id})>"
