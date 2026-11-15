import asyncio


async def fetch_movies():
    print("[API] Запрос к базе фильмов...")
    await asyncio.sleep(0.5)

    return [
        {
            "title": "Синистер",
            "genre": "Хоррор",
            "rating": 6.8,
            "poster": "https://placehold.co/300x450/2b2b2b/FFFFFF/png?text=Sinister"
        },
        {
            "title": "Реинкарнация",
            "genre": "Хоррор",
            "rating": 7.3,
            "poster": "https://placehold.co/300x450/2b2b2b/FFFFFF/png?text=Hereditary"
        },
        {
            "title": "Оцепеневшие от страха",
            "genre": "Хоррор",
            "rating": 6.5,
            "poster": "https://placehold.co/300x450/2b2b2b/FFFFFF/png?text=Terrified"
        }
    ]
