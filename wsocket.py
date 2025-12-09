# wsocket.py
import random
import string
from fastapi import WebSocket, WebSocketDisconnect
from models import Player, Game, get_session

rooms = {}  # Словарь для хранения комнат
chats = {}  # Словарь для хранения истории сообщений в комнатах

def generate_room_id(length=6):
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))
  
async def create_or_join_room(nickname: str):
    db = get_session()
    
    # Проверяем наличие свободных комнат
    free_rooms = db.query(Game).filter_by(status="opened", player2=None).all()
    
    if free_rooms:
        # Присоединяемся к свободной комнате
        room = free_rooms[0]
        room.player2 = nickname
        room.status = "closed"
        # Проверяем статус игроков
        player1_status = db.query(Player.status).filter_by(nickname=room.player1).scalar()
        player2_status = db.query(Player.status).filter_by(nickname=room.player2).scalar()
        if player1_status == "online" and player2_status == "online":
            room.process = "active"
        else:
            room.process = "desactive"
        db.commit()
        print(f"Игрок {nickname} присоединился к комнате {room.room_id}.")
        return room.room_id
    else:
        # Создаём новую комнату
        room_id = generate_room_id()
        game = Game(room_id=room_id, player1=nickname, player2=None, status="opened", process="desactive")
        db.add(game)
        db.commit()
        print(f"Создана комната с ID: {room_id}, владелец: {nickname}")
        return room_id

async def broadcast_message(room_id: str, message: dict):
    for ws in rooms.get(room_id, []):
        await ws.send_json(message)

async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    print(f"Клиент подключился к комнате {room_id}.")

    # Добавляем вебсокет в комнату
    if room_id not in rooms:
        rooms[room_id] = []
    rooms[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await broadcast_message(room_id, data)
    except WebSocketDisconnect:
        print(f"Клиент отключился от комнаты {room_id}.")
        rooms[room_id].remove(websocket)
        if not rooms[room_id]:
            del rooms[room_id]

async def notify_room_update(room_id: str):
    db = get_session()
    game = db.query(Game).filter_by(room_id=room_id).first()
    if game:
        status = game.status
        players = [game.player1, game.player2]
        await broadcast_message(room_id, {"type": "room_update", "status": status, "players": players})

async def close_room(room_id: str):
    db = get_session()
    game = db.query(Game).filter_by(room_id=room_id).first()
    if game:
        game.status = "closed"
        game.process = "desactive"
        db.commit()
        await notify_room_update(room_id)
        print(f"Комната {room_id} закрыта и переведена в статус 'desactive'.")
        # Вызываем функцию extra_closed
        await extra_closed(room_id)

async def extra_closed(room_id: str):
    db = get_session()
    game = db.query(Game).filter_by(room_id=room_id).first()
    if game:
        nicknames = [game.player1, game.player2]
        for nickname in nicknames:
            if nickname:
                # Вызываем метод logout для каждого игрока
                await logout(nickname, room_id)

async def logout(nickname: str, room_id: str):
    db = get_session()
    player = db.query(Player).filter_by(nickname=nickname).first()
    if player:
        player.status = "offline"
        db.commit()
    # Отправляем уведомление обоим игрокам
    await broadcast_message(room_id, {"type": "redirect", "url": "/logout/" + nickname})