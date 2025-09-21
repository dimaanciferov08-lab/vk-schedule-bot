import vk_api
import json
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import datetime
import random
import requests

# !!! ЗАПОЛНИ ЭТИ ДАННЫЕ СВОИМИ !!!
CONFIG = {
    "group_id": 232761329,
    "token": "vk1.a.Y2xBv4alWQ55rd1IxtkpKc48ibKqpQ1x0Wyc9Hv0z18elxu3JaSBfCi7F5sJ9H4eKy1jg3iqFOjQTkQyCIYdnf77mcezdC__MLiyRi9Xwfus_uLz7UWd9AR8VPQDr7uMEiD1NxadTzqUllP7p4uqWixuefYkm6ryhgMbFLPSo-hnXKyt0XQ4qvpfIG5kLWlJoH7Ivew1yhgiKmtDWhbHYw",
    "admin_id": 238448950,
    "current_week": 1,
    "current_view": "today",
    "locations": {
        "101": {"lat": 59.9343, "lon": 30.3351, "name": "Главный корпус", "address": "ул. Примерная, 1"},
        "201": {"lat": 59.9345, "lon": 30.3353, "name": "Второй корпус", "address": "ул. Примерная, 2"},
        "301": {"lat": 59.9347, "lon": 30.3355, "name": "Третий корпус", "address": "ул. Примерная, 3"},
        "405": {"lat": 59.9349, "lon": 30.3357, "name": "Лабораторный корпус", "address": "ул. Примерная, 4"},
        "505": {"lat": 59.9351, "lon": 30.3359, "name": "Научный корпус", "address": "ул. Примерная, 5"},
        "актовый зал": {"lat": 59.9344, "lon": 30.3352, "name": "Актовый зал", "address": "ул. Егорова, 15"},
        "спортзал": {"lat": 59.9346, "lon": 30.3354, "name": "Спортивный зал", "address": "ул. Спортивная, 10"},
        "223с": {"lat": 59.9350, "lon": 30.3358, "name": "Корпус С", "address": "Советская, 14"},
        "14лт": {"lat": 59.9352, "lon": 30.3360, "name": "Корпус Т", "address": "Советская, 10"},
        "111л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "107л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "104л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "505л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "406с": {"lat": 59.9350, "lon": 30.3358, "name": "Корпус С", "address": "Советская, 14"}
    }
}

