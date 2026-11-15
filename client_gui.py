import sys
import json
import asyncio
import qasync
import websockets
import aiohttp
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from api_parser import fetch_movies


class CineSyncClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CineSync")
        self.resize(350, 650)
        self.ws = None
        self.movies = []
        self.current_movie_index = 0

        # --- СТИЛИЗАЦИЯ (QSS) ---
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3a3a3c; /* Глубокий темно-серый */
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #4a4a4c; }
            QPushButton:disabled { background-color: #2c2c2e; color: #666666; }

            #LikeBtn { 
                background-color: #d4a33d; /* Горчично-желтый */
                color: #ffffff; 
            }
            #LikeBtn:hover { 
                background-color: #c29334; 
            }

            #SkipBtn { 
                background-color: #555555; /* Мягкий серый для скипа */
                color: #ffffff; 
            }
            #SkipBtn:hover { 
                background-color: #666666; 
            }

            #MovieLabel { font-size: 16px; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.room_input = QLineEdit(placeholderText="Код комнаты (например: 123)")
        self.join_btn = QPushButton("Подключиться")

        # Постер
        self.poster_label = QLabel()
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setFixedSize(310, 460)
        self.poster_label.setStyleSheet("background-color: #2b2b2b; border-radius: 15px;")
        self.poster_label.setScaledContents(True)

        self.movie_label = QLabel("Введите код и подключитесь")
        self.movie_label.setObjectName("MovieLabel")
        self.movie_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.like_btn = QPushButton("Лайк (Match)")
        self.like_btn.setObjectName("LikeBtn")

        self.skip_btn = QPushButton("Скип")
        self.skip_btn.setObjectName("SkipBtn")

        self.like_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)

        layout.addWidget(self.room_input)
        layout.addWidget(self.join_btn)
        layout.addWidget(self.poster_label)
        layout.addWidget(self.movie_label)
        layout.addWidget(self.like_btn)
        layout.addWidget(self.skip_btn)
        self.setLayout(layout)

        self.join_btn.clicked.connect(lambda: asyncio.ensure_future(self.connect_to_server()))
        self.like_btn.clicked.connect(lambda: asyncio.ensure_future(self.vote("like")))
        self.skip_btn.clicked.connect(lambda: asyncio.ensure_future(self.vote("skip")))

    async def load_poster(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)
                    self.poster_label.setPixmap(pixmap)
                else:
                    self.movie_label.setText(f"Ошибка загрузки постера: {response.status}")

    async def connect_to_server(self):
        room = self.room_input.text()
        if not room: return

        self.join_btn.setEnabled(False)
        self.movie_label.setText("Загрузка фильмов...")

        self.movies = await fetch_movies()
        self.ws = await websockets.connect("ws://127.0.0.1:8765")
        await self.ws.send(json.dumps({"action": "join", "room": room}))

        self.like_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        await self.show_next_movie()

        asyncio.create_task(self.listen_server())

    async def show_next_movie(self):
        if self.current_movie_index < len(self.movies):
            movie = self.movies[self.current_movie_index]
            self.movie_label.setText(
                f"<b>{movie['title']}</b><br><span style='color:#a0a0a0;'>{movie['genre']} | Рейтинг: {movie['rating']}</span>")
            await self.load_poster(movie['poster'])
        else:
            self.movie_label.setText("Фильмы закончились!")
            self.poster_label.clear()
            self.like_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)

    async def vote(self, action_type):
        movie = self.movies[self.current_movie_index]
        await self.ws.send(json.dumps({
            "action": "vote",
            "movie": movie["title"],
            "vote": action_type
        }))
        self.current_movie_index += 1
        await self.show_next_movie()

    async def listen_server(self):
        try:
            async for message in self.ws:
                data = json.loads(message)

                if data.get("action") == "update":
                    print(f"Другой участник: {data['movie']} -> {data['vote']}")

                elif data.get("action") == "match":
                    # Показываем системный алерт macOS
                    QMessageBox.information(
                        self,
                        "🎉 МЭТЧ!",
                        f"У вас совпадение!\nВсе хотят посмотреть:\n{data['movie']}"
                    )
        except websockets.ConnectionClosed:
            pass


def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = CineSyncClient()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
