# models.py
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

# Создаём двигатель для работы с базой данных
DB_URL = "postgresql://postgres:NtfFv,hjep@127.0.0.1:5432/bot"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Модель игрока
class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True)
    password = Column(String)
    status = Column(Enum("online", "offline", name="player_status"))  # Тут явно указываем тип ENUM
    
# Модель игры (комнат)
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, unique=True, index=True)  # Уникальный идентификатор комнаты
    player1 = Column(String)  # Никнейм первого игрока
    player2 = Column(String, nullable=True)  # Никнейм второго игрока (может быть пустым)
    status = Column(Enum("opened", "closed", name="room_status"))  # Статус комнаты
    process = Column(Enum("active", "desactive", name="game_process"))  # Активность игры

Base.metadata.create_all(bind=engine)

# Вспомогательная функция для получения сессии
def get_session():
    return SessionLocal()