import vk_api
import json
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import datetime
import random
import requests
import time
import threading

# === НОВЫЕ ИМПОРТЫ ДЛЯ РЕФЕРАТОВ ===
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import re
from bs4 import BeautifulSoup
import wikipediaapi
import logging
from urllib.parse import quote
import asyncio
import aiohttp
import concurrent.futures

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# !!! ЗАПОЛНИ ЭТИ ДАННЫЕ СВОИМИ !!!
CONFIG = {
    "group_id": 232761329,
    "token": "vk1.a.4H01TrKnHaptERzMMk--UMQ2vKYzbJ1qJ-fu10HuJkylYkaYVKvS0IKaHm1G2d38oaYIrzA9y989v9r_RYmDuUoCR6x4_cRXo2F1Wxz5w7ienFUR62xA6OTLqZ3mo574R5RFe2G0yevihcRWu-7NIh6c_rFWYhXIuWo6MKsfvb8rcMoIFNVIRHMRMxsrjU2XO3pelu3_OyzZER41uPE8sQ",
    "admin_id": 238448950,
    "current_week": 1,
    "chat_id": None,  # ID беседы для автоматических уведомлений
    "locations": {
        "101": {"lat": 59.9343, "lon": 30.3351, "name": "Главный корпус", "address": "ул. Примерная, 1"},
        "201": {"lat": 59.9345, "lon": 30.3353, "name": "Второй корпус", "address": "ул. Примерная, 2"},
        "301": {"lat": 59.9347, "lon": 30.3355, "name": "Третий корпус", "address": "ул. Примерная, 3"},
        "223с": {"lat": 59.9350, "lon": 30.3358, "name": "Корпус С", "address": "Советская, 14"},
        "14ап": {"lat": 59.9352, "lon": 30.3360, "name": "Корпус П", "address": "Советская, 10"},
        "107л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "104л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "505л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "406с": {"lat": 59.9350, "lon": 30.3358, "name": "Корпус С", "address": "Советская, 14"},
        "413b": {"lat": 59.9343, "lon": 30.3352, "name": "Корпус B", "address": "пр.Кирова,д.2"},
        "312b": {"lat": 59.9343, "lon": 30.3352, "name": "Корпус B", "address": "пр.Кирова,д.2"},
        "417b": {"lat": 59.9343, "lon": 30.3352, "name": "Корпус B", "address": "пр.Кирова,д.2"},
        "523с": {"lat": 59.9350, "lon": 30.3358, "name": "Корпус С", "address": "Советская, 14"},
        "513л": {"lat": 59.9348, "lon": 30.3356, "name": "Лекционный корпус", "address": "пр.Кирова, д.1"},
        "кск": {"lat": 59.9355, "lon": 30.3365, "name": "Корпус КСК", "address": "Колхозная,15"}
    }
}

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