# База знаний вопросов-ответов
faq_database = {}

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_week1 (
            id INTEGER PRIMARY KEY,
            data TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_week2 (
            id INTEGER PRIMARY KEY,
            data TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            votes TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            asked_by INTEGER NOT NULL,
            asked_at TEXT NOT NULL,
            answered BOOLEAN DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            answer TEXT NOT NULL,
            added_by INTEGER NOT NULL,
            added_at TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO schedule_week1 (id, data, last_updated) VALUES (1, '{}', '')")
    cursor.execute("INSERT OR IGNORE INTO schedule_week2 (id, data, last_updated) VALUES (1, '{}', '')")
    
    # Загружаем FAQ из базы
    cursor.execute("SELECT keyword, answer FROM faq")
    for keyword, answer in cursor.fetchall():
        faq_database[keyword] = answer
    
    conn.commit()
    conn.close()

# Сохранение расписания в БД
def save_schedule(schedule_data):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    table_name = f"schedule_week{CONFIG['current_week']}"
    cursor.execute(f"UPDATE {table_name} SET data = ?, last_updated = ? WHERE id = 1", 
                  (json.dumps(schedule_data, ensure_ascii=False), current_time))
    
    conn.commit()
    conn.close()
    return current_time

# Загрузка расписания из БД
def load_schedule():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    table_name = f"schedule_week{CONFIG['current_week']}"
    cursor.execute(f"SELECT data, last_updated FROM {table_name} WHERE id = 1")
    
    data, last_updated = cursor.fetchone()
    conn.close()
    return json.loads(data), last_updated

# Русские названия месяцев и дней
months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]

days_of_week = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресеньe"]
days_of_week_capitalized = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресеньe"]

# Временные интервалы пар
time_slots = {
    "1": "09:00—10:35",
    "2": "10:45—12:20", 
    "3": "12:40—14:15",
    "4": "14:45—16:20",
    "5": "16:30—18:05",
    "6": "18:15—19:50"
}

# Создание клавиатуры
def create_keyboard():
    keyboard = VkKeyboard(inline=True)
    
    # Кнопка Сегодня
    if CONFIG["current_view"] == "today":
        keyboard.add_button('Сегодня', color=VkKeyboardColor.POSITIVE)
    else:
        keyboard.add_button('Сегодня', color=VkKeyboardColor.SECONDARY)
    
    # Кнопки Неделя и След неделя
    if CONFIG["current_view"] == "week":
        keyboard.add_button('Неделя', color=VkKeyboardColor.POSITIVE)
    else:
        keyboard.add_button('Неделя', color=VkKeyboardColor.SECONDARY)
    
    if CONFIG["current_view"] == "next_week":
        keyboard.add_button('След неделя', color=VkKeyboardColor.POSITIVE)
    else:
        keyboard.add_button('След неделя', color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()

# Функция создания клавиатуры для опросов
def create_poll_keyboard(poll_type, poll_id=None):
    keyboard = VkKeyboard(inline=True)
    
    if poll_type == "yes_no":
        keyboard.add_button('✅ Да', color=VkKeyboardColor.POSITIVE, payload={'poll_id': poll_id, 'option': 0})
        keyboard.add_button('❌ Нет', color=VkKeyboardColor.NEGATIVE, payload={'poll_id': poll_id, 'option': 1})
    elif poll_type == "go_not_go":
        keyboard.add_button('🎯 Иду', color=VkKeyboardColor.POSITIVE, payload={'poll_id': poll_id, 'option': 0})
        keyboard.add_button('🚫 Не иду', color=VkKeyboardColor.NEGATIVE, payload={'poll_id': poll_id, 'option': 1})
    elif poll_type == "custom":
        keyboard.add_button('Вариант 1', color=VkKeyboardColor.PRIMARY, payload={'poll_id': poll_id, 'option': 0})
        keyboard.add_button('Вариант 2', color=VkKeyboardColor.SECONDARY, payload={'poll_id': poll_id, 'option': 1})
    
    keyboard.add_line()
    keyboard.add_button('📊 Результаты', color=VkKeyboardColor.DEFAULT, payload={'results': poll_id})
    
    return keyboard.get_keyboard()

# Получение даты для дня недели
def get_date_for_weekday(day_index, week_offset=0):
    today = datetime.datetime.now()
    # Находим понедельник текущей недели
    monday = today - datetime.timedelta(days=today.weekday())
    # Добавляем смещение недели и дня
    target_date = monday + datetime.timedelta(weeks=week_offset, days=day_index)
    return target_date

# Форматирование расписания на сегодня
def format_schedule_today(schedule_data, last_updated=""):
    if not schedule_data:
        return "Расписание пока не добавлено."
    
    today = datetime.datetime.now()
    day_name = days_of_week[today.weekday()]
    day_name_cap = days_of_week_capitalized[today.weekday()]
    day_num = today.day
    month_name = months[today.month - 1]
    date_str = f"{day_name_cap}, {day_num} {month_name}"
    
    separator = "·" * 60
    
    response = f"{separator}\n"
    response += f"📅 {date_str}\n"
    response += f"{separator}\n\n"
    
    if day_name in schedule_data and schedule_data[day_name]:
        for lesson in schedule_data[day_name]:
            time_range = time_slots.get(lesson['pair'], f"Пара {lesson['pair']}")
            response += f"⏳ {lesson['pair']} пара ({time_range})\n"
            response += f"📚 Предмет: {lesson['subject']}\n"
            response += f"🏫 Тип: {lesson.get('type', 'Занятие')}\n"
            response += f"👤 Преподаватель: {lesson['teacher']}\n"
            response += f"🚪 Аудитория: {lesson['room']}\n\n"
    else:
        response += " Занятий нет\n\n"
    
    if last_updated:
        try:
            update_dt = datetime.datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
            update_str = update_dt.strftime(f"%d {months[update_dt.month - 1]} %Y в %H:%M")
            response += f"🔄 Обновлено: {update_str}"
        except:
            response += f"🔄 Обновлено: {last_updated}"
    
    return response

# Форматирование расписания на всю неделю
def format_schedule_week(schedule_data, last_updated="", week_offset=0):
    if not schedule_data:
        return "Расписание пока не добавлено."
    
    separator = "·" * 60
    response = ""
    
    today = datetime.datetime.now()
    today_name = days_of_week[today.weekday()]
    
    for i, day_name in enumerate(days_of_week):
        # Получаем дату для этого дня недели
        day_date = get_date_for_weekday(i, week_offset)
        day_num = day_date.day
        month_name = months[day_date.month - 1]
        day_name_cap = days_of_week_capitalized[i]
        
        response += f"{separator}\n"
        
        # Проверяем, сегодня ли это
        is_today = (week_offset == 0 and day_name == today_name)
        
        if is_today:
            response += f"🎯 {day_name_cap}, {day_num} {month_name} (сегодня)\n"
        else:
            response += f"📅 {day_name_cap}, {day_num} {month_name}\n"
        
        response += f"{separator}\n\n"
        
        if day_name in schedule_data and schedule_data[day_name]:
            for lesson in schedule_data[day_name]:
                time_range = time_slots.get(lesson['pair'], f"Пара {lesson['pair']}")
                response += f"⏳ {lesson['pair']} пара ({time_range})\n"
                response += f"📚 Предмет: {lesson['subject']}\n"
                response += f"🏫 Тип: {lesson.get('type', 'Занятие')}\n"
                response += f"👤 Преподаватель: {lesson['teacher']}\n"
                response += f"🚪 Аудитория: {lesson['room']}\n\n"
        else:
            response += " Занятий нет\n\n"
    
    if last_updated:
        try:
            update_dt = datetime.datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
            update_str = update_dt.strftime(f"%d {months[update_dt.month - 1]} %Y в %H:%M")
            response += f"🔄 Обновлено: {update_str}"
        except:
            response += f"🔄 Обновлено: {last_updated}"
    
    return response

# Функция для отправки сообщения с клавиатурой
def send_message(peer_id, message, keyboard=None):
    try:
        random_id = get_random_id()
        params = {
            'peer_id': peer_id,
            'message': message,
            'random_id': random_id,
        }
        if keyboard:
            params['keyboard'] = keyboard
            
        vk_session.method('messages.send', params)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

# Проверка является ли пользователь админом
def is_admin(user_id):
    return user_id == CONFIG['admin_id']

# Создание опроса
def create_poll(question, options, creator_id):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    poll_id = str(random.randint(100000, 999999))
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO polls (poll_id, question, options, votes, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
        (poll_id, question, json.dumps(options), json.dumps({}), current_time, creator_id)
    )
    
    conn.commit()
    conn.close()
    return poll_id

# Голосование в опросе
def vote_in_poll(poll_id, user_id, option_index):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT votes FROM polls WHERE poll_id = ?", (poll_id,))
    result = cursor.fetchone()
    
    if result:
        votes = json.loads(result[0])
        # Удаляем предыдущий голос пользователя
        votes = {k: v for k, v in votes.items() if v != user_id}
        # Добавляем новый голос
        votes[str(option_index)] = user_id
        
        cursor.execute("UPDATE polls SET votes = ? WHERE poll_id = ?", (json.dumps(votes), poll_id))
        conn.commit()
    
    conn.close()

# Получение результатов опроса
def get_poll_results(poll_id):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT question, options, votes FROM polls WHERE poll_id = ?", (poll_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        question, options_json, votes_json = result
        options = json.loads(options_json)
        votes = json.loads(votes_json)
        
        # Подсчет голосов
        results = {i: 0 for i in range(len(options))}
        for option_index in votes.values():
            results[int(option_index)] += 1
        
        return question, options, results
    return None, None, None

# Сохранение вопроса
def save_question(question, user_id):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO questions (question, asked_by, asked_at) VALUES (?, ?, ?)",
        (question, user_id, current_time)
    )
    
    conn.commit()
    conn.close()

# Поиск ответа на вопрос
def find_answer(question):
    question_lower = question.lower()
    
    # Поиск по ключевым словам
    for keyword, answer in faq_database.items():
        if keyword in question_lower:
            return answer
    
    # Если ответ не найден
    return None

# Добавление FAQ админом
def add_faq(keyword, answer, admin_id):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Добавляем в базу
    cursor.execute(
        "INSERT INTO faq (keyword, answer, added_by, added_at) VALUES (?, ?, ?, ?)",
        (keyword.lower(), answer, admin_id, current_time)
    )
    
    # Обновляем кэш
    faq_database[keyword.lower()] = answer
    
    conn.commit()
    conn.close()
    return True

# Просмотр всех FAQ
def get_all_faq():
    return list(faq_database.items())

# Просмотр неотвеченных вопросов
def get_unanswered_questions():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, question, asked_by, asked_at FROM questions WHERE answered = 0 ORDER BY asked_at DESC")
    questions = cursor.fetchall()
    
    conn.close()
    return questions

# Функции для работы с картами
def get_location_map(room_number):
    """Возвращает ссылку на карту с меткой"""
    room_lower = room_number.lower()
    
    # Ищем точное совпадение
    if room_lower in CONFIG['locations']:
        location = CONFIG['locations'][room_lower]
        lat, lon = location['lat'], location['lon']
        return f"📍 {location['name']}\n🚪 Аудитория: {room_number}\n📫 Адрес: {location['address']}\n\n🗺️ Карта: https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map"
    
    # Ищем по частичному совпадению (только цифры)
    room_digits = ''.join(filter(str.isdigit, room_number))
    for room_key, location in CONFIG['locations'].items():
        if room_digits in room_key:
            return f"📍 {location['name']}\n🚪 Аудитория: {room_number}\n📫 Адрес: {location['address']}\n\n🗺️ Карта: https://yandex.ru/maps/?pt={location['lon']},{location['lat']}&z=17&l=map"
    
    return None

def find_room_in_schedule(room_query):
    """Ищет аудиторию в расписании"""
    schedule, _ = load_schedule()
    found_lessons = []
    
    for day_name, lessons in schedule.items():
        if lessons:
            for lesson in lessons:
                if room_query.lower() in lesson['room'].lower():
                    found_lessons.append({
                        'day': day_name,
                        'pair': lesson['pair'],
                        'subject': lesson['subject'],
                        'room': lesson['room'],
                        'time': time_slots.get(lesson['pair'], '')
                    })
    
    return found_lessons

# Инициализируем БД
init_db()

# Подключаемся к VK
vk_session = vk_api.VkApi(token=CONFIG['token'])
longpoll = VkBotLongPoll(vk_session, CONFIG['group_id'])
vk = vk_session.get_api()

print("Бот запущен...")

# Переменная для хранения ID беседы
chat_id = None

# Главный цикл обработки событий
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.object.message['text'].strip().lower()
        user_id = event.object.message['from_id']
        peer_id = event.object.message['peer_id']
        original_text = event.object.message['text']
        
        # Сохраняем ID беседы при первом сообщении
        if event.from_chat and chat_id is None:
            chat_id = peer_id
            print(f"Бот добавлен в беседу: {chat_id}")
        
        # Обработка команд в беседе
        if event.from_chat:
            if msg == 'расписание' or msg == 'сегодня':
                CONFIG["current_view"] = "today"
                schedule, last_updated = load_schedule()
                response = format_schedule_today(schedule, last_updated)
                send_message(peer_id, response, create_keyboard())
            
            elif msg == 'неделя':
                CONFIG["current_week"] = 1
                CONFIG["current_view"] = "week"
                schedule, last_updated = load_schedule()
                response = format_schedule_week(schedule, last_updated, 0)
                send_message(peer_id, response, create_keyboard())
            
            elif msg == 'след неделя':
                CONFIG["current_week"] = 2
                CONFIG["current_view"] = "next_week"
                schedule, last_updated = load_schedule()
                response = format_schedule_week(schedule, last_updated, 1)
                send_message(peer_id, response, create_keyboard())
            
            # Поиск аудитории на карте
            elif msg.startswith('!где '):
                room_query = original_text[5:].strip()
                if room_query:
                    # Пытаемся найти на карте
                    map_info = get_location_map(room_query)
                    if map_info:
                        send_message(peer_id, map_info)
                    else:
                        # Ищем в расписании
                        found_lessons = find_room_in_schedule(room_query)
                        if found_lessons:
                            response = f"🔍 Найдено в расписании для '{room_query}':\n\n"
                            for lesson in found_lessons:
                                response += f"📅 {lesson['day']}, {lesson['pair']} пара ({lesson['time']})\n"
                                response += f"📚 {lesson['subject']}\n"
                                response += f"🚪 {lesson['room']}\n\n"
                            send_message(peer_id, response)
                        else:
                            send_message(peer_id, f"❌ Аудитория '{room_query}' не найдена ни на карте, ни в расписании")
                else:
                    send_message(peer_id, "❌ Укажите номер аудитории после !где")
            
            # Показать все аудитории
            elif msg == '!аудитории':
                response = "🗺️ Доступные аудитории:\n\n"
                for room, info in CONFIG['locations'].items():
                    response += f"🚪 {room} - {info['name']}\n"
                response += "\n🔍 Используйте: !где [номер аудитории]"
                send_message(peer_id, response)

            # Поиск где сейчас должна быть пара
            elif msg == '!где я должен быть':
                today = datetime.datetime.now()
                day_name = days_of_week[today.weekday()]
                schedule, _ = load_schedule()
                
                if day_name in schedule and schedule[day_name]:
                    current_time = today.strftime("%H:%M")
                    current_lesson = None
                    
                    for lesson in schedule[day_name]:
                        time_range = time_slots.get(lesson['pair'], '')
                        if time_range:
                            start_time = time_range.split('—')[0]
                            # Простой поиск текущей пары
                            if current_time >= start_time:
                                current_lesson = lesson
                    
                    if current_lesson:
                        room = current_lesson['room']
                        map_info = get_location_map(room)
                        if map_info:
                            response = f"🎯 Сейчас у вас должна быть:\n"
                            response += f"📚 {current_lesson['subject']}\n"
                            response += f"👤 {current_lesson['teacher']}\n\n"
                            response += map_info
                            send_message(peer_id, response)
                        else:
                            send_message(peer_id, f"📚 Сейчас: {current_lesson['subject']} в {room}")
                    else:
                        send_message(peer_id, "✅ Сейчас пар нет, можно отдыхать!")
                else:
                    send_message(peer_id, "📅 Сегодня занятий нет")
            
            # Обработка вопросов
            elif msg.startswith('!вопрос '):
                question = original_text[8:].strip()
                if question:
                    # Сохраняем вопрос в базу
                    save_question(question, user_id)
                    
                    # Ищем ответ в базе знаний
                    answer = find_answer(question)
                    if answer:
                        send_message(peer_id, f"🤖 {answer}")
                    else:
                        send_message(peer_id, "❌ Пока не знаю ответ на этот вопрос. Администратору отправлено уведомление!")
                        
                        # Уведомляем админа
                        if CONFIG['admin_id']:
                            admin_msg = f"📩 Новый вопрос от @id{user_id}:\n{question}"
                            send_message(CONFIG['admin_id'], admin_msg)
                else:
                    send_message(peer_id, "❌ Напишите вопрос после команды !вопрос")
            
            # Обработка команд опросов (только админ)
            elif is_admin(user_id):
                if msg.startswith('!опрос '):
                    question = original_text[7:].strip()
                    if ' или ' in question:
                        options = [opt.strip() for opt in question.split(' или ')]
                        poll_id = create_poll(question, options, user_id)
                        response = f"📊 ОПРОС:\n{question}\n\n"
                        for i, option in enumerate(options):
                            response += f"{i+1}. {option}\n"
                        
                        send_message(peer_id, response, create_poll_keyboard("custom", poll_id))
                
                elif msg.startswith('!голосование '):
                    question = original_text[13:].strip()
                    poll_id = create_poll(question, ["✅ Да", "❌ Нет"], user_id)
                    response = f"📊 ГОЛОСОВАНИЕ:\n{question}"
                    send_message(peer_id, response, create_poll_keyboard("yes_no", poll_id))
                    
                elif msg.startswith('!иду '):
                    question = original_text[5:].strip()
                    poll_id = create_poll(question, ["🎯 Иду", "🚫 Не иду"], user_id)
                    response = f"📊 КТО ИДЕТ:\n{question}"
                    send_message(peer_id, response, create_poll_keyboard("go_not_go", poll_id))
            
            continue
        
        # Обработка нажатий на кнопки опросов
        if event.from_chat and 'payload' in event.object.message:
            try:
                payload = json.loads(event.object.message['payload'])
                if 'poll_id' in payload:
                    poll_id = payload['poll_id']
                    option_index = payload['option']
                    
                    vote_in_poll(poll_id, user_id, option_index)
                    send_message(peer_id, "✅ Ваш голос учтен!")
                    
                elif 'results' in payload:
                    poll_id = payload['results']
                    question, options, results = get_poll_results(poll_id)
                    
                    if question and results:
                        response = f"📊 РЕЗУЛЬТАТЫ ОПРОСА:\n{question}\n\n"
                        for i, option in enumerate(options):
                            votes = results.get(i, 0)
                            response += f"{option}: {votes} голосов\n"
                        
                        send_message(peer_id, response)
                    else:
                        send_message(peer_id, "❌ Опрос не найден")
                        
            except json.JSONDecodeError:
                pass
        
        # Обработка команд из личных сообщений (только для админа)
        if event.from_user and is_admin(user_id):
            # Команды переключения недели
            if msg == '!следующая неделя':
                CONFIG["current_week"] = 2
                send_message(peer_id, "✅ Переключено на следующую неделю")
                continue
                
            elif msg == '!текущая неделя':
                CONFIG["current_week"] = 1
                send_message(peer_id, "✅ Переключено на текущую неделю")
                continue
            
            # Команды управления FAQ
            elif msg.startswith('!добавить вопрос '):
                parts = original_text[17:].split(' ответ ')
                if len(parts) == 2:
                    keyword = parts[0].strip().lower()
                    answer = parts[1].strip()
                    if add_faq(keyword, answer, user_id):
                        send_message(peer_id, f"✅ Вопрос добавлен:\nКлюч: {keyword}\nОтвет: {answer}")
                    else:
                        send_message(peer_id, "❌ Ошибка добавления вопроса")
                else:
                    send_message(peer_id, "❌ Формат: !добавить вопрос [ключ] ответ [ответ]")
            
            elif msg == '!все вопросы':
                faq_list = get_all_faq()
                if faq_list:
                    response = "📋 Все вопросы-ответы:\n\n"
                    for i, (keyword, answer) in enumerate(faq_list, 1):
                        response += f"{i}. {keyword} → {answer}\n"
                    send_message(peer_id, response)
                else:
                    send_message(peer_id, "❌ Нет добавленных вопросов")
            
            elif msg == '!неотвеченные':
                questions = get_unanswered_questions()
                if questions:
                    response = "📋 Неотвеченные вопросы:\n\n"
                    for i, (q_id, question, user_id, asked_at) in enumerate(questions, 1):
                        response += f"{i}. {question}\n   👤 @id{user_id} в {asked_at}\n\n"
                    send_message(peer_id, response)
                else:
                    send_message(peer_id, "✅ Нет неотвеченных вопросов")
            
            # Добавление аудитории на карту
            elif msg.startswith('!добавить аудиторию '):
                try:
                    # Формат: !добавить аудиторию номер;название;адрес;широта;долгота
                    parts = original_text[20:].split(';')
                    if len(parts) == 5:
                        room = parts[0].strip().lower()
                        name = parts[1].strip()
                        address = parts[2].strip()
                        lat = float(parts[3].strip())
                        lon = float(parts[4].strip())
                        
                        CONFIG['locations'][room] = {
                            'name': name,
                            'address': address,
                            'lat': lat,
                            'lon': lon
                        }
                        
                        send_message(peer_id, f"✅ Аудитория {room} добавлена на карту!")
                    else:
                        send_message(peer_id, "❌ Формат: !добавить аудиторию номер;название;адрес;широта;долгота")
                except:
                    send_message(peer_id, "❌ Ошибка в формате данных")
            
            # Попытка распарсить JSON для обновления расписания
            try:
                new_schedule = json.loads(original_text)
                if isinstance(new_schedule, dict):
                    update_time = save_schedule(new_schedule)
                    
                    send_message(peer_id, f"✅ Расписание обновлено! {update_time}")
                    
                    if chat_id:
                        try:
                            week_status = "Текущая неделя" if CONFIG["current_week"] == 1 else "Следующая неделя"
                            announcement = f"🎉 РАСПИСАНИЕ ОБНОВЛЕНО! 🎉\n\n{week_status}\n\n"
                            week_offset = 0 if CONFIG["current_week"] == 1 else 1
                            announcement += format_schedule_week(new_schedule, update_time, week_offset)
                            send_message(chat_id, announcement, create_keyboard())
                        except Exception as e:
                            send_message(peer_id, f"❌ Не удалось отправить в беседу: {e}")
                    else:
                        send_message(peer_id, "⚠️ Бот не добавлен в беседу или не админ")
                    
            except json.JSONDecodeError:
                if original_text.lower().startswith('уведомление:'):
                    notification_text = original_text[12:].strip()
                    if notification_text and chat_id:
                        try:
                            important_msg = "🔔 ВАЖНОЕ УВЕДОМЛЕНИЕ 🔔\n\n" + notification_text
                            send_message(chat_id, important_msg)
                            send_message(peer_id, "✅ Уведомление отправлено в беседу!")
                        except Exception as e:
                            send_message(peer_id, f"❌ Не удалось отправить уведомление: {e}")
