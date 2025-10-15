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
import random
import math

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

# === БИБЛИОТЕКА ЗНАНИЙ ===
class KnowledgeBase:
    def __init__(self):
        self.subjects = {
            'механика': {
                'формулы': {
                    'кинематика': [
                        'v = s/t (скорость)',
                        'a = (v - v₀)/t (ускорение)',
                        's = v₀t + at²/2 (путь)',
                        'v² = v₀² + 2as'
                    ],
                    'динамика': [
                        'F = ma (второй закон Ньютона)',
                        'F₁ = -F₂ (третий закон Ньютона)',
                        'F_тр = μN (сила трения)',
                        'P = mg (вес тела)'
                    ],
                    'энергия': [
                        'E_кин = mv²/2',
                        'E_пот = mgh',
                        'A = Fs cos α (работа)',
                        'N = A/t (мощность)'
                    ]
                },
                'константы': {
                    'g': 9.81,
                    'G': 6.67430e-11,
                    'π': 3.14159
                }
            },
            'математика': {
                'формулы': {
                    'алгебра': [
                        '(a + b)² = a² + 2ab + b²',
                        'a² - b² = (a - b)(a + b)',
                        'ax² + bx + c = 0',
                        'x = (-b ± √(b² - 4ac))/2a'
                    ],
                    'геометрия': [
                        'S_треуг = ½bh',
                        'S_круга = πr²',
                        'V_сферы = 4/3πr³',
                        'V_цилиндра = πr²h'
                    ],
                    'тригонометрия': [
                        'sin²α + cos²α = 1',
                        'sin(α ± β) = sinα cosβ ± cosα sinβ',
                        'cos(α ± β) = cosα cosβ ∓ sinα sinβ'
                    ]
                }
            },
            'физика': {
                'формулы': {
                    'электричество': [
                        'I = U/R (закон Ома)',
                        'P = UI (мощность)',
                        'Q = I²Rt (теплота)',
                        'F = kq₁q₂/r² (закон Кулона)'
                    ],
                    'оптика': [
                        'n = c/v (показатель преломления)',
                        '1/f = 1/d + 1/f (формула линзы)',
                        'λ = c/ν (длина волны)'
                    ]
                }
            }
        }
    
    def calculate_mechanics(self, task_type, params):
        """Вычисления по механике"""
        try:
            if task_type == 'скорость':
                if 's' in params and 't' in params:
                    return params['s'] / params['t']
            elif task_type == 'ускорение':
                if 'v' in params and 'v0' in params and 't' in params:
                    return (params['v'] - params['v0']) / params['t']
            elif task_type == 'сила':
                if 'm' in params and 'a' in params:
                    return params['m'] * params['a']
            elif task_type == 'энергия_кинетическая':
                if 'm' in params and 'v' in params:
                    return 0.5 * params['m'] * params['v']**2
            elif task_type == 'энергия_потенциальная':
                if 'm' in params and 'h' in params:
                    return params['m'] * 9.81 * params['h']
            return None
        except:
            return None
    
    def get_formulas(self, subject, topic):
        """Получить формулы по теме"""
        if subject in self.subjects and topic in self.subjects[subject]['формулы']:
            return self.subjects[subject]['формулы'][topic]
        return []