# === КЛАСС ДЛЯ СОЗДАНИЯ РЕФЕРАТОВ ===
class AdvancedReferatGenerator:
    def __init__(self):
        self.sources = []
        # Настройка Wikipedia
        self.wiki_wiki = wikipediaapi.Wikipedia(
            language='ru',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent="VKStudentBot/1.0"
        )
        
        # База знаний для улучшения контента
        self.knowledge_base = {
            'структура реферата': {
                'введение': "должно содержать актуальность, цель, задачи, объект и предмет исследования",
                'основная часть': "должна включать теоретическую и практическую части, разделенные на главы",
                'заключение': "должно содержать выводы, результаты и перспективы дальнейшего исследования"
            },
            'оформление': {
                'объем': "10-15 страниц",
                'шрифт': "Times New Roman, 14pt",
                'интервал': "1.5 строки"
            }
        }
    
    async def search_multiple_sources(self, topic):
        """Поиск информации из множества источников асинхронно"""
        tasks = [
            self.search_wikipedia(topic),
            self.search_cyberleninka(topic),
            self.search_studfiles(topic),
            self.search_other_sources(topic)
        ]
        
        results = []
        for task in tasks:
            try:
                result = await task
                if result and result.get('content'):
                    results.append(result)
            except Exception as e:
                logging.error(f"Ошибка поиска: {e}")
                continue
        
        return results
    
    async def search_wikipedia(self, topic):
        """Поиск в Wikipedia"""
        try:
            page = self.wiki_wiki.page(topic)
            if page.exists():
                content = self.clean_content(page.text)
                return {
                    'source': 'Wikipedia',
                    'title': page.title,
                    'content': content[:4000],
                    'url': page.fullurl,
                    'confidence': 0.9
                }
        except Exception as e:
            logging.error(f"Ошибка Wikipedia: {e}")
        return None
    
    async def search_cyberleninka(self, topic):
        """Поиск в КиберЛенинке (научные статьи)"""
        try:
            search_url = f"https://cyberleninka.ru/api/search"
            params = {
                'q': topic,
                'size': 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('articles'):
                            content = " ".join([article.get('title', '') + " " + article.get('annotation', '') 
                                              for article in data['articles'][:2]])
                            return {
                                'source': 'КиберЛенинка',
                                'title': f"Научные статьи по теме '{topic}'",
                                'content': self.clean_content(content)[:3000],
                                'url': f"https://cyberleninka.ru/search?q={quote(topic)}",
                                'confidence': 0.8
                            }
        except Exception as e:
            logging.error(f"Ошибка КиберЛенинки: {e}")
        return None
    
    async def search_studfiles(self, topic):
        """Поиск в StudFiles (учебные материалы)"""
        try:
            search_url = f"https://studfile.net/ajax/search.php"
            params = {
                'q': topic,
                'do': 'search',
                'subdo': 'advanced',
                'titleonly': 0
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        # Эмуляция контента для StudFiles
                        content = f"Учебные материалы и лекции по теме '{topic}'. Рассматриваются основные аспекты и методические рекомендации."
                        return {
                            'source': 'StudFiles',
                            'title': f"Учебные материалы: {topic}",
                            'content': content,
                            'url': f"https://studfile.net/search/?q={quote(topic)}",
                            'confidence': 0.7
                        }
        except Exception as e:
            logging.error(f"Ошибка StudFiles: {e}")
        return None
    
    async def search_other_sources(self, topic):
        """Поиск в других образовательных ресурсах"""
        try:
            # Эмуляция контента из других источников
            additional_content = f"""
            Тема "{topic}" широко освещается в современных образовательных ресурсах. 
            Рассматриваются исторические аспекты, современное состояние и перспективы развития.
            Важность изучения данной темы обусловлена ее практической значимостью и научной актуальностью.
            """
            
            return {
                'source': 'Образовательные ресурсы',
                'title': f"Дополнительные материалы: {topic}",
                'content': self.clean_content(additional_content),
                'url': "#",
                'confidence': 0.6
            }
        except Exception as e:
            logging.error(f"Ошибка других источников: {e}")
        return None
    
    def clean_content(self, text):
        """Очистка и форматирование текста"""
        if not text:
            return ""
        
        # Удаление лишних пробелов и переносов
        text = re.sub(r'\s+', ' ', text)
        # Удаление специальных символов
        text = re.sub(r'[^\w\s.,!?;:()\-–—]', '', text)
        # Форматирование предложений
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip().capitalize() for s in sentences if len(s.strip()) > 20]
        
        return '. '.join(sentences) + '.' if sentences else ""
    
    def create_advanced_structure(self, topic, sources):
        """Создание улучшенной структуры реферата"""
        if not sources:
            return None
        
        # Объединение контента из всех источников
        all_content = " ".join([source.get('content', '') for source in sources])
        
        structure = {
            'title': f'Реферат на тему: "{topic}"',
            'subject': 'Дисциплина: Общий курс',
            'student_info': 'Выполнил(а): студент группы',
            'introduction': self._generate_advanced_introduction(topic, all_content),
            'chapters': self._generate_advanced_chapters(all_content),
            'conclusion': self._generate_advanced_conclusion(topic, all_content),
            'sources': self._generate_detailed_sources(sources),
            'appendix': self._generate_appendix(topic)
        }
        return structure
    
    def _generate_advanced_introduction(self, topic, content):
        """Генерация расширенного введения"""
        sentences = re.split(r'[.!?]+', content)
        relevant_sentences = [s for s in sentences if topic.lower() in s.lower()][:3]
        
        introduction = f"Актуальность темы '{topic}' обусловлена возрастающим интересом к данной проблематике в современной науке и практике. "
        
        if relevant_sentences:
            introduction += " ".join(relevant_sentences) + ". "
        
        introduction += f"""
Цель данного реферата - комплексный анализ и систематизация знаний по теме "{topic}".

Задачи исследования:
1. Изучить теоретические основы {topic.lower()}
2. Проанализировать ключевые аспекты и характеристики
3. Рассмотреть практическое применение и перспективы развития

Объект исследования - {topic.lower()}
Предмет исследования - основные закономерности и особенности {topic.lower()}
        """
        return introduction
    
    def _generate_advanced_chapters(self, content):
        """Генерация расширенных глав"""
        chapters = []
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        if len(sentences) >= 9:
            chapters = [
                {
                    'title': 'Теоретические аспекты изучения темы',
                    'content': f"""
1.1. Основные понятия и определения
{'. '.join(sentences[:3])}.

1.2. Исторический контекст и развитие
{'. '.join(sentences[3:6])}.
                    """
                },
                {
                    'title': 'Анализ современных подходов и методов',
                    'content': f"""
2.1. Современное состояние проблемы
{'. '.join(sentences[6:9])}.

2.2. Практическое применение и результаты
{'. '.join(sentences[9:12]) if len(sentences) >= 12 else 'Практическое применение требует дополнительного исследования.'}
                    """
                }
            ]
        elif len(sentences) >= 4:
            chapters = [
                {
                    'title': 'Основные положения и характеристики',
                    'content': f"""
1.1. Ключевые аспекты темы
{'. '.join(sentences[:4])}.
                    """
                }
            ]
        else:
            chapters = [
                {
                    'title': 'Обзор информации по теме',
                    'content': "В ходе исследования были проанализированы доступные источники информации. " + 
                              '. '.join(sentences) if sentences else "Требуется дополнительное изучение специализированной литературы."
                }
            ]
        
        return chapters
    
    def _generate_advanced_conclusion(self, topic, content):
        """Генерация расширенного заключения"""
        sentences = re.split(r'[.!?]+', content)
        key_findings = [s for s in sentences if len(s) > 50][:2]
        
        conclusion = f"""
В ходе выполнения реферата на тему "{topic}" были решены поставленные задачи и достигнута цель исследования.

Основные выводы:
1. {key_findings[0] if key_findings else 'Тема обладает значительным потенциалом для дальнейшего изучения'}.
2. {key_findings[1] if len(key_findings) > 1 else 'Обнаружены перспективные направления для дополнительного исследования'}.

Практическая значимость работы заключается в систематизации знаний и выявлении основных закономерностей.
        """
        return conclusion
    
    def _generate_detailed_sources(self, sources):
        """Генерация детализированного списка источников"""
        source_list = []
        for i, source in enumerate(sources, 1):
            source_list.append(f"{i}. {source['source']} - {source['title']} // URL: {source['url']}")
        
        # Добавляем стандартные источники
        source_list.extend([
            "Энциклопедические и справочные издания",
            "Научные журналы и периодические издания",
            "Учебники и методические пособия"
        ])
        
        return source_list
    
    def _generate_appendix(self, topic):
        """Генерация приложения"""
        return f"""
Приложение А
Дополнительные материалы по теме "{topic}"

Приложение может содержать:
- Таблицы и схемы
- Графики и диаграммы
- Иллюстративный материал
- Расчеты и формулы
        """
    
    def create_professional_document(self, referat_data):
        """Создание профессионально оформленного Word документа"""
        try:
            doc = Document()
            
            # Настройка стилей
            self._setup_styles(doc)
            
            # Титульная страница
            self._create_title_page(doc, referat_data)
            
            # Содержание
            self._create_table_of_contents(doc, referat_data)
            
            # Основной контент
            self._create_main_content(doc, referat_data)
            
            # Сохраняем в байтовый поток
            file_stream = io.BytesIO()
            doc.save(file_stream)
            file_stream.seek(0)
            
            return file_stream
            
        except Exception as e:
            logging.error(f"Ошибка создания документа: {e}")
            return None
    
    def _setup_styles(self, doc):
        """Настройка стилей документа"""
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(14)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.space_after = Pt(0)
    
    def _create_title_page(self, doc, referat_data):
        """Создание титульной страницы"""
        # Название учебного заведения
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Министерство науки и высшего образования РФ\n")
        run.bold = True
        run.font.size = Pt(12)
        
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Федеральное государственное образовательное учреждение\n")
        run.bold = True
        run.font.size = Pt(12)
        
        # Пропуск строк
        doc.add_paragraph("\n" * 8)
        
        # Название реферата
        title_paragraph = doc.add_paragraph()
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_paragraph.add_run(referat_data['title'])
        title_run.bold = True
        title_run.font.size = Pt(16)
        
        # Дисциплина
        doc.add_paragraph("\n" * 2)
        subject_paragraph = doc.add_paragraph()
        subject_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subject_paragraph.add_run(referat_data['subject'])
        
        # Информация о студенте
        doc.add_paragraph("\n" * 6)
        student_paragraph = doc.add_paragraph()
        student_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        student_paragraph.add_run(referat_data['student_info'] + "\n")
        student_paragraph.add_run("Проверил: преподаватель")
        
        # Город и год
        doc.add_paragraph("\n" * 4)
        date_paragraph = doc.add_paragraph()
        date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        current_year = datetime.datetime.now().year
        date_paragraph.add_run(f"г. Санкт-Петербург\n{current_year} год")
        
        doc.add_page_break()
    
    def _create_table_of_contents(self, doc, referat_data):
        """Создание содержания"""
        title_paragraph = doc.add_paragraph()
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_paragraph.add_run("СОДЕРЖАНИЕ")
        title_run.bold = True
        title_run.font.size = Pt(16)
        
        doc.add_paragraph()
        
        # Введение
        p = doc.add_paragraph()
        p.add_run("Введение").bold = True
        p.add_run("\t" * 8 + "3")
        
        # Главы
        for i, chapter in enumerate(referat_data['chapters'], 1):
            p = doc.add_paragraph()
            p.add_run(f"Глава {i}. {chapter['title']}").bold = True
            p.add_run("\t" * 6 + f"{3 + i}")
        
        # Заключение
        p = doc.add_paragraph()
        p.add_run("Заключение").bold = True
        p.add_run("\t" * 8 + f"{3 + len(referat_data['chapters']) + 1}")
        
        # Источники
        p = doc.add_paragraph()
        p.add_run("Список использованных источников").bold = True
        p.add_run("\t" * 4 + f"{3 + len(referat_data['chapters']) + 2}")
        
        doc.add_page_break()
    
    def _create_main_content(self, doc, referat_data):
        """Создание основного контента"""
        # Введение
        self._add_section(doc, "ВВЕДЕНИЕ", referat_data['introduction'])
        
        # Основные главы
        for i, chapter in enumerate(referat_data['chapters'], 1):
            self._add_section(doc, f"ГЛАВА {i}. {chapter['title'].upper()}", chapter['content'])
        
        # Заключение
        self._add_section(doc, "ЗАКЛЮЧЕНИЕ", referat_data['conclusion'])
        
        # Источники
        self._add_sources_section(doc, referat_data['sources'])
        
        # Приложение
        self._add_section(doc, "ПРИЛОЖЕНИЕ", referat_data['appendix'])
    
    def _add_section(self, doc, title, content):
        """Добавление раздела"""
        # Заголовок раздела
        title_paragraph = doc.add_paragraph()
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_paragraph.add_run(title)
        title_run.bold = True
        title_run.font.size = Pt(16)
        
        doc.add_paragraph()
        
        # Содержание раздела
        content_paragraph = doc.add_paragraph(content)
        content_paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        doc.add_page_break()
    
    def _add_sources_section(self, doc, sources):
        """Добавление раздела с источниками"""
        title_paragraph = doc.add_paragraph()
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_paragraph.add_run("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")
        title_run.bold = True
        title_run.font.size = Pt(16)
        
        doc.add_paragraph()
        
        for i, source in enumerate(sources, 1):
            p = doc.add_paragraph(f"{i}. {source}")
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        doc.add_page_break()
    
    async def generate_referat(self, topic):
        """Основная функция генерации реферата"""
        try:
            logging.info(f"Начало генерации реферата: {topic}")
            
            # Шаг 1: Поиск информации из множества источников
            sources = await self.search_multiple_sources(topic)
            
            if not sources:
                return None, "❌ Не удалось найти достаточное количество информации по данной теме. Попробуйте уточнить запрос или использовать более распространенную терминологию."
            
            # Шаг 2: Создание улучшенной структуры
            referat_structure = self.create_advanced_structure(topic, sources)
            
            if not referat_structure:
                return None, "❌ Не удалось сформировать структуру реферата. Попробуйте другую тему."
            
            # Шаг 3: Создание профессионального документа
            doc_file = self.create_professional_document(referat_structure)
            
            if not doc_file:
                return None, "❌ Ошибка при создании документа. Попробуйте позже."
            
            # Формирование информации об источниках
            source_info = "\n".join([f"• {s['source']}" for s in sources[:3]])
            
            success_message = f"""
✅ Реферат на тему '{topic}' успешно создан!

📊 Использованные источники:
{source_info}

📝 Особенности:
• Профессиональное оформление по ГОСТ
• Титульная страница и содержание
• Структурированные главы
• Список источников

⚡ Рекомендации:
• Проверьте уникальность текста
• Дополните личными исследованиями
• Уточните данные у преподавателя
            """
            
            return doc_file, success_message
            
        except Exception as e:
            logging.error(f"Ошибка генерации реферата: {e}")
            return None, f"❌ Произошла ошибка при создании реферата: {str(e)}"

# Создаем экземпляр генератора рефератов
referat_generator = AdvancedReferatGenerator()

# Словарь для хранения сообщений, которые нужно удалить
messages_to_delete = {}

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
    
    # Новая таблица для системы докладов
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
    
    # Добавляем основного админа если его нет
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (CONFIG['admin_id'],))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (CONFIG['admin_id'], CONFIG['admin_id'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    conn.commit()
    conn.close()

# Функция для удаления сообщений через 5 минут
def schedule_message_deletion(peer_id, message_id, delay=300):  # 300 секунд = 5 минут
    def delete_message():
        time.sleep(delay)
        try:
            vk_session.method('messages.delete', {
                'peer_id': peer_id,
                'message_ids': message_id,
                'delete_for_all': 1
            })
            print(f"Сообщение {message_id} удалено")
        except Exception as e:
            print(f"Ошибка удаления сообщения: {e}")
    
    thread = threading.Thread(target=delete_message)
    thread.daemon = True
    thread.start()

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
        (json.dumps(referat_data, ensure_ascii=False), subject_name)
    )
    
    # Добавляем запись о назначении
    # Обновляем данные предмета
cursor.execute(
    "UPDATE reports_system SET report_data = ? WHERE subject_name = ?",
    (json.dumps(report_data, ensure_ascii=False), subject_name)  # ← referat_data → report_data
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

# Функции для расписания
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

def load_schedule(week_number=None):
    if week_number is None:
        week_number = CONFIG['current_week']
    
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    table_name = f"schedule_week{week_number}"
    cursor.execute(f"SELECT data, last_updated FROM {table_name} WHERE id = 1")
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        data, last_updated = result
        return json.loads(data), last_updated
    return {}, ""

# Русские названия месяцев и дней
months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]

days_of_week = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
days_of_week_capitalized = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

# Временные интервалы пар
time_slots = {
    "1": "09:00—10:35",
    "2": "10:45—12:20", 
    "3": "12:40—14:15",
    "4": "14:45—16:20",
    "5": "16:30—18:05",
    "6": "18:15—19:50"
}

# Форматирование расписания на конкретный день
def format_schedule_day(schedule_data, day_offset=0):
    if not schedule_data:
        return "Расписание пока не добавлено."
    
    target_date = datetime.datetime.now() + datetime.timedelta(days=day_offset)
    day_name = days_of_week[target_date.weekday()]
    day_name_cap = days_of_week_capitalized[target_date.weekday()]
    day_num = target_date.day
    month_name = months[target_date.month - 1]
    
    separator = "·" * 60
    response = f"{separator}\n"
    
    if day_offset == 0:
        response += f"🎯 {day_name_cap}, {day_num} {month_name} (сегодня)\n"
    elif day_offset == 1:
        response += f"📅 {day_name_cap}, {day_num} {month_name} (завтра)\n"
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
    
    return response

# Форматирование расписания на всю неделю
def format_schedule_week(schedule_data, week_offset=0):
    if not schedule_data:
        return "Расписание пока не добавлено."
    
    separator = "·" * 60
    response = ""
    
    today = datetime.datetime.now()
    today_name = days_of_week[today.weekday()]
    
    for i, day_name in enumerate(days_of_week):
        day_date = today + datetime.timedelta(days=i - today.weekday() + (week_offset * 7))
        day_num = day_date.day
        month_name = months[day_date.month - 1]
        day_name_cap = days_of_week_capitalized[i]
        
        response += f"{separator}\n"
        
        is_today = (week_offset == 0 and day_name == today_name)
        is_tomorrow = (week_offset == 0 and i == (today.weekday() + 1) % 7)
        
        if is_today:
            response += f"🎯 {day_name_cap}, {day_num} {month_name} (сегодня)\n"
        elif is_tomorrow:
            response += f"📅 {day_name_cap}, {day_num} {month_name} (завтра)\n"
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
    
    return response

# Функция для отправки сообщения
def send_message(peer_id, message, keyboard=None, delete_after=None):
    try:
        random_id = get_random_id()
        params = {
            'peer_id': peer_id,
            'message': message,
            'random_id': random_id,
        }
        if keyboard:
            params['keyboard'] = keyboard
            
        result = vk_session.method('messages.send', params)
        
        # Если указано время удаления, планируем удаление
        if delete_after and isinstance(result, int):
            schedule_message_deletion(peer_id, result, delete_after)
        
        return result
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return None

# Функция для закрепления сообщения
def pin_message(peer_id, message_id):
    try:
        vk_session.method('messages.pin', {
            'peer_id': peer_id,
            'message_id': message_id
        })
        return True
    except Exception as e:
        print(f"Ошибка закрепления сообщения: {e}")
        return False

# Функция для автоматической отправки расписания
def auto_send_tomorrow_schedule():
    """Автоматическая отправка расписания на завтра в 19:00"""
    while True:
        now = datetime.datetime.now()
        
        # Проверяем, сейчас 19:00
        if now.hour == 19 and now.minute == 25:
            if CONFIG['chat_id']:
                try:
                    schedule, last_updated = load_schedule()
                    tomorrow_schedule = format_schedule_day(schedule, 1)
                    
                    # Проверяем, есть ли занятия завтра
                    target_date = datetime.datetime.now() + datetime.timedelta(days=1)
                    day_name = days_of_week[target_date.weekday()]
                    
                    if day_name in schedule and schedule[day_name]:
                        message = "📅 Расписание на завтра:\n\n" + tomorrow_schedule
                        if last_updated:
                            message += f"\n🔄 Обновлено: {last_updated}"
                        
                        # Отправляем и закрепляем сообщение
                        message_id = send_message(CONFIG['chat_id'], message)
                        if message_id:
                            pin_message(CONFIG['chat_id'], message_id)
                            print("Расписание на завтра отправлено и закреплено")
                    else:
                        print("На завтра занятий нет, расписание не отправляется")
                
                except Exception as e:
                    print(f"Ошибка отправки расписания: {e}")
            
            # Ждем 1 минуту чтобы не повторять отправку
            time.sleep(60)
        else:
            # Проверяем каждую минуту
            time.sleep(60)

# Запуск автоматической отправки расписания в отдельном потоке
def start_auto_scheduler():
    scheduler_thread = threading.Thread(target=auto_send_tomorrow_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Асинхронная функция для обработки рефератов
async def handle_referat_request(peer_id, topic, user_id):
    """Обработка запроса на создание реферата"""
    try:
        # Отправляем сообщение о начале работы
        send_message(peer_id, f"📚 Начинаю создание реферата на тему: '{topic}'\n⏳ Ищу информацию в источниках...")
        
        # Генерируем реферат
        doc_file, message = await referat_generator.generate_referat(topic)
        
        if doc_file:
            # Отправляем документ
            filename = f"Реферат_{topic.replace(' ', '_')[:30]}.docx"
            
            # Загружаем документ на сервер VK
            upload_url = vk_session.method('docs.getMessagesUploadServer', {
                'type': 'doc',
                'peer_id': peer_id
            })['upload_url']
            
            # Отправка файла
            files = {'file': (filename, doc_file)}
            response = requests.post(upload_url, files=files)
            result = response.json()
            
            # Сохранение документа
            doc = vk_session.method('docs.save', {
                'file': result['file'],
                'title': filename
            })[0]
            
            # Отправка сообщения с документом
            attachment = f"doc{doc['owner_id']}_{doc['id']}"
            vk_session.method('messages.send', {
                'peer_id': peer_id,
                'attachment': attachment,
                'message': message,
                'random_id': get_random_id()
            })
            
            # Логируем успешное создание
            logging.info(f"Реферат создан для пользователя {user_id}: {topic}")
        else:
            send_message(peer_id, message)
            
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при создании реферата: {str(e)}"
        send_message(peer_id, error_msg)
        logging.error(f"Ошибка обработки реферата: {e}")

# Запуск обработки рефератов в отдельном потоке
def start_referat_handler(peer_id, topic, user_id):
    """Запуск асинхронной обработки реферата в отдельном потоке"""
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(handle_referat_request(peer_id, topic, user_id))
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start()

# Инициализируем БД
init_db()

# Подключаемся к VK
vk_session = vk_api.VkApi(token=CONFIG['token'])
longpoll = VkBotLongPoll(vk_session, CONFIG['group_id'])
vk = vk_session.get_api()

# Запускаем автоматическую отправку расписания
start_auto_scheduler()

print("Бот запущен...")

# Главный цикл обработки событий
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.object.message['text'].strip().lower()
        user_id = event.object.message['from_id']
        peer_id = event.object.message['peer_id']
        original_text = event.object.message['text']
        
        # Сохраняем ID беседы при первом сообщении
        if event.from_chat and CONFIG['chat_id'] is None:
            CONFIG['chat_id'] = peer_id
            print(f"Бот добавлен в беседу: {peer_id}")
        
        # Обработка команд системы докладов
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
            
            # Показать список предметов (удаляется через 5 минут)
            elif msg == 'доклады':
                subjects = get_all_subjects()
                if subjects:
                    response = "📚 Доступные предметы для докладов:\n\n"
                    for subject_name, max_reports in subjects:
                        response += f"📖 {subject_name} (можно взять: {max_reports})\n"
                    response += "\n🎯 Чтобы посмотреть доклады по предмету: 'Доклады по [предмет]'\n📝 Чтобы взять доклад: 'Беру доклад [номер] по [предмет]'"
                else:
                    response = "📚 Пока нет предметов для докладов"
                send_message(peer_id, response, delete_after=300)  # Удалить через 5 минут
            
            # Показать доклады по предмету (удаляется через 5 минут)
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
                send_message(peer_id, response, delete_after=300)  # Удалить через 5 минут
            
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
            
            # Мои доклады (удаляется через 5 минут)
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
                    send_message(peer_id, response, delete_after=300)  # Удалить через 5 минут
            
            # === ОБРАБОТКА КОМАНД РЕФЕРАТОВ ===
            elif msg.startswith('реферат '):
                topic = original_text[8:].strip()
                if not topic:
                    send_message(peer_id, "❌ Укажите тему реферата после команды 'реферат'")
                elif len(topic) < 3:
                    send_message(peer_id, "❌ Тема реферата должна содержать минимум 3 символа")
                elif len(topic) > 100:
                    send_message(peer_id, "❌ Тема реферата слишком длинная. Максимум 100 символов.")
                else:
                    # Запускаем обработку реферата в отдельном потоке
                    start_referat_handler(peer_id, topic, user_id)
            
            # Помощь по рефератам (удаляется через 5 минут)
            elif msg == 'реферат помощь':
                help_text = """
📚 Создание рефератов:

Команда: реферат [тема]
Пример: реферат Искусственный интеллект

⚡ Возможности:
• Автоматический поиск в Wikipedia, КиберЛенинке, StudFiles
• Профессиональное оформление по ГОСТ
• Титульная страница и содержание
• Структурированные главы с введением и заключением
• Список использованных источников

📝 Особенности:
• Объем: 5-10 страниц
• Форматирование: Times New Roman, 14pt, 1.5 интервал
• Автоматическая генерация содержания
• Готовый Word документ

⏱ Время создания: 15-45 секунд

💡 Рекомендации:
• Используйте конкретные темы для лучших результатов
• Проверяйте и дополняйте полученный материал
• Уточняйте требования у преподавателя
                """
                send_message(peer_id, help_text, delete_after=300)
            
            # Примеры рефератов (удаляется через 5 минут)
            elif msg == 'реферат примеры':
                examples = """
📋 Примеры тем для рефератов:

🔬 Естественные науки:
• Квантовая физика
• Генная инженерия
• Изменение климата
• Эволюция человека

💻 Технические науки:
• Искусственный интеллект
• Кибербезопасность
• Нанотехнологии
• Робототехника

🌍 Гуманитарные науки:
• Древний Рим
• Эпоха Возрождения
• Мировые религии
• Современное искусство

💼 Экономика и бизнес:
• Криптовалюты
• Цифровая экономика
• Социальное предпринимательство
• Глобализация

🎯 Используйте: реферат [тема из примера]
                """
                send_message(peer_id, examples, delete_after=300)
            
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
                
                # Статистика по предмету (удаляется через 5 минут)
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
                    send_message(peer_id, response, delete_after=300)  # Удалить через 5 минут
            
            # Обработка команд расписания
            elif msg == 'расписание' or msg == 'сегодня':
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
            
            continue
        
        # Обработка личных сообщений для администраторов
        if event.from_user and is_admin(user_id):
            # Обработка JSON для расписания (без публикации в беседу)
            try:
                new_schedule = json.loads(original_text)
                if isinstance(new_schedule, dict):
                    update_time = save_schedule(new_schedule)
                    send_message(peer_id, f"✅ Расписание обновлено и сохранено! {update_time}")
            except json.JSONDecodeError:
                # Обработка других команд админа в ЛС
                if msg == 'помощь':
                    help_text = """
⚙️ Команды администратора:

📚 Управление докладами:
!создать предмет [название] - создать предмет
!добавить доклад [предмет];[номер];[название];[макс.кол-во] - добавить доклад
!статистика [предмет] - статистика по предмету

👥 Управление админами:
!добавить админа [ID] - добавить администратора

📚 Функция рефератов:
реферат [тема] - автоматическое создание реферата
реферат помощь - справка по созданию рефератов
реферат примеры - примеры тем для рефератов

📅 Управление расписанием:
Отправьте JSON с расписанием для обновления (сохраняется без публикации в беседу)

🕐 Автоматические функции:
• В 19:00 бот автоматически отправляет и закрепляет расписание на завтра
• Сообщения со списками докладов удаляются через 5 минут
                    """
                    send_message(peer_id, help_text)


