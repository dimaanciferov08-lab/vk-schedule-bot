import vk_api
import json
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import datetime

# !!! ЗАПОЛНИ ЭТИ ДАННЫЕ СВОИМИ !!!
CONFIG = {
    "group_id": 232761329,
    "token": "vk1.a.Y2xBv4alWQ55rd1IxtkpKc48ibKqpQ1x0Wyc9Hv0z18elxu3JaSBfCi7F5sJ9H4eKy1jg3iqFOjQTkQyCIYdnf77mcezdC__MLiyRi9Xwfus_uLz7UWd9AR8VPQDr7uMEiD1NxadTzqUllP7p4uqWixuefYkm6ryhgMbFLPSo-hnXKyt0XQ4qvpfIG5kLWlJoH7Ivew1yhgiKmtDWhbHYw",
    "admin_id": 238448950,
    "current_week": 1,
    "current_view": "today"  # today, week, next_week
}

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
    cursor.execute("INSERT OR IGNORE INTO schedule_week1 (id, data, last_updated) VALUES (1, '{}', '')")
    cursor.execute("INSERT OR IGNORE INTO schedule_week2 (id, data, last_updated) VALUES (1, '{}', '')")
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

            continue

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