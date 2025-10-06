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
        "406с": {"lat": 59.9350, "lon": 30.3358, "name": "Корпус С", "address": "Советская, 14"},
        "413b": {"lat": 59.9343, "lon": 30.3352, "name": "Корпус B", "address": "пр.Кирова,д.2"},
        "312b": {"lat": 59.9343, "lon": 30.3352, "name": "Корпус B", "address": "пр.Кирова,д.2"},
        "417b": {"lat": 59.9343, "lon": 30.3352, "name": "Корпус B", "address": "пр.Кирова,д.2"},
        "523с": {"lat": 59.9350, "lon": 30.3358, "name": "Корпус С", "address": "Советская, 14"},
        "14ап": {"lat": 59.9352, "lon": 30.3360, "name": "Корпус П", "address": "Советская, 10"},
        "513л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "кск": {"lat": 59.9355, "lon": 30.3365, "name": "Корпус КСК", "address": "Колхозная,15"}
    }
}

# База знаний вопросов-ответов
faq_database = {}

# Список группы
GROUP_LIST = {
    "1": "Амосов Никита",
    "2": "Богомолов Георгий", 
    "3": "Веселов Даниил",
    "4": "Громов Роман",
    "5": "Долотин Иван",
    "6": "Дударев Святослав",
    "7": "Зуев Андрей",
    "8": "Иванов Матвей",
    "9": "Карпов Дмитрий",
    "10": "Клещев Сергей",
    "11": "Лебедев Кирилл",
    "12": "Назаренков Иван",
    "13": "Святец Александр",
    "14": "Семенов Леонид",
    "15": "Фомичева Елизавета",
    "16": "Шевченко Дарья",
    "17": "Яременко Антон"
}

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # Расписание на 4 недели вперед
    for week in range(1, 5):
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS schedule_week{week} (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                week_start_date TEXT NOT NULL
            )
        ''')
        cursor.execute(f"INSERT OR IGNORE INTO schedule_week{week} (id, data, last_updated, week_start_date) VALUES (1, '{{}}', '', '')")
    
    # Остальные таблицы
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            task TEXT NOT NULL,
            added_by INTEGER NOT NULL,
            added_at TEXT NOT NULL,
            deadline TEXT
        )
    ''')
    
    # Новая таблица для системы докладов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports_system (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            report_data TEXT NOT NULL,
            max_reports_per_student INTEGER DEFAULT 1,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            student_number TEXT NOT NULL,
            student_name TEXT NOT NULL,
            registered_at TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            report_number INTEGER NOT NULL,
            report_title TEXT NOT NULL,
            assigned_at TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            added_by INTEGER NOT NULL,
            added_at TEXT NOT NULL
        )
    ''')
    
    # Загружаем FAQ из базы
    cursor.execute("SELECT keyword, answer FROM faq")
    for keyword, answer in cursor.fetchall():
        faq_database[keyword] = answer
    
    # Добавляем основного админа если его нет
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (CONFIG['admin_id'],))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (CONFIG['admin_id'], CONFIG['admin_id'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    conn.commit()
    conn.close()

# Функции для системы докладов
def register_student(user_id, student_number):
    """Регистрация студента в системе"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    if student_number not in GROUP_LIST:
        conn.close()
        return False, "❌ Номер не найден в списке группы!"
    
    student_name = GROUP_LIST[student_number]
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO student_registry (user_id, student_number, student_name, registered_at) VALUES (?, ?, ?, ?)",
            (user_id, student_number, student_name, current_time)
        )
        conn.commit()
        conn.close()
        return True, f"✅ Вы успешно зарегистрированы как: {student_number} - {student_name}"
    except Exception as e:
        conn.close()
        return False, f"❌ Ошибка регистрации: {str(e)}"

def get_student_info(user_id):
    """Получение информации о студенте"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT student_number, student_name FROM student_registry WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result

def create_subject(subject_name, admin_id):
    """Создание нового предмета для докладов"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Проверяем, существует ли уже предмет
    cursor.execute("SELECT id FROM reports_system WHERE subject_name = ?", (subject_name,))
    if cursor.fetchone():
        conn.close()
        return False, "❌ Предмет с таким названием уже существует!"
    
    # Создаем предмет с пустым списком докладов
    cursor.execute(
        "INSERT INTO reports_system (subject_name, report_data, created_by, created_at) VALUES (?, ?, ?, ?)",
        (subject_name, json.dumps({}), admin_id, current_time)
    )
    
    conn.commit()
    conn.close()
    return True, f"✅ Предмет '{subject_name}' успешно создан!"

def add_report_to_subject(subject_name, report_number, report_title, max_per_student, admin_id):
    """Добавление доклада к предмету"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # Получаем текущие данные предмета
    cursor.execute("SELECT id, report_data FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "❌ Предмет не найден!"
    
    subject_id, report_data_json = result
    report_data = json.loads(report_data_json)
    
    # Проверяем, существует ли уже доклад с таким номером
    if str(report_number) in report_data:
        conn.close()
        return False, "❌ Доклад с таким номером уже существует!"
    
    # Добавляем доклад
    report_data[str(report_number)] = {
        "title": report_title,
        "taken_by": None,
        "max_per_student": max_per_student
    }
    
    # Обновляем данные
    cursor.execute(
        "UPDATE reports_system SET report_data = ?, max_reports_per_student = ? WHERE id = ?",
        (json.dumps(report_data, ensure_ascii=False), max_per_student, subject_id)
    )
    
    conn.commit()
    conn.close()
    return True, f"✅ Доклад #{report_number} добавлен к предмету '{subject_name}'"

def take_report_for_student(user_id, subject_name, report_number):
    """Закрепление доклада за студентом"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # Проверяем, зарегистрирован ли студент
    student_info = get_student_info(user_id)
    if not student_info:
        conn.close()
        return False, "❌ Сначала зарегистрируйтесь! Отправьте 'Я [ваш номер]'"
    
    student_number, student_name = student_info
    
    # Получаем данные предмета
    cursor.execute("SELECT report_data, max_reports_per_student FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "❌ Предмет не найден!"
    
    report_data_json, max_reports = result
    report_data = json.loads(report_data_json)
    
    # Проверяем существование доклада
    if str(report_number) not in report_data:
        conn.close()
        return False, "❌ Доклад с таким номером не найден!"
    
    report_info = report_data[str(report_number)]
    
    # Проверяем, не занят ли доклад
    if report_info["taken_by"]:
        conn.close()
        return False, "❌ Этот доклад уже занят!"
    
    # Проверяем лимит докладов для студента
    cursor.execute(
        "SELECT COUNT(*) FROM report_assignments WHERE user_id = ? AND subject_name = ?", 
        (user_id, subject_name)
    )
    current_count = cursor.fetchone()[0]
    
    if current_count >= max_reports:
        conn.close()
        return False, f"❌ Вы уже взяли максимальное количество докладов ({max_reports}) по этому предмету!"
    
    # Закрепляем доклад за студентом
    report_info["taken_by"] = student_number
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Обновляем данные предмета
    cursor.execute(
        "UPDATE reports_system SET report_data = ? WHERE subject_name = ?",
        (json.dumps(report_data, ensure_ascii=False), subject_name)
    )
    
    # Добавляем запись о назначении
    cursor.execute(
        "INSERT INTO report_assignments (user_id, subject_name, report_number, report_title, assigned_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, subject_name, report_number, report_info["title"], current_time)
    )
    
    conn.commit()
    conn.close()
    return True, f"✅ Доклад успешно закреплен за вами!\n📚 {subject_name}\n📄 Доклад #{report_number}: {report_info['title']}"

def get_subject_reports(subject_name):
    """Получение списка докладов по предмету"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT report_data FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return None
    
    report_data = json.loads(result[0])
    conn.close()
    return report_data

def get_student_reports(user_id):
    """Получение докладов студента"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT subject_name, report_number, report_title, assigned_at FROM report_assignments WHERE user_id = ? ORDER BY assigned_at DESC",
        (user_id,)
    )
    reports = cursor.fetchall()
    conn.close()
    return reports

def get_all_subjects():
    """Получение всех предметов"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT subject_name, max_reports_per_student FROM reports_system WHERE is_active = 1")
    subjects = cursor.fetchall()
    conn.close()
    return subjects

def is_admin(user_id):
    """Проверка является ли пользователь админом"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() is not None
    conn.close()
    
    return result or user_id == CONFIG['admin_id']

def add_admin(new_admin_id, added_by):
    """Добавление нового администратора"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (new_admin_id, added_by, current_time)
        )
        conn.commit()
        conn.close()
        return True, f"✅ Пользователь @id{new_admin_id} добавлен как администратор"
    except Exception as e:
        conn.close()
        return False, f"❌ Ошибка добавления администратора: {str(e)}"

# Остальные функции остаются без изменений (load_schedule, save_schedule, format_schedule_day, и т.д.)
# ... [здесь должны быть все остальные функции из предыдущего кода] ...

# Автоматическое определение номера недели
def get_current_week_number():
    today = datetime.datetime.now()
    year_start = datetime.datetime(today.year, 9, 1)
    week_num = (today - year_start).days // 7 + 1
    return (week_num % 4) or 4

# Сохранение расписания в БД
def save_schedule(schedule_data, week_number=None):
    if week_number is None:
        week_number = CONFIG['current_week']
    
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    today = datetime.datetime.now()
    monday = today - datetime.timedelta(days=today.weekday())
    week_start = monday.strftime("%Y-%m-%d")
    
    table_name = f"schedule_week{week_number}"
    cursor.execute(f"UPDATE {table_name} SET data = ?, last_updated = ?, week_start_date = ? WHERE id = 1", 
                  (json.dumps(schedule_data, ensure_ascii=False), current_time, week_start))
    
    conn.commit()
    conn.close()
    return current_time

# Загрузка расписания из БД
def load_schedule(week_number=None):
    if week_number is None:
        week_number = CONFIG['current_week']
    
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    table_name = f"schedule_week{week_number}"
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

# Инициализируем БД
init_db()

# Автоматически определяем текущую неделю
CONFIG['current_week'] = get_current_week_number()

# Подключаемся к VK
vk_session = vk_api.VkApi(token=CONFIG['token'])
longpoll = VkBotLongPoll(vk_session, CONFIG['group_id'])
vk = vk_session.get_api()

print("Бот запущен...")

# Главный цикл обработки событий
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.object.message['text'].strip().lower()
        user_id = event.object.message['from_id']
        peer_id = event.object.message['peer_id']
        original_text = event.object.message['text']
        
        # Обработка команд системы докладов
        if event.from_chat:
            # Регистрация студента
            if msg.startswith('я '):
                parts = original_text[2:].strip().split()
                if parts and parts[0].isdigit():
                    student_number = parts[0]
                    success, message = register_student(user_id, student_number)
                    send_message(peer_id, message)
            
            # Показать список предметов
            elif msg == 'доклады':
                subjects = get_all_subjects()
                if subjects:
                    response = "📚 Доступные предметы для докладов:\n\n"
                    for subject_name, max_reports in subjects:
                        response += f"📖 {subject_name} (можно взять: {max_reports})\n"
                    response += "\n🎯 Чтобы посмотреть доклады по предмету: 'Доклады по [предмет]'\n📝 Чтобы взять доклад: 'Беру доклад [номер] по [предмет]'"
                else:
                    response = "📚 Пока нет предметов для докладов"
                send_message(peer_id, response)
            
            # Показать доклады по предмету
            elif msg.startswith('доклады по '):
                subject_name = original_text[11:].strip()
                reports = get_subject_reports(subject_name)
                
                if reports:
                    response = f"📋 Доклады по предмету '{subject_name}':\n\n"
                    free_count = 0
                    
                    for report_num, report_info in sorted(reports.items(), key=lambda x: int(x[0])):
                        status = "✅ Свободен" if not report_info["taken_by"] else f"❌ Занят ({GROUP_LIST.get(report_info['taken_by'], 'Неизвестный')})"
                        if not report_info["taken_by"]:
                            free_count += 1
                        
                        response += f"📄 {report_num}. {report_info['title'][:50]}...\n"
                        response += f"   {status}\n\n"
                    
                    response += f"📊 Свободно докладов: {free_count}/{len(reports)}"
                else:
                    response = f"❌ Предмет '{subject_name}' не найден или в нем нет докладов"
                send_message(peer_id, response)
            
            # Взять доклад
            elif msg.startswith('беру доклад '):
                try:
                    # Парсим команду "Беру доклад X по Y"
                    parts = original_text[12:].strip().split(' по ')
                    if len(parts) == 2:
                        report_number = int(parts[0].strip())
                        subject_name = parts[1].strip()
                        
                        success, message = take_report_for_student(user_id, subject_name, report_number)
                        send_message(peer_id, message)
                    else:
                        send_message(peer_id, "❌ Формат: Беру доклад [номер] по [предмет]")
                except ValueError:
                    send_message(peer_id, "❌ Неверный номер доклада")
                except Exception as e:
                    send_message(peer_id, f"❌ Ошибка: {str(e)}")
            
            # Мои доклады
            elif msg == 'мои доклады':
                student_info = get_student_info(user_id)
                if not student_info:
                    send_message(peer_id, "❌ Сначала зарегистрируйтесь! Отправьте 'Я [ваш номер]'")
                else:
                    student_number, student_name = student_info
                    reports = get_student_reports(user_id)
                    
                    if reports:
                        response = f"📚 Ваши доклады ({student_number} - {student_name}):\n\n"
                        for subject, report_num, title, assigned_at in reports:
                            response += f"📖 {subject}\n"
                            response += f"📄 Доклад #{report_num}: {title}\n"
                            response += f"🕐 Взято: {assigned_at}\n\n"
                    else:
                        response = "❌ У вас пока нет взятых докладов"
                    send_message(peer_id, response)
            
            # Команды для администраторов
            elif is_admin(user_id):
                # Создать предмет
                if msg.startswith('!создать предмет '):
                    subject_name = original_text[16:].strip()
                    if subject_name:
                        success, message = create_subject(subject_name, user_id)
                        send_message(peer_id, message)
                    else:
                        send_message(peer_id, "❌ Укажите название предмета")
                
                # Добавить доклад
                elif msg.startswith('!добавить доклад '):
                    try:
                        # Формат: !добавить доклад [предмет];[номер];[название];[макс.кол-во]
                        parts = original_text[17:].strip().split(';')
                        if len(parts) >= 3:
                            subject_name = parts[0].strip()
                            report_number = int(parts[1].strip())
                            report_title = parts[2].strip()
                            max_per_student = int(parts[3]) if len(parts) > 3 else 1
                            
                            success, message = add_report_to_subject(subject_name, report_number, report_title, max_per_student, user_id)
                            send_message(peer_id, message)
                        else:
                            send_message(peer_id, "❌ Формат: !добавить доклад [предмет];[номер];[название];[макс.кол-во]")
                    except ValueError:
                        send_message(peer_id, "❌ Неверный формат чисел")
                    except Exception as e:
                        send_message(peer_id, f"❌ Ошибка: {str(e)}")
                
                # Добавить администратора
                elif msg.startswith('!добавить админа '):
                    try:
                        new_admin_id = int(original_text[17:].strip())
                        success, message = add_admin(new_admin_id, user_id)
                        send_message(peer_id, message)
                    except ValueError:
                        send_message(peer_id, "❌ Неверный ID пользователя")
                
                # Статистика по предмету
                elif msg.startswith('!статистика '):
                    subject_name = original_text[12:].strip()
                    reports = get_subject_reports(subject_name)
                    
                    if reports:
                        total = len(reports)
                        taken = sum(1 for r in reports.values() if r["taken_by"])
                        free = total - taken
                        
                        response = f"📊 Статистика по предмету '{subject_name}':\n\n"
                        response += f"• Всего докладов: {total}\n"
                        response += f"• Занято: {taken}\n"
                        response += f"• Свободно: {free}\n"
                        response += f"• Процент выполнения: {taken/total*100:.1f}%\n\n"
                        
                        if taken > 0:
                            response += "👥 Студенты с докладами:\n"
                            for report_num, report_info in reports.items():
                                if report_info["taken_by"]:
                                    student_name = GROUP_LIST.get(report_info["taken_by"], "Неизвестный")
                                    response += f"• {student_name} - доклад #{report_num}\n"
                    else:
                        response = f"❌ Предмет '{subject_name}' не найден"
                    send_message(peer_id, response)
            
            # Обработка остальных команд (расписание, ДЗ и т.д.)
            # ... [здесь должен быть остальной код обработки команд] ...
            
            continue
        
        # Обработка личных сообщений для администраторов
        if event.from_user and is_admin(user_id):
            # Обработка JSON для расписания
            try:
                new_schedule = json.loads(original_text)
                if isinstance(new_schedule, dict):
                    update_time = save_schedule(new_schedule)
                    send_message(peer_id, f"✅ Расписание обновлено! {update_time}")
            except json.JSONDecodeError:
                # Обработка других команд админа
                pass

# ... [остальной код остается без изменений] ...
