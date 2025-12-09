# main.py
from fastapi import FastAPI, Request, Form, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from models1 import Player, Game ,get_session
from wsocket1 import create_or_join_room, rooms, websocket_endpoint, close_room

# Подключаем шаблоны
templates = Jinja2Templates(directory="test/templates")

app = FastAPI()

# Регистрируем вебсокетные маршруты
app.websocket("/room/ws")(websocket_endpoint)

@app.get("/", response_class=HTMLResponse)
async def serve_html(request: Request):
    return templates.TemplateResponse("start.html", {"request": request})

@app.post("/players/register")
async def register_player(request: Request, nickname: str = Form(), password: str = Form(), db=Depends(get_session)):
    # Проверка на заполненность полей
    if not nickname or not password:
        return {"detail": "Все поля должны быть заполнены"}, 400

    # Проверяем длину логина и пароля
    if len(nickname) > 10 or len(password) > 10:
        return {"detail": "Максимальная длина логина и пароля — 10 символов."}, 400

    # Проверяем уникальность никнейма
    existing_player = db.query(Player).filter_by(nickname=nickname).first()
    if existing_player:
        return {"detail": "Данный никнейм уже занят. Выберите другой."}, 400

    # Регистрация нового игрока
    new_player = Player(nickname=nickname, password=password, status="offline")
    db.add(new_player)
    db.commit()

    # Перенаправляем на страницу успешной регистрации
    return templates.TemplateResponse("registr.html", {"request": request})

@app.post("/players/login")
async def login_player(request: Request, nickname: str = Form(), password: str = Form(), db=Depends(get_session)):
    # Проверка на заполненность полей
    if not nickname or not password:
        return {"detail": "Все поля должны быть заполнены"}, 400

    # Поиск игрока по никнейму
    player = db.query(Player).filter_by(nickname=nickname).first()
    if not player:
        return {"detail": "Никнейм не найден"}, 404

    # Проверка пароля (прямое сравнение без хэширования!)
    if player.password != password:
        return {"detail": "Неверный пароль"}, 401

    # Меняем статус игрока на онлайн
    player.status = "online"
    db.commit()

    # Если авторизация успешна, переходим на страницу личного кабинета
    return RedirectResponse(url=f"/login/{nickname}", status_code=303)

@app.get("/login/{nickname}", response_class=HTMLResponse)
async def personalized_login(request: Request, nickname: str):
    return templates.TemplateResponse("login.html", {"request": request, "nickname": nickname})

@app.get("/players")
async def get_online_players(db=Depends(get_session)):
    # Получаем всех игроков, которые находятся онлайн
    online_players = db.query(Player).filter_by(status="online").all()

    # Исключаем игроков, участвующих в играх
    active_games = db.query(Game.player1, Game.player2).filter_by(process="active").all()
    busy_players = set([player for pair in active_games for player in pair if player])

    # Возвращаем только тех, кто не участвует в играх
    available_players = [player.nickname for player in online_players if player.nickname not in busy_players]
    return {"players": [p for p in available_players]}

@app.get("/logout/{nickname}")
async def logout(nickname: str, db=Depends(get_session)):
    # Меняем статус игрока на offline
    player = db.query(Player).filter_by(nickname=nickname).first()
    if player:
        player.status = "offline"
        db.commit()
    
    # Проверяем, нужно ли обновить статус комнаты
    room_games = db.query(Game).filter((Game.player1==nickname)|(Game.player2==nickname)).all()
    for game in room_games:
        await close_room(game.room_id)
    
    return RedirectResponse(url="/")
    
# комната
@app.get("/game/create")
async def create_room_route(request: Request, nickname: str, db=Depends(get_session)):
    # Используем готовую функцию create_room
    room_id = await create_or_join_room(nickname)
    return RedirectResponse(url=f"/game/{room_id}")

# Присоединение к комнате
@app.get("/game/{room_id}")
async def join_room(room_id: str, request: Request, db=Depends(get_session)):
    # Проверяем, существует ли комната
    game = db.query(Game).filter_by(room_id=room_id).first()
    if not game:
        return {"detail": "Комната не найдена"}
    return templates.TemplateResponse("game.html", {"request": request, "room_id": room_id, "game": game})

# комната
@app.websocket("/game/{room_id}/chat")
async def chat_endpoint(websocket: WebSocket, room_id: str):
    await websocket_endpoint(websocket, room_id)

# доработать нужно
@app.get("/games")
async def get_active_games(db=Depends(get_session)):
    # Получаем все активные комнаты
    active_games = db.query(Game).filter_by(process="active").all()
    return {"games": [{"room_id": game.room_id, "status": game.status, "process": game.process} for game in active_games]}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)