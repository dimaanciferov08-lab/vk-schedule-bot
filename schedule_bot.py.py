import vk_api
import json
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import sqlite3
import datetime
import time
import threading
import requests
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import re
import logging
import wikipediaapi

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 🔑 НАСТРОЙКИ
CONFIG = {
    "group_id": 232761329,
    "token": "vk1.a.Y2xBv4alWQ55rd1IxtkpKc48ibKqpQ1x0Wyc9Hv0z18elxu3JaSBfCi7F5sJ9H4eKy1jg3iqFOjQTkQyCIYdnf77mcezdC__MLiyRi9Xwfus_uLz7UWd9AR8VPQDr7uMEiD1NxadTzqUllP7p4uqWixuefYkm6ryhgMbFLPSo-hnXKyt0XQ4qvpfIG5kLWlJoH7Ivew1yhgiKmtDWhbHYw",
    "admin_id": 238448950,
    "current_week": 1,
    "chat_id": None
}

# Список группы
GROUP_LIST = {
    "1": "Амосов Никита", "2": "Богомолов Георгий", "3": "Веселов Даниил",
    "4": "Громов Роман", "5": "Долотин Иван", "6": "Дударев Святослав",
    "7": "Зуев Андрей", "8": "Иванов Матвей", "9": "Карпов Дмитрий",
    "10": "Клещев Сергей", "11": "Лебедев Кирилл", "12": "Назаренков Иван",
    "13": "Святец Александр", "14": "Семенов Леонид", "15": "Фомичева Елизавета",
    "16": "Шевченко Дарья", "17": "Яременко Антон"
}

# === КЛАСС ДЛЯ СОЗДАНИЯ РЕФЕРАТОВ ===
class ReferatGenerator:
    def __init__(self):
        self.wiki_wiki = wikipediaapi.Wikipedia(
            language='ru',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent="VKStudentBot/1.0"
        )
    
    def search_wikipedia(self, topic):
        """Поиск в Wikipedia"""
        try:
            page = self.wiki_wiki.page(topic)
            if page.exists():
                return {
                    'title': page.title,
                    'content': page.text[:3000],  # Ограничиваем объем
                    'url': page.fullurl,
                    'exists': True
                }
            return {'exists': False}
        except Exception as e:
            logging.error(f"Ошибка Wikipedia: {e}")
            return {'exists': False}
    
    def create_referat_structure(self, topic):
        """Создание структуры реферата"""
        # Пытаемся получить данные из Wikipedia
        wiki_data = self.search_wikipedia(topic)
        
        if wiki_data.get('exists'):
            # Используем данные из Wikipedia
            content = wiki_data['content']
            sentences = content.split('. ')[:10]  # Берем первые 10 предложений
            
            introduction = f"""Актуальность темы '{topic}' обусловлена ее значимостью. {sentences[0] if sentences else 'Данная тема представляет научный и практический интерес.'}

Цель данного реферата - комплексное изучение и анализ темы "{topic}".

Задачи исследования:
1. Изучить теоретические аспекты {topic.lower()}
2. Проанализировать основные характеристики
3. Рассмотреть практическое применение"""
            
            chapters = [
                {
                    'title': 'Основные понятия и история',
                    'content': f"{'. '.join(sentences[1:4]) if len(sentences) > 4 else 'Рассматриваются исторические аспекты и основные определения.'}"
                },
                {
                    'title': 'Современное состояние', 
                    'content': f"{'. '.join(sentences[4:8]) if len(sentences) > 8 else 'Анализируется современное состояние и практическое значение.'}"
                }
            ]
                
            conclusion = f"""В ходе выполнения реферата на тему "{topic}" были достигнуты поставленные цели.

Основные выводы:
1. {sentences[0] if sentences else 'Тема имеет важное значение.'}
2. Обнаружены перспективы для дальнейшего изучения"""
            
        else:
            # Шаблонная структура
            introduction = f"""Актуальность темы '{topic}' обусловлена ее значимостью в современной науке и практике.

Цель данного реферата - комплексный анализ и систематизация знаний по теме "{topic}".

Задачи исследования:
1. Изучить теоретические основы {topic.lower()}
2. Проанализировать ключевые аспекты и характеристики  
3. Рассмотреть практическое применение и перспективы развития"""
            
            chapters = [
                {
                    'title': 'Теоретические аспекты изучения темы',
                    'content': f"Тема '{topic}' представляет значительный интерес для современной науки. В данной главе рассматриваются основные понятия и теоретические основы изучения данной проблематики."
                },
                {
                    'title': 'Анализ современных подходов',
                    'content': f"В данной главе анализируются современные подходы к изучению {topic.lower()}. Рассматриваются различные методологии и практические аспекты."
                }
            ]
            
            conclusion = f"""В ходе выполнения реферата на тему "{topic}" были решены поставленные задачи.

Основные выводы:
1. Тема '{topic}' обладает значительным потенциалом для дальнейшего изучения
2. Практическая значимость работы заключается в систематизации знаний"""
        
        structure = {
            'title': f'Реферат на тему: "{topic}"',
            'subject': 'Дисциплина: Общий курс',
            'student_info': 'Выполнил(а): студент группы',
            'introduction': introduction,
            'chapters': chapters,
            'conclusion': conclusion,
            'sources': [
                "Энциклопедические и справочные издания",
                "Научные статьи и периодические издания", 
                "Учебники и методические пособия"
            ],
            'appendix': f"Приложение А\nДополнительные материалы по теме '{topic}'"
        }
        
        if wiki_data.get('exists'):
            structure['sources'].insert(0, f"Wikipedia - {wiki_data['title']}")
            
        return structure
    
    def create_word_document(self, referat_data):
        """Создание Word документа"""
        try:
            doc = Document()
            
            # Настройка стилей
            style = doc.styles['Normal']
            style.font.name = 'Times New Roman'
            style.font.size = Pt(14)
            
            # Титульная страница
            title = doc.add_heading(referat_data['title'], 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_paragraph("\n" * 4)
            doc.add_paragraph(referat_data['subject']).alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph("\n" * 3)
            doc.add_paragraph(referat_data['student_info']).alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph("\n" * 3)
            date_para = doc.add_paragraph(f"Дата создания: {datetime.datetime.now().strftime('%d.%m.%Y')}")
            date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_page_break()
            
            # Содержание
            title = doc.add_heading('СОДЕРЖАНИЕ', level=1)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph()
            doc.add_paragraph("Введение")
            for i, chapter in enumerate(referat_data['chapters'], 1):
                doc.add_paragraph(f"Глава {i}. {chapter['title']}")
            doc.add_paragraph("Заключение")
            doc.add_paragraph("Список использованных источников")
            doc.add_paragraph("Приложение")
            
            doc.add_page_break()
            
            # Введение
            doc.add_heading('ВВЕДЕНИЕ', level=1)
            for paragraph in referat_data['introduction'].split('\n\n'):
                if paragraph.strip():
                    p = doc.add_paragraph(paragraph)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Основные главы
            for i, chapter in enumerate(referat_data['chapters'], 1):
                doc.add_page_break()
                doc.add_heading(f'ГЛАВА {i}. {chapter["title"].upper()}', level=1)
                p = doc.add_paragraph(chapter['content'])
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Заключение
            doc.add_page_break()
            doc.add_heading('ЗАКЛЮЧЕНИЕ', level=1)
            for paragraph in referat_data['conclusion'].split('\n\n'):
                if paragraph.strip():
                    p = doc.add_paragraph(paragraph)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Источники
            doc.add_page_break()
            doc.add_heading('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', level=1)
            for source in referat_data['sources']:
                p = doc.add_paragraph(source, style='List Bullet')
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Приложение
            doc.add_page_break()
            doc.add_heading('ПРИЛОЖЕНИЕ', level=1)
            p = doc.add_paragraph(referat_data['appendix'])
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Сохраняем в байтовый поток
            file_stream = io.BytesIO()
            doc.save(file_stream)
            file_stream.seek(0)
            
            return file_stream
            
        except Exception as e:
            logging.error(f"Ошибка создания документа: {e}")
            return None
    
    def generate_referat(self, topic):
        """Основная функция генерации реферата"""
        try:
            logging.info(f"Начало генерации реферата: {topic}")
            
            # Создаем структуру реферата
            referat_structure = self.create_referat_structure(topic)
            
            if not referat_structure:
                return None, "❌ Не удалось сформировать структуру реферата"
            
            # Создаем документ
            doc_file = self.create_word_document(referat_structure)
            
            if not doc_file:
                return None, "❌ Ошибка при создании документа"
            
            success_message = f"""✅ Реферат на тему '{topic}' успешно создан!

📊 Особенности:
• Профессиональное оформление
• Титульная страница и содержание  
• {len(referat_structure['chapters'])} структурированные главы
• Введение с целями и задачами
• Заключение с выводами
• Список источников

💡 Рекомендации:
• Дополните материал конкретными примерами
• Проверьте уникальность текста"""
            
            return doc_file, success_message
            
        except Exception as e:
            logging.error(f"Ошибка генерации реферата: {e}")
            return None, f"❌ Ошибка при создании реферата"

# Создаем экземпляр генератора рефератов
referat_generator = ReferatGenerator()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
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
    
    # Таблицы для системы докладов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports_system (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL UNIQUE,
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
    
    # Добавляем основного админа
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (CONFIG['admin_id'],))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (CONFIG['admin_id'], CONFIG['admin_id'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

# Функция для отправки сообщения
def send_message(peer_id, message, keyboard=None):
    try:
        params = {
            'peer_id': peer_id,
            'message': message,
            'random_id': get_random_id(),
        }
        if keyboard:
            params['keyboard'] = keyboard.get_keyboard() if hasattr(keyboard, 'get_keyboard') else keyboard
            
        result = vk_session.method('messages.send', params)
        print(f"✅ Сообщение отправлено: {message[:50]}...")
        return result
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return None

# Функции для системы докладов
def register_student(user_id, student_number):
    """Регистрация студента в системе"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
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
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT student_number, student_name FROM student_registry WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result

def create_subject(subject_name, admin_id):
    """Создание нового предмета для докладов"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("SELECT id FROM reports_system WHERE subject_name = ?", (subject_name,))
    if cursor.fetchone():
        conn.close()
        return False, "❌ Предмет с таким названием уже существует!"
    
    cursor.execute(
        "INSERT INTO reports_system (subject_name, report_data, created_by, created_at) VALUES (?, ?, ?, ?)",
        (subject_name, json.dumps({}), admin_id, current_time)
    )
    
    conn.commit()
    conn.close()
    return True, f"✅ Предмет '{subject_name}' успешно создан!"

def add_report_to_subject(subject_name, report_number, report_title, max_per_student, admin_id):
    """Добавление доклада к предмету"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, report_data FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "❌ Предмет не найден!"
    
    subject_id, report_data_json = result
    report_data = json.loads(report_data_json)
    
    if str(report_number) in report_data:
        conn.close()
        return False, "❌ Доклад с таким номером уже существует!"
    
    report_data[str(report_number)] = {
        "title": report_title,
        "taken_by": None,
        "max_per_student": max_per_student
    }
    
    cursor.execute(
        "UPDATE reports_system SET report_data = ?, max_reports_per_student = ? WHERE id = ?",
        (json.dumps(report_data, ensure_ascii=False), max_per_student, subject_id)
    )
    
    conn.commit()
    conn.close()
    return True, f"✅ Доклад #{report_number} добавлен к предмету '{subject_name}'"

def take_report_for_student(user_id, subject_name, report_number):
    """Закрепление доклада за студентом"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    student_info = get_student_info(user_id)
    if not student_info:
        conn.close()
        return False, "❌ Сначала зарегистрируйтесь! Отправьте 'Я [ваш номер]'"
    
    student_number, student_name = student_info
    
    cursor.execute("SELECT report_data, max_reports_per_student FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "❌ Предмет не найден!"
    
    report_data_json, max_reports = result
    report_data = json.loads(report_data_json)
    
    if str(report_number) not in report_data:
        conn.close()
        return False, "❌ Доклад с таким номером не найден!"
    
    report_info = report_data[str(report_number)]
    
    if report_info["taken_by"]:
        conn.close()
        return False, "❌ Этот доклад уже занят!"
    
    cursor.execute(
        "SELECT COUNT(*) FROM report_assignments WHERE user_id = ? AND subject_name = ?", 
        (user_id, subject_name)
    )
    current_count = cursor.fetchone()[0]
    
    if current_count >= max_reports:
        conn.close()
        return False, f"❌ Вы уже взяли максимальное количество докладов ({max_reports}) по этому предмету!"
    
    report_info["taken_by"] = student_number
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ИСПРАВЛЕННАЯ СТРОКА
    cursor.execute(
        "UPDATE reports_system SET report_data = ? WHERE subject_name = ?",
        (json.dumps(report_data, ensure_ascii=False), subject_name)
    )
    
    cursor.execute(
        "INSERT INTO report_assignments (user_id, subject_name, report_number, report_title, assigned_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, subject_name, report_number, report_info["title"], current_time)
    )
    
    conn.commit()
    conn.close()
    return True, f"✅ Доклад успешно закреплен за вами!\n📚 {subject_name}\n📄 Доклад #{report_number}: {report_info['title']}"

def get_subject_reports(subject_name):
    """Получение списка докладов по предмету"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
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
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
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
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT subject_name, max_reports_per_student FROM reports_system WHERE is_active = 1")
    subjects = cursor.fetchall()
    conn.close()
    return subjects

def is_admin(user_id):
    """Проверка является ли пользователь админом"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() is not None
    conn.close()
    
    return result or user_id == CONFIG['admin_id']

def add_admin(new_admin_id, added_by):
    """Добавление нового администратора"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
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

# Функции для расписания
def save_schedule(schedule_data, week_number=None):
    if week_number is None:
        week_number = CONFIG['current_week']
    
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
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

def load_schedule(week_number=None):
    if week_number is None:
        week_number = CONFIG['current_week']
    
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    table_name = f"schedule_week{week_number}"
    cursor.execute(f"SELECT data, last_updated FROM {table_name} WHERE id = 1")
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        data, last_updated = result
        return json.loads(data), last_updated
    return {}, ""

# Русские названия дней
days_of_week = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
days_of_week_capitalized = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

# Форматирование расписания
def format_schedule_day(schedule_data, day_offset=0):
    if not schedule_data:
        return "📅 Расписание пока не добавлено."
    
    target_date = datetime.datetime.now() + datetime.timedelta(days=day_offset)
    day_name = days_of_week[target_date.weekday()]
    day_name_cap = days_of_week_capitalized[target_date.weekday()]
    
    response = f"📅 {day_name_cap}:\n"
    response += "─" * 30 + "\n"
    
    if day_name in schedule_data and schedule_data[day_name]:
        for lesson in schedule_data[day_name]:
            response += f"🕒 {lesson['pair']} пара\n"
            response += f"📚 {lesson['subject']}\n"
            response += f"👤 {lesson['teacher']}\n"
            response += f"🚪 {lesson['room']}\n\n"
    else:
        response += "🎉 Занятий нет\n\n"
    
    return response

def format_schedule_week(schedule_data, week_offset=0):
    if not schedule_data:
        return "📅 Расписание пока не добавлено."
    
    response = ""
    today = datetime.datetime.now()
    
    for i, day_name in enumerate(days_of_week):
        day_date = today + datetime.timedelta(days=i - today.weekday() + (week_offset * 7))
        day_name_cap = days_of_week_capitalized[i]
        
        response += f"📅 {day_name_cap}:\n"
        response += "─" * 30 + "\n"
        
        if day_name in schedule_data and schedule_data[day_name]:
            for lesson in schedule_data[day_name]:
                response += f"🕒 {lesson['pair']} пара: {lesson['subject']}\n"
        else:
            response += "🎉 Занятий нет\n"
        response += "\n"
    
    return response

# Функция для отправки документа
def send_document(peer_id, file_stream, filename, message=""):
    """Отправка документа пользователю"""
    try:
        print(f"📤 Начинаю отправку документа: {filename}")
        
        # Получаем URL для загрузки
        upload_data = vk_session.method('docs.getMessagesUploadServer', {
            'type': 'doc',
            'peer_id': peer_id
        })
        
        upload_url = upload_data['upload_url']
        print(f"📤 URL для загрузки получен")
        
        # Отправляем файл
        files = {'file': (filename, file_stream.getvalue())}
        response = requests.post(upload_url, files=files, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки файла: {response.status_code}")
            return False
            
        result = response.json()
        print(f"📤 Файл загружен на сервер")
        
        # Сохраняем документ
        doc_data = vk_session.method('docs.save', {
            'file': result['file']
        })
        
        if not doc_data:
            print("❌ Ошибка сохранения документа")
            return False
            
        doc = doc_data[0]
        attachment = f"doc{doc['owner_id']}_{doc['id']}"
        print(f"📤 Документ сохранен: {attachment}")
        
        # Отправляем сообщение с документом
        send_result = vk_session.method('messages.send', {
            'peer_id': peer_id,
            'attachment': attachment,
            'message': message,
            'random_id': get_random_id()
        })
        
        print(f"✅ Документ успешно отправлен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки документа: {e}")
        return False

# Инициализируем БД
init_db()

# Подключаемся к VK
try:
    print("🔄 Подключаюсь к VK API...")
    vk_session = vk_api.VkApi(token=CONFIG['token'])
    vk = vk_session.get_api()
    
    group_info = vk.groups.getById(group_id=CONFIG['group_id'])
    print(f"✅ Успешно подключен к группе: {group_info[0]['name']}")
    
    longpoll = VkBotLongPoll(vk_session, CONFIG['group_id'])
    print("✅ LongPoll запущен")
    
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    exit()

print("🎯 Бот запущен и готов к работе!")

# Главный цикл обработки событий
for event in longpoll.listen():
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.object.message['text'].strip().lower()
            user_id = event.object.message['from_id']
            peer_id = event.object.message['peer_id']
            original_text = event.object.message['text']
            
            print(f"📩 Получено: '{msg}' от {user_id}")
            
            if event.from_chat and CONFIG['chat_id'] is None:
                CONFIG['chat_id'] = peer_id
                print(f"💬 Беседа сохранена: {peer_id}")
            
            if event.from_chat:
                # Регистрация студента
                if msg.startswith('я '):
                    parts = original_text[2:].strip().split()
                    if parts and parts[0].isdigit():
                        student_number = parts[0]
                        success, message = register_student(user_id, student_number)
                        send_message(peer_id, message)
                    else:
                        send_message(peer_id, "❌ Неверный формат! Используйте: Я [ваш номер]")
                
                # Доклады
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
                
                elif msg.startswith('беру доклад '):
                    try:
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
                
                # === РЕФЕРАТЫ ===
                elif msg.startswith('реферат '):
                    topic = original_text[8:].strip()
                    if not topic:
                        send_message(peer_id, "❌ Укажите тему реферата после команды 'реферат'")
                    elif len(topic) < 3:
                        send_message(peer_id, "❌ Тема реферата должна содержать минимум 3 символа")
                    else:
                        send_message(peer_id, f"📚 Начинаю создание реферата на тему: '{topic}'\n⏳ Это займет 10-20 секунд...")
                        
                        # Генерируем реферат
                        doc_file, message = referat_generator.generate_referat(topic)
                        
                        if doc_file:
                            print(f"✅ Реферат сгенерирован, размер: {len(doc_file.getvalue())} байт")
                            filename = f"Реферат_{topic.replace(' ', '_')[:30]}.docx"
                            
                            if send_document(peer_id, doc_file, filename, message):
                                print(f"✅ Реферат '{topic}' успешно отправлен")
                            else:
                                send_message(peer_id, "❌ Ошибка отправки документа. Попробуйте позже.")
                        else:
                            send_message(peer_id, message)
                
                elif msg == 'реферат помощь':
                    help_text = """
📚 Создание рефератов:

Команда: реферат [тема]
Пример: реферат Искусственный интеллект

⚡ Возможности:
• Автоматический поиск в Wikipedia
• Профессиональное оформление
• Титульная страница и содержание
• 2 структурированные главы
• Введение с целями и задачами
• Заключение с выводами
• Список источников

📝 Особенности:
• Объем: 5-8 страниц
• Готовый Word документ
• Автоматическая структура

⏱ Время создания: 10-20 секунд

💡 Рекомендации:
• Используйте конкретные темы
• Проверяйте и дополняйте материал
                    """
                    send_message(peer_id, help_text)
                
                elif msg == 'реферат примеры':
                    examples = """
📋 Примеры тем для рефератов:

🔬 Естественные науки:
• Квантовая физика
• Генная инженерия
• Изменение климата

💻 Технические науки:
• Искусственный интеллект
• Кибербезопасность
• Нанотехнологии

🌍 Гуманитарные науки:
• Древний Рим
• Эпоха Возрождения
• Мировые религии

💼 Экономика:
• Криптовалюты
• Цифровая экономика
• Глобализация

🎯 Используйте: реферат [тема]
                    """
                    send_message(peer_id, examples)
                
                # Команды администраторов
                elif is_admin(user_id):
                    if msg.startswith('!создать предмет '):
                        subject_name = original_text[16:].strip()
                        if subject_name:
                            success, message = create_subject(subject_name, user_id)
                            send_message(peer_id, message)
                        else:
                            send_message(peer_id, "❌ Укажите название предмета")
                    
                    elif msg.startswith('!добавить доклад '):
                        try:
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
                    
                    elif msg.startswith('!добавить админа '):
                        try:
                            new_admin_id = int(original_text[17:].strip())
                            success, message = add_admin(new_admin_id, user_id)
                            send_message(peer_id, message)
                        except ValueError:
                            send_message(peer_id, "❌ Неверный ID пользователя")
                
                # Расписание
                elif msg in ['расписание', 'сегодня']:
                    schedule, last_updated = load_schedule()
                    response = format_schedule_day(schedule, 0)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                
                elif msg == 'завтра':
                    schedule, last_updated = load_schedule()
                    response = format_schedule_day(schedule, 1)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                
                elif msg == 'неделя':
                    schedule, last_updated = load_schedule()
                    response = format_schedule_week(schedule, 0)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                
                elif msg == 'след неделя':
                    next_week = (CONFIG['current_week'] % 4) + 1
                    schedule, last_updated = load_schedule(next_week)
                    response = f"📅 Следующая неделя\n\n" + format_schedule_week(schedule, 1)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                
                elif msg == 'помощь':
                    help_text = """
📋 Доступные команды:

📅 Расписание:
• "расписание" или "сегодня" - на сегодня
• "завтра" - на завтра  
• "неделя" - на всю неделю
• "след неделя" - на следующую неделю

📚 Доклады:
• "я [номер]" - регистрация (пример: "я 1")
• "доклады" - список предметов
• "мои доклады" - мои взятые доклады
• "доклады по [предмет]" - доклады по предмету
• "беру доклад [номер] по [предмет]" - взять доклад

📖 Рефераты:
• "реферат [тема]" - создать реферат
• "реферат помощь" - справка по рефератам
• "реферат примеры" - примеры тем

⚡ Прочее:
• "привет" - тест бота
• "помощь" - этот список
                    """
                    send_message(peer_id, help_text)
                
                elif msg == 'привет':
                    send_message(peer_id, '👋 Привет! Я бот-помощник для студентов. Напиши "помощь" для списка команд.')
                
                else:
                    send_message(peer_id, '❓ Не понимаю команду. Напиши "помощь" для списка команд.')
                
    except Exception as e:
        print(f"💥 Ошибка обработки сообщения: {e}")
