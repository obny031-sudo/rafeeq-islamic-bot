"""Seed PostgreSQL with initial Islamic content."""

import logging
from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_graph import ContentNode, ContentType

logger = logging.getLogger(__name__)

ADHKAR_SEED_DATA: Dict[str, List[Dict[str, Any]]] = {
    "morning": [
        {
            "arabic": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ",
            "transliteration": "Asbahna wa asbahal mulku lillah, walhamdu lillah",
            "translation": "We have entered the morning and the dominion belongs to Allah, and all praise is for Allah.",
            "reference": "Muslim 271",
        },
        {
            "arabic": "اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ النُّشُور",
            "transliteration": "Allahumma bika asbahna wa bika amsayna, wa bika nahya wa bika namutu, wa ilaykan-nushur",
            "translation": "O Allah, by Your grace we enter the morning and by Your grace we enter the evening, by Your grace we live and by Your grace we die, and to You is the resurrection.",
            "reference": "Tirmidhi 3392",
        },
        {
            "arabic": "اللَّهُمَّ أَنْتَ رَبِّي لا إِلَهَ إلا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ",
            "transliteration": "Allahumma anta rabbi la ilaha illa anta, khalaqtani wa ana abduka, wa ana 'ala ahdika wa wa'dika mastata'tu",
            "translation": "O Allah, You are my Lord, there is no god but You. You have created me and I am Your servant, and I am on Your covenant and Your promise as much as I can.",
            "reference": "Bukhari 6307",
        },
        {
            "arabic": "سُبْحَانَ اللهِ وَبِحَمْدِهِ",
            "transliteration": "SubhanAllahi wa bihamdihi",
            "translation": "Glory be to Allah and praise Him.",
            "reference": "Muslim 2692",
            "count": 100,
        },
        {
            "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالآخِرَةِ",
            "transliteration": "Allahumma inni as'alukal 'afwa wal 'afiyah fid-dunya wal akhirah",
            "translation": "O Allah, I ask You for forgiveness and well-being in this world and the Hereafter.",
            "reference": "Ibn Majah 3879",
        },
    ],
    "evening": [
        {
            "arabic": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ",
            "transliteration": "Amsayna wa amsal mulku lillah, walhamdu lillah",
            "translation": "We have entered the evening and the dominion belongs to Allah, and all praise is for Allah.",
            "reference": "Muslim 271",
        },
        {
            "arabic": "اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ الْمَصِير",
            "transliteration": "Allahumma bika amsayna wa bika asbahna, wa bika nahya wa bika namutu, wa ilaykal-masir",
            "translation": "O Allah, by Your grace we enter the evening and by Your grace we enter the morning, by Your grace we live and by Your grace we die, and to You is the return.",
            "reference": "Tirmidhi 3392",
        },
        {
            "arabic": "أَعُوذُ بِكَلِمَاتِ اللهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ",
            "transliteration": "A'udhu bikalimatillahit-tammati min sharri ma khalaq",
            "translation": "I seek refuge in the perfect words of Allah from the evil of what He has created.",
            "reference": "Tirmidhi 3598",
            "count": 3,
        },
        {
            "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْجَنَّةَ وَأَعُوذُ بِكَ مِنَ النَّار",
            "transliteration": "Allahumma inni as'alukal jannah wa a'udhu bika minan-nar",
            "translation": "O Allah, I ask You for Paradise and seek refuge in You from the Fire.",
            "reference": "Ibn Majah 4341",
        },
    ],
    "sleep": [
        {
            "arabic": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا",
            "transliteration": "Bismika Allahumma amutu wa ahya",
            "translation": "In Your name O Allah, I die and I live.",
            "reference": "Bukhari 6324",
        },
        {
            "arabic": "اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ",
            "transliteration": "Allahumma qini 'adhabaka yawma tab'athu 'ibadak",
            "translation": "O Allah, protect me from Your punishment on the Day You resurrect Your servants.",
            "reference": "Tirmidhi 3397",
        },
    ],
    "general": [
        {
            "arabic": "سُبْحَانَ اللهِ",
            "transliteration": "SubhanAllah",
            "translation": "Glory be to Allah.",
            "reference": "Muslim 2692",
        },
        {
            "arabic": "الْحَمْدُ لِلَّهِ",
            "transliteration": "Alhamdulillah",
            "translation": "All praise is due to Allah.",
            "reference": "Muslim 2692",
        },
        {
            "arabic": "اللَّهُ أَكْبَرُ",
            "transliteration": "Allahu Akbar",
            "translation": "Allah is the Greatest.",
            "reference": "Muslim 2692",
        },
        {
            "arabic": "لا إِلَهَ إِلا اللَّهُ",
            "transliteration": "La ilaha illallah",
            "translation": "There is no god but Allah.",
            "reference": "Bukhari 6303",
        },
    ],
}


async def seed_adhkar_content(session: AsyncSession) -> int:
    """Seed adhkar content nodes if the table is empty."""
    result = await session.execute(
        select(func.count()).select_from(ContentNode).where(ContentNode.content_type == ContentType.ADHKAR)
    )
    existing = result.scalar() or 0
    if existing > 0:
        logger.info("Adhkar content already seeded (%s entries)", existing)
        return 0

    created = 0
    for category, items in ADHKAR_SEED_DATA.items():
        for index, item in enumerate(items, start=1):
            tags = [category]
            if item.get("count"):
                tags.append(f"count:{item['count']}")

            node = ContentNode(
                content_type=ContentType.ADHKAR,
                source_id=f"adhkar_{category}_{index}",
                text_arabic=item["arabic"],
                text_transliteration=item.get("transliteration"),
                text_translation=item.get("translation"),
                reference=item.get("reference"),
                tags=tags,
                source_name="Authentic Adhkar Collection",
            )
            session.add(node)
            created += 1

    await session.flush()
    logger.info("Seeded %s adhkar content nodes", created)
    return created
