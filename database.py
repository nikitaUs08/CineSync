import asyncio
import aiosqlite

DB_NAME = "cinesync.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT NOT NULL,
                movie_title TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()
        print("[БД] Таблицы успешно созданы.")

async def save_match(room_code, movie_title):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO matches (room_code, movie_title) VALUES (?, ?)",
            (room_code, movie_title)
        )
        await db.commit()
        print(f"[БД] Сохранен мэтч: {movie_title} в комнате {room_code}")

if __name__ == "__main__":
    asyncio.run(init_db())
