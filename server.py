import asyncio
import websockets
import json
from database import save_match  # Подключаем БД

rooms = {}
room_likes = {}  # Хранит количество лайков: {"123": {"Синистер": 2}}


async def handler(websocket):
    room_code = None
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")

            if action == "join":
                room_code = data.get("room")
                if room_code not in rooms:
                    rooms[room_code] = []
                    room_likes[room_code] = {}
                rooms[room_code].append(websocket)
                print(f"[Сервер] Новое подключение. Комната {room_code}: {len(rooms[room_code])} чел.")

            elif action == "vote":
                movie = data["movie"]
                vote = data["vote"]
                print(f"[Сервер] Свайп в комнате {room_code}: {movie} -> {vote}")

                if vote == "like":
                    # Считаем лайки
                    if movie not in room_likes[room_code]:
                        room_likes[room_code][movie] = 0
                    room_likes[room_code][movie] += 1

                    # Если 2 человека лайкнули один фильм
                    if room_likes[room_code][movie] == 2:
                        print(f"[Сервер] 🎉 МЭТЧ в комнате {room_code} на фильм {movie}!")

                        # Асинхронно пишем в базу данных
                        await save_match(room_code, movie)

                        # Рассылаем уведомление о мэтче всем в комнате
                        for client in rooms[room_code]:
                            await client.send(json.dumps({
                                "action": "match",
                                "movie": movie
                            }))

                # Обычная рассылка голоса (опционально, чтобы видеть, кто что жмет)
                for client in rooms[room_code]:
                    if client != websocket:
                        await client.send(json.dumps({
                            "action": "update",
                            "movie": movie,
                            "vote": vote
                        }))

    except websockets.ConnectionClosed:
        pass
    finally:
        if room_code and room_code in rooms:
            if websocket in rooms[room_code]:
                rooms[room_code].remove(websocket)
            if not rooms[room_code]:
                del rooms[room_code]
                if room_code in room_likes:
                    del room_likes[room_code]
                print(f"[Сервер] Комната {room_code} закрыта.")


async def main():
    print("[Сервер] Запущен на ws://127.0.0.1:8765")
    async with websockets.serve(handler, "127.0.0.1", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