# === УЛУЧШЕННЫЙ ГЕНЕРАТОР РЕФЕРАТОВ И ДОКЛАДОВ ===
class AdvancedReferatGenerator:
    def __init__(self):
        self.wiki_wiki = wikipediaapi.Wikipedia(
            language='ru',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent="VKStudentBot/1.0"
        )
        self.knowledge_base = KnowledgeBase()
    
    def search_wikipedia(self, topic):
        """Поиск в Wikipedia"""
        try:
            page = self.wiki_wiki.page(topic)
            if page.exists():
                return {
                    'title': page.title,
                    'content': page.text[:5000],
                    'url': page.fullurl,
                    'exists': True
                }
            return {'exists': False}
        except Exception as e:
            logging.error(f"Ошибка Wikipedia: {e}")
            return {'exists': False}
    
    def generate_extended_content(self, topic, pages=5):
        """Генерация расширенного контента по количеству страниц"""
        # Базовый контент из Wikipedia
        wiki_data = self.search_wikipedia(topic)
        
        if pages <= 3:
            # Короткий доклад (3-5 страниц)
            chapters_count = 2
            subsections_per_chapter = 2
        elif pages <= 8:
            # Средний реферат (6-8 страниц)
            chapters_count = 3
            subsections_per_chapter = 3
        else:
            # Большая работа (9+ страниц)
            chapters_count = 4
            subsections_per_chapter = 4
        
        chapters = []
        
        for i in range(chapters_count):
            chapter = {
                'title': self._generate_chapter_title(topic, i),
                'subsections': []
            }
            
            for j in range(subsections_per_chapter):
                subsection = {
                    'title': self._generate_subsection_title(topic, i, j),
                    'content': self._generate_subsection_content(topic, i, j, wiki_data)
                }
                chapter['subsections'].append(subsection)
            
            chapters.append(chapter)
        
        return chapters
    
    def _generate_chapter_title(self, topic, chapter_num):
        """Генерация названия главы"""
        titles = [
            f"Теоретические аспекты изучения {topic}",
            f"Исторический контекст и развитие {topic}",
            f"Современные подходы к исследованию {topic}",
            f"Практическое применение {topic}",
            f"Методология исследования {topic}",
            f"Анализ ключевых концепций {topic}"
        ]
        return titles[chapter_num % len(titles)]
    
    def _generate_subsection_title(self, topic, chapter_num, subsection_num):
        """Генерация названия подраздела"""
        prefixes = [
            "Основные понятия и определения",
            "Исторические предпосылки", 
            "Современное состояние",
            "Ключевые характеристики",
            "Методы исследования",
            "Практические аспекты",
            "Теоретические основы",
            "Анализ подходов"
        ]
        return f"{subsection_num + 1}.{chapter_num + 1} {prefixes[(chapter_num + subsection_num) % len(prefixes)]}"
    
    def _generate_subsection_content(self, topic, chapter_num, subsection_num, wiki_data):
        """Генерация содержания подраздела"""
        base_content = ""
        if wiki_data.get('exists'):
            sentences = wiki_data['content'].split('. ')
            if sentences:
                base_content = '. '.join(sentences[:3]) + '. '
        
        templates = [
            f"Рассматриваемый аспект {topic} представляет значительный интерес для научного сообщества. {base_content}",
            f"Анализ данного направления исследования {topic} позволяет выявить ключевые закономерности. {base_content}",
            f"Изучение представленного раздела {topic} способствует пониманию основных принципов. {base_content}",
            f"Проведенный анализ аспектов {topic} демонстрирует их практическую значимость. {base_content}"
        ]
        
        return templates[(chapter_num + subsection_num) % len(templates)]
    
    def create_document_structure(self, topic, doc_type="реферат", pages=5):
        """Создание структуры документа"""
        
        chapters = self.generate_extended_content(topic, pages)
        
        if doc_type == "доклад":
            doc_title = f"Доклад на тему: '{topic}'"
            doc_subject = "Дисциплина: Специальный курс"
        else:
            doc_title = f"Реферат на тему: '{topic}'"
            doc_subject = "Дисциплина: Общий курс"
        
        structure = {
            'title': doc_title,
            'subject': doc_subject,
            'student_info': 'Выполнил(а): студент группы',
            'type': doc_type,
            'pages': pages,
            'introduction': self._generate_introduction(topic, doc_type, pages),
            'chapters': chapters,
            'conclusion': self._generate_conclusion(topic, doc_type),
            'sources': self._generate_sources(topic),
            'appendix': self._generate_appendix(topic)
        }
        
        return structure
    
    def _generate_introduction(self, topic, doc_type, pages):
        """Генерация введения"""
        return f"""Актуальность темы '{topic}' обусловлена ее значимостью в современной науке и практике. 

Цель данного {doc_type} - комплексный анализ и систематизация знаний по теме "{topic}".

Задачи исследования:
1. Изучить теоретические основы {topic.lower()}
2. Проанализировать ключевые аспекты и характеристики  
3. Рассмотреть практическое применение и перспективы развития
4. Сформулировать выводы и рекомендации

Объем работы: {pages} страниц
Методы исследования: анализ литературы, систематизация данных, сравнительный анализ"""
    
    def _generate_conclusion(self, topic, doc_type):
        """Генерация заключения"""
        return f"""В ходе выполнения {doc_type} на тему "{topic}" были решены поставленные задачи и достигнута цель исследования.

Основные выводы:
1. Тема '{topic}' обладает значительным потенциалом для дальнейшего изучения
2. Обнаружены перспективные направления для дополнительного исследования  
3. Практическая значимость работы заключается в систематизации знаний

Рекомендации:
- Продолжить углубленное изучение темы
- Рассмотреть возможность практического применения полученных знаний
- Разработать методические рекомендации по дальнейшему исследованию"""
    
    def _generate_sources(self, topic):
        """Генерация списка источников"""
        return [
            "Энциклопедические и справочные издания",
            "Научные статьи и периодические издания", 
            "Учебники и методические пособия",
            "Интернет-ресурсы и образовательные порталы",
            "Монографии и научные публикации",
            f"Wikipedia - {topic}"
        ]
    
    def _generate_appendix(self, topic):
        """Генерация приложения"""
        return f"""Приложение А
Дополнительные материалы по теме "{topic}"

Приложение может содержать:
- Таблицы и схемы
- Графики и диаграммы 
- Иллюстративный материал
- Расчеты и формулы
- Методические рекомендации

Приложение Б
Глоссарий основных терминов

Для углубленного изучения темы рекомендуется ознакомиться с дополнительной литературой."""
    
    def create_word_document(self, doc_structure):
        """Создание Word документа"""
        try:
            doc = Document()
            
            # Настройка стилей
            style = doc.styles['Normal']
            style.font.name = 'Times New Roman'
            style.font.size = Pt(14)
            
            # Титульная страница
            title = doc.add_heading(doc_structure['title'], 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_paragraph("\n" * 4)
            doc.add_paragraph(doc_structure['subject']).alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph("\n" * 3)
            doc.add_paragraph(doc_structure['student_info']).alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph("\n" * 3)
            date_para = doc.add_paragraph(f"Дата создания: {datetime.datetime.now().strftime('%d.%m.%Y')}")
            date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_page_break()
            
            # Содержание
            title = doc.add_heading('СОДЕРЖАНИЕ', level=1)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph()
            doc.add_paragraph("Введение")
            
            for i, chapter in enumerate(doc_structure['chapters']):
                doc.add_paragraph(f"Глава {i+1}. {chapter['title']}")
                for j, subsection in enumerate(chapter['subsections']):
                    doc.add_paragraph(f"   {subsection['title']}")
            
            doc.add_paragraph("Заключение")
            doc.add_paragraph("Список использованных источников")
            doc.add_paragraph("Приложение")
            
            doc.add_page_break()
            
            # Введение
            doc.add_heading('ВВЕДЕНИЕ', level=1)
            for paragraph in doc_structure['introduction'].split('\n\n'):
                if paragraph.strip():
                    p = doc.add_paragraph(paragraph)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Основные главы
            for i, chapter in enumerate(doc_structure['chapters']):
                doc.add_page_break()
                doc.add_heading(f'ГЛАВА {i+1}. {chapter["title"].upper()}', level=1)
                
                for subsection in chapter['subsections']:
                    doc.add_heading(subsection['title'], level=2)
                    p = doc.add_paragraph(subsection['content'])
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    doc.add_paragraph()
            
            # Заключение
            doc.add_page_break()
            doc.add_heading('ЗАКЛЮЧЕНИЕ', level=1)
            for paragraph in doc_structure['conclusion'].split('\n\n'):
                if paragraph.strip():
                    p = doc.add_paragraph(paragraph)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Источники
            doc.add_page_break()
            doc.add_heading('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', level=1)
            for source in doc_structure['sources']:
                p = doc.add_paragraph(source, style='List Bullet')
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Приложение
            doc.add_page_break()
            doc.add_heading('ПРИЛОЖЕНИЕ', level=1)
            p = doc.add_paragraph(doc_structure['appendix'])
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Сохраняем в байтовый поток
            file_stream = io.BytesIO()
            doc.save(file_stream)
            file_stream.seek(0)
            
            return file_stream
            
        except Exception as e:
            logging.error(f"Ошибка создания документа: {e}")
            return None
    
    def generate_document(self, topic, doc_type="реферат", pages=5):
        """Основная функция генерации документа"""
        try:
            logging.info(f"Начало генерации {doc_type}: {topic}, {pages} страниц")
            
            # Создаем структуру документа
            doc_structure = self.create_document_structure(topic, doc_type, pages)
            
            if not doc_structure:
                return None, f"❌ Не удалось сформировать структуру {doc_type}"
            
            # Создаем документ
            doc_file = self.create_word_document(doc_structure)
            
            if not doc_file:
                return None, f"❌ Ошибка при создании документа"
            
            success_message = f"""✅ {doc_type.capitalize()} на тему '{topic}' успешно создан!

📊 Параметры:
• Тип: {doc_type.capitalize()}
• Объем: {pages} страниц
• Глав: {len(doc_structure['chapters'])}
• Подразделов: {sum(len(ch['subsections']) for ch in doc_structure['chapters'])}

🎯 Особенности:
• Профессиональное оформление
• Детальная структура
• Полное содержание
• Список источников

💡 Рекомендации:
• Дополните материал примерами
• Проверьте уникальность
• Добавьте графики при необходимости"""
            
            return doc_file, success_message
            
        except Exception as e:
            logging.error(f"Ошибка генерации {doc_type}: {e}")
            return None, f"❌ Ошибка при создании {doc_type}"

# Создаем экземпляры
advanced_generator = AdvancedReferatGenerator()
knowledge_base = KnowledgeBase()

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
        print(f"📤 Файл загружен на сервер: {result}")
        
        # Сохраняем документ - ИСПРАВЛЕННАЯ ЧАСТЬ
        doc_data = vk_session.method('docs.save', {
            'file': result['file'],
            'title': filename,
            'tags': 'реферат'
        })
        
        print(f"📤 Ответ от docs.save: {doc_data}")
        
        if not doc_data:
            print("❌ Ошибка сохранения документа: пустой ответ")
            return False
            
        # ИСПРАВЛЕНИЕ: docs.save возвращает словарь с ключом 'doc', а не список
        if 'doc' in doc_data:
            doc = doc_data['doc']
            attachment = f"doc{doc['owner_id']}_{doc['id']}"
        elif 'type' in doc_data and doc_data['type'] == 'doc':
            doc = doc_data['doc']
            attachment = f"doc{doc['owner_id']}_{doc['id']}"
        else:
            print(f"❌ Неизвестный формат ответа: {doc_data}")
            return False
            
        print(f"📤 Документ сохранен: {attachment}")
        
        # Отправляем сообщение с документом
        send_result = vk_session.method('messages.send', {
            'peer_id': peer_id,
            'attachment': attachment,
            'message': message,
            'random_id': get_random_id()
        })
        
        print(f"✅ Документ успешно отправлен: {send_result}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки документа: {e}")
        import traceback
        traceback.print_exc()
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
                        doc_file, message = advanced_generator.generate_document(topic, "реферат", 5)
                        
                        if doc_file:
                            filename = f"Реферат_{topic.replace(' ', '_')[:20]}.docx"
                            if send_document(peer_id, doc_file, filename, message):
                                print(f"✅ Реферат '{topic}' отправлен")
                            else:
                                send_message(peer_id, "❌ Ошибка отправки документа")
                        else:
                            send_message(peer_id, message)
                
                # === НОВЫЕ КОМАНДЫ: МАССИВНЫЕ ДОКЛАДЫ ===
                elif msg.startswith('доклад '):
                    parts = original_text[7:].strip().split(' страниц')
                    if len(parts) == 2:
                        topic = parts[0].strip()
                        try:
                            pages = int(parts[1].strip())
                            if pages < 1 or pages > 20:
                                send_message(peer_id, "❌ Укажите от 1 до 20 страниц")
                            else:
                                send_message(peer_id, f"📚 Создаю доклад на тему: '{topic}'\n📄 Объем: {pages} страниц\n⏳ Это займет некоторое время...")
                                doc_file, message = advanced_generator.generate_document(topic, "доклад", pages)
                                if doc_file:
                                    filename = f"Доклад_{topic.replace(' ', '_')[:20]}_{pages}стр.docx"
                                    if send_document(peer_id, doc_file, filename, message):
                                        print(f"✅ Доклад '{topic}' отправлен")
                                    else:
                                        send_message(peer_id, "❌ Ошибка отправки документа")
                                else:
                                    send_message(peer_id, message)
                        except ValueError:
                            send_message(peer_id, "❌ Укажите количество страниц числом")
                    else:
                        send_message(peer_id, "❌ Формат: доклад [тема] страниц [число]")
                
                # === РАСЧЕТЫ ПО МЕХАНИКЕ ===
                elif msg.startswith('рассчитать '):
                    parts = original_text[11:].strip().split()
                    if len(parts) >= 2:
                        subject = parts[0].lower()
                        task = ' '.join(parts[1:])
                        
                        if subject == 'механика':
                            # Парсим параметры из задачи
                            params = {}
                            if 'масс' in task:
                                masses = re.findall(r'масс[аыу]? (\d+)', task)
                                if masses:
                                    params['m'] = float(masses[0])
                            if 'скорост' in task:
                                speeds = re.findall(r'скорост[ьи]? (\d+)', task)
                                if speeds:
                                    params['v'] = float(speeds[0])
                            if 'время' in task:
                                times = re.findall(r'врем[яени]? (\d+)', task)
                                if times:
                                    params['t'] = float(times[0])
                            if 'высот' in task:
                                heights = re.findall(r'высот[аыу]? (\d+)', task)
                                if heights:
                                    params['h'] = float(heights[0])
                            
                            # Выполняем расчет
                            if 'ускорен' in task:
                                result = knowledge_base.calculate_mechanics('ускорение', params)
                                if result:
                                    send_message(peer_id, f"📐 Результат расчета:\nУскорение = {result:.2f} м/с²")
                                else:
                                    send_message(peer_id, "❌ Недостаточно данных для расчета ускорения")
                            elif 'сил' in task:
                                result = knowledge_base.calculate_mechanics('сила', params)
                                if result:
                                    send_message(peer_id, f"📐 Результат расчета:\nСила = {result:.2f} Н")
                                else:
                                    send_message(peer_id, "❌ Недостаточно данных для расчета силы")
                            elif 'энерги' in task and 'кинетич' in task:
                                result = knowledge_base.calculate_mechanics('энергия_кинетическая', params)
                                if result:
                                    send_message(peer_id, f"📐 Результат расчета:\nКинетическая энергия = {result:.2f} Дж")
                                else:
                                    send_message(peer_id, "❌ Недостаточно данных для расчета энергии")
                            elif 'энерги' in task and 'потенциал' in task:
                                result = knowledge_base.calculate_mechanics('энергия_потенциальная', params)
                                if result:
                                    send_message(peer_id, f"📐 Результат расчета:\nПотенциальная энергия = {result:.2f} Дж")
                                else:
                                    send_message(peer_id, "❌ Недостаточно данных для расчета энергии")
                            else:
                                send_message(peer_id, "❌ Укажите что рассчитать: ускорение, сила, энергия_кинетическая, энергия_потенциальная")
                        else:
                            send_message(peer_id, "❌ Доступные предметы: механика")
                    else:
                        send_message(peer_id, "❌ Формат: рассчитать [предмет] [задача]")
                
                # === ФОРМУЛЫ ===
                elif msg.startswith('формулы '):
                    subject = original_text[8:].strip().lower()
                    if subject in knowledge_base.subjects:
                        response = f"📚 Формулы по {subject}:\n\n"
                        for topic, formulas in knowledge_base.subjects[subject]['формулы'].items():
                            response += f"📖 {topic.capitalize()}:\n"
                            for formula in formulas[:3]:  # Показываем первые 3 формулы
                                response += f"• {formula}\n"
                            response += "\n"
                        send_message(peer_id, response)
                    else:
                        send_message(peer_id, "❌ Доступные предметы: " + ", ".join(knowledge_base.subjects.keys()))
                
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
                
                elif msg == 'доклад помощь':
                    help_text = """
📄 Создание докладов:

Команда: доклад [тема] страниц [число]
Пример: доклад Квантовая физика страниц 10

⚡ Возможности:
• Автоматическое масштабирование объема
• Детальная структура с подразделами
• Профессиональное оформление
• Гибкая настройка количества страниц

📊 Диапазон объемов:
• 1-3 страницы: 2 главы, 2 подраздела
• 4-8 страниц: 3 главы, 3 подраздела  
• 9-20 страниц: 4 главы, 4 подраздела

💡 Рекомендации:
• Для курсовых: 10-15 страниц
• Для семинаров: 5-8 страниц
• Для выступлений: 3-5 страниц
                    """
                    send_message(peer_id, help_text)
                
                elif msg == 'расчеты помощь':
                    help_text = """
📐 Математические расчеты:

Команда: рассчитать [предмет] [задача]
Пример: рассчитать механика масса 10 ускорение 2

📚 Доступные предметы:
• механика - расчеты по физике

🔧 Примеры задач:
• рассчитать механика масса 5 скорость 20 энергия_кинетическая
• рассчитать механика масса 10 высота 5 энергия_потенциальная
• рассчитать механика масса 2 ускорение 3 сила

📖 Формулы:
• формулы механика - показать все формулы
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
• "реферат [тема]" - создать реферат (5 страниц)
• "реферат помощь" - справка по рефератам
• "реферат примеры" - примеры тем

📄 Массивные доклады:
• "доклад [тема] страниц [число]" - доклад нужного объема
• "доклад помощь" - справка по докладам

📐 Расчеты:
• "рассчитать [предмет] [задача]" - математические расчеты
• "формулы [предмет]" - показать формулы
• "расчеты помощь" - справка по расчетам

⚡ Прочее:
• "привет" - тест бота
• "помощь" - этот список
                    """
                    send_message(peer_id, help_text)
                
                elif msg == 'привет':
                    send_message(peer_id, '👋 Привет! Я умный бот-помощник для студентов. Напиши "помощь" для списка команд.')
                
                else:
                    send_message(peer_id, '❓ Не понимаю команду. Напиши "помощь" для списка команд.')
                
    except Exception as e:
        print(f"💥 Ошибка обработки сообщения: {e}")

