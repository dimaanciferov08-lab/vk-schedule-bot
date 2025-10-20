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
from sympy import symbols, solve, simplify, diff, integrate, sqrt
import sympy as sp

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 🔑 НАСТРОЙКИ
CONFIG = {
    "group_id": 232761329,
    "token": "vk1.a.Y2xBv4alWQ55rd1IxtkpKc48ibKqpQ1x0Wyc9Hv0z18elxu3JaSBfCi7F5sJ9H4eKy1jg3iqFOjQTkQyCIYdnf77mcezdC__MLiyRi9Xwfus_uLz7UWd9AR8VPQDr7uMEiD1NxadTzqUllP7p4uqWixuefYkm6ryhgMbFLPSo-hnXKyt0XQ4qvpfIG5kLWlJoH7Ivew1yhgiKmtDWhbHYw",
    "admin_id": 238448950,
    "current_week": 1,
    "allowed_chats": [2000000673],[2000000678],  # Список разрешенных бесед
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

# === УЛУЧШЕННЫЙ ГЕНЕРАТОР РЕФЕРАТОВ ===
class TosikReferatGenerator:
    def __init__(self):
        self.wiki_wiki = wikipediaapi.Wikipedia(
            language='ru',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent="TosikBot/1.0"
        )
    
    def search_wikipedia(self, topic):
        """Поиск в Wikipedia"""
        try:
            page = self.wiki_wiki.page(topic)
            if page.exists():
                return {
                    'title': page.title,
                    'content': page.text[:8000],  # Больше контента
                    'url': page.fullurl,
                    'exists': True
                }
            return {'exists': False}
        except Exception as e:
            logging.error(f"Ошибка Wikipedia: {e}")
            return {'exists': False}
    
    def generate_detailed_content(self, topic, pages=10):
        """Генерация детализированного контента"""
        wiki_data = self.search_wikipedia(topic)
        
        # Определяем структуру по количеству страниц
        if pages <= 5:
            chapters = 2
            sections_per_chapter = 2
        elif pages <= 10:
            chapters = 3
            sections_per_chapter = 3
        elif pages <= 15:
            chapters = 4
            sections_per_chapter = 4
        else:
            chapters = 5
            sections_per_chapter = 5
        
        content_structure = []
        
        for chapter_num in range(chapters):
            chapter = {
                'title': self._get_chapter_title(topic, chapter_num),
                'sections': []
            }
            
            for section_num in range(sections_per_chapter):
                section = {
                    'title': self._get_section_title(chapter_num, section_num),
                    'content': self._generate_section_content(topic, chapter_num, section_num, wiki_data)
                }
                chapter['sections'].append(section)
            
            content_structure.append(chapter)
        
        return content_structure
    
    def _get_chapter_title(self, topic, chapter_num):
        """Генерация названий глав"""
        titles = [
            f"Теоретические основы и методология изучения {topic}",
            f"Исторический контекст и этапы развития {topic}",
            f"Современные подходы и методологические аспекты {topic}",
            f"Практическое применение и актуальность {topic}",
            f"Перспективы развития и инновационные аспекты {topic}",
            f"Анализ ключевых концепций и парадигм {topic}"
        ]
        return titles[chapter_num % len(titles)]
    
    def _get_section_title(self, chapter_num, section_num):
        """Генерация названий разделов"""
        prefixes = [
            "Основные понятия и терминологический аппарат",
            "Исторические предпосылки и генезис", 
            "Методологическая база исследования",
            "Ключевые характеристики и параметры",
            "Анализ современных тенденций",
            "Практическая значимость и применение",
            "Теоретические основы и концепции",
            "Сравнительный анализ подходов",
            "Экспериментальные исследования",
            "Статистические данные и анализ"
        ]
        return f"{section_num + 1}.{chapter_num + 1} {prefixes[(chapter_num + section_num) % len(prefixes)]}"
    
    def _generate_section_content(self, topic, chapter_num, section_num, wiki_data):
        """Генерация содержания раздела"""
        base_content = ""
        if wiki_data.get('exists'):
            # Берем разные части текста для разных разделов
            sentences = wiki_data['content'].split('. ')
            start_idx = (chapter_num * 3 + section_num) * 2
            if start_idx < len(sentences):
                base_content = '. '.join(sentences[start_idx:start_idx + 4]) + '. '
        
        # Богатые шаблоны контента
        templates = [
            f"Рассматриваемый аспект исследования {topic} представляет собой комплексную научную проблему, требующую многоуровневого анализа. {base_content} Проведенный анализ позволяет выявить системные закономерности и установить причинно-следственные связи в рамках изучаемой проблематики.",
            f"Методологический подход к исследованию {topic} основывается на применении междисциплинарных методов анализа. {base_content} Системное рассмотрение вопроса демонстрирует высокую практическую значимость полученных результатов и их применимость в различных сферах деятельности.",
            f"Анализ исторической ретроспективы развития {topic} свидетельствует о наличии устойчивых тенденций и закономерностей. {base_content} Современное состояние исследований характеризуется интеграцией различных научных парадигм и методологических подходов.",
            f"Практическая реализация концепций {topic} предполагает учет множества факторов и условий. {base_content} Экспериментальные данные подтверждают эффективность предложенных методик и их соответствие современным требованиям.",
            f"Теоретическое осмысление проблематики {topic} базируется на фундаментальных научных принципах. {base_content} Проведенное исследование позволяет сформулировать ряд практических рекомендаций и определить перспективные направления дальнейшей работы."
        ]
        
        return templates[(chapter_num + section_num) % len(templates)]
    
    def create_referat_structure(self, topic, pages=10):
        """Создание структуры реферата"""
        content = self.generate_detailed_content(topic, pages)
        
        structure = {
            'title': f'РЕФЕРАТ\nпо дисциплине: Общий курс\nна тему: "{topic}"',
            'student_info': 'Выполнил: студент группы\nПроверил: преподаватель',
            'pages': pages,
            'introduction': self._generate_detailed_introduction(topic, pages),
            'chapters': content,
            'conclusion': self._generate_detailed_conclusion(topic),
            'sources': self._generate_detailed_sources(topic),
            'appendix': self._generate_detailed_appendix(topic)
        }
        
        return structure
    
    def _generate_detailed_introduction(self, topic, pages):
        """Генерация детализированного введения"""
        return f"""ВВЕДЕНИЕ

Актуальность темы исследования "{topic}" обусловлена возрастающей значимостью данной проблематики в современных условиях. Стремительное развитие науки и технологий определяет необходимость комплексного изучения представленной темы.

Цель исследования заключается в системном анализе и обобщении теоретических и практических аспектов {topic}.

Задачи исследования:
1. Проанализировать теоретические основы и методологические подходы к изучению {topic}
2. Исследовать исторические аспекты и современное состояние проблемы
3. Выявить ключевые тенденции и закономерности развития {topic}
4. Определить практическую значимость и перспективы применения полученных результатов
5. Сформулировать выводы и рекомендации по дальнейшему исследованию

Объем работы: {pages} страниц
Методы исследования: анализ научной литературы, системный подход, сравнительный анализ, синтез теоретического и практического материала

Структура работы обусловлена поставленными задачами и включает введение, {len(self.generate_detailed_content(topic, pages))} главы, заключение, список использованных источников и приложения."""
    
    def _generate_detailed_conclusion(self, topic):
        """Генерация детализированного заключения"""
        return f"""ЗАКЛЮЧЕНИЕ

Проведенное исследование по теме "{topic}" позволило достичь поставленной цели и решить все задачи работы. 

Основные выводы:
1. Установлены теоретические основы и методологические принципы изучения {topic}
2. Выявлены исторические закономерности и современные тенденции развития
3. Определена практическая значимость исследования для различных сфер деятельности
4. Обоснованы перспективные направления дальнейших исследований

Практическая значимость работы заключается в возможности применения полученных результатов в образовательном процессе, научной деятельности и практической реализации.

Перспективы дальнейшего исследования связаны с углубленным изучением отдельных аспектов {topic} и расширением методологической базы исследования."""
    
    def _generate_detailed_sources(self, topic):
        """Генерация детализированного списка источников"""
        return [
            "Научные монографии и специализированные издания",
            "Периодические научные издания и журналы", 
            "Учебники и учебные пособия",
            "Материалы научных конференций и симпозиумов",
            "Электронные образовательные ресурсы",
            "Нормативные документы и стандарты",
            "Статистические сборники и базы данных",
            f"Материалы энциклопедии Wikipedia - {topic}",
            "Зарубежные научные публикации",
            "Диссертационные исследования и авторефераты"
        ]
    
    def _generate_detailed_appendix(self, topic):
        """Генерация детализированного приложения"""
        return f"""ПРИЛОЖЕНИЯ

Приложение А
Таблицы и схемы по теме "{topic}"

Приложение Б
Графики и диаграммы исследования

Приложение В
Методические материалы и рекомендации

Приложение Г
Статистические данные и расчеты

Приложение Д
Иллюстративный материал и визуализация

Для углубленного изучения темы рекомендуется ознакомиться с дополнительными источниками и провести самостоятельное исследование."""
    
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
            
            doc.add_paragraph("\n" * 6)
            doc.add_paragraph(referat_data['student_info']).alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph("\n" * 4)
            
            current_year = datetime.datetime.now().year
            date_para = doc.add_paragraph(f"г. Санкт-Петербург\n{current_year} год")
            date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_page_break()
            
            # Содержание
            title = doc.add_heading('СОДЕРЖАНИЕ', level=1)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph()
            
            doc.add_paragraph("Введение")
            page_num = 3
            
            for i, chapter in enumerate(referat_data['chapters']):
                doc.add_paragraph(f"Глава {i+1}. {chapter['title']}")
                page_num += 1
                for j, section in enumerate(chapter['sections']):
                    doc.add_paragraph(f"   {section['title']}")
            
            doc.add_paragraph("Заключение")
            doc.add_paragraph("Список использованных источников")
            doc.add_paragraph("Приложения")
            
            doc.add_page_break()
            
            # Введение
            doc.add_heading('ВВЕДЕНИЕ', level=1)
            for paragraph in referat_data['introduction'].split('\n\n'):
                if paragraph.strip():
                    p = doc.add_paragraph(paragraph)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Основные главы
            for i, chapter in enumerate(referat_data['chapters']):
                doc.add_page_break()
                doc.add_heading(f'ГЛАВА {i+1}. {chapter["title"].upper()}', level=1)
                
                for section in chapter['sections']:
                    doc.add_heading(section['title'], level=2)
                    p = doc.add_paragraph(section['content'])
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    doc.add_paragraph()
            
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
            for i, source in enumerate(referat_data['sources'], 1):
                p = doc.add_paragraph(f"{i}. {source}")
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            # Приложение
            doc.add_page_break()
            doc.add_heading('ПРИЛОЖЕНИЯ', level=1)
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
    
    def generate_referat(self, topic, pages=10):
        """Основная функция генерации реферата"""
        try:
            logging.info(f"Тосик начинает создание реферата: {topic}, {pages} страниц")
            
            # Создаем структуру реферата
            referat_structure = self.create_referat_structure(topic, pages)
            
            if not referat_structure:
                return None, "❌ Не удалось сформировать структуру реферата"
            
            # Создаем документ
            doc_file = self.create_word_document(referat_structure)
            
            if not doc_file:
                return None, "❌ Ошибка при создании документа"
            
            success_message = f"""📚 Тосик создал реферат на тему: "{topic}"

📊 Параметры:
• Объем: {pages} страниц
• Глав: {len(referat_structure['chapters'])}
• Разделов: {sum(len(ch['sections']) for ch in referat_structure['chapters'])}

🎯 Особенности:
• Полноценная академическая работа
• Детальная структура с разделами
• Профессиональное оформление по ГОСТ
• Список источников
• Приложения

💡 Рекомендации:
• Дополните работу конкретными примерами
• Добавьте графики и таблицы
• Проверьте уникальность текста"""
            
            return doc_file, success_message
            
        except Exception as e:
            logging.error(f"Ошибка генерации реферата: {e}")
            return None, f"❌ Ошибка при создании реферата"

# Создаем улучшенный генератор
tosik_referat_generator = TosikReferatGenerator()

# === УМНЫЙ ПОМОЩНИК ТОСИК ===
class TosikAssistant:
    def __init__(self):
        self.x, self.y, self.z = symbols('x y z')
    
    def solve_math_problem(self, problem):
        """Решает математические задачи"""
        try:
            problem_lower = problem.lower()
            
            if any(word in problem_lower for word in ['уравнен', 'x²', 'x**2']):
                return self._solve_equation(problem)
            elif any(word in problem_lower for word in ['площад', 'объем', 'геометр']):
                return self._solve_geometry(problem)
            elif any(word in problem_lower for word in ['производн', 'дифференц']):
                return self._solve_derivative(problem)
            elif any(word in problem_lower for word in ['интеграл']):
                return self._solve_integral(problem)
            else:
                return "🤔 Напиши конкретную задачу: уравнение, площадь, производная, интеграл"
                
        except Exception as e:
            return f"❌ Ошибка решения: {str(e)}"
    
    def _solve_equation(self, problem):
        """Решает уравнения"""
        try:
            # Извлекаем коэффициенты
            nums = [float(x) for x in re.findall(r'([+-]?\d*\.?\d+)', problem.replace(' ', '')) if x]
            
            if len(nums) >= 3:
                a, b, c = nums[0], nums[1], nums[2]
                D = b**2 - 4*a*c
                
                result = f"📊 Решение уравнения: {a}x² + {b}x + {c} = 0\n"
                result += f"Дискриминант: D = {b}² - 4×{a}×{c} = {D}\n"
                
                if D < 0:
                    result += "❌ Действительных корней нет"
                elif D == 0:
                    x = -b / (2*a)
                    result += f"✅ Один корень: x = {x:.2f}"
                else:
                    x1 = (-b + math.sqrt(D)) / (2*a)
                    x2 = (-b - math.sqrt(D)) / (2*a)
                    result += f"✅ Два корня:\n"
                    result += f"x₁ = {x1:.2f}\n"
                    result += f"x₂ = {x2:.2f}"
                
                return result
                
        except:
            return "❌ Не удалось решить уравнение"
    
    def _solve_geometry(self, problem):
        """Решает геометрические задачи"""
        numbers = [float(x) for x in re.findall(r'(\d+\.?\d*)', problem)]
        
        if 'площад' in problem.lower() and 'круг' in problem.lower() and numbers:
            r = numbers[0]
            area = math.pi * r**2
            return f"📐 Площадь круга:\nS = πr² = 3.14 × {r}² = {area:.2f}"
        
        elif 'объем' in problem.lower() and 'сфер' in problem.lower() and numbers:
            r = numbers[0]
            volume = (4/3) * math.pi * r**3
            return f"📐 Объем сферы:\nV = 4/3πr³ = 4/3 × 3.14 × {r}³ = {volume:.2f}"
        
        return "🤔 Напиши конкретную геометрическую задачу"
    
    def _solve_derivative(self, problem):
        """Решает производные"""
        return """
📚 Производная функции:

Основные правила:
1. (xⁿ)' = n·xⁿ⁻¹
2. (sin x)' = cos x  
3. (cos x)' = -sin x
4. (eˣ)' = eˣ
5. (ln x)' = 1/x

Пример:
f(x) = 3x⁴ + 2x² - 5x + 1
f'(x) = 12x³ + 4x - 5
        """
    
    def _solve_integral(self, problem):
        """Решает интегралы"""
        return """
📚 Интеграл функции:

Основные правила:
1. ∫xⁿ dx = xⁿ⁺¹/(n+1) + C
2. ∫sin x dx = -cos x + C  
3. ∫cos x dx = sin x + C
4. ∫eˣ dx = eˣ + C
5. ∫1/x dx = ln|x| + C

Пример:
∫(4x³ - 2x + 1) dx = x⁴ - x² + x + C
        """
    
    def calculate_expression(self, expression):
        """Вычисляет математические выражения"""
        try:
            # Заменяем символы для Python
            expr_clean = expression.replace('^', '**').replace('×', '*').replace('÷', '/')
            result = eval(expr_clean)
            return f"🧮 Результат: {expression} = {result}"
        except:
            return "❌ Не удалось вычислить выражение"

# Создаем помощника Тосика
tosik_assistant = TosikAssistant()

# Функция для проверки разрешенных бесед
def is_allowed_chat(peer_id):
    """Проверяет, разрешена ли беседа"""
    return peer_id in CONFIG['allowed_chats']

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

# Функция для отправки документа
def send_document(peer_id, file_stream, filename, message=""):
    """Отправка документа пользователю"""
    try:
        print(f"📤 Тосик отправляет документ: {filename}")
        
        # Получаем URL для загрузки
        upload_data = vk_session.method('docs.getMessagesUploadServer', {
            'type': 'doc',
            'peer_id': peer_id
        })
        
        upload_url = upload_data['upload_url']
        
        # Отправляем файл
        files = {'file': (filename, file_stream.getvalue())}
        response = requests.post(upload_url, files=files, timeout=30)
        
        if response.status_code != 200:
            return False
            
        result = response.json()
        
        # Сохраняем документ
        doc_data = vk_session.method('docs.save', {
            'file': result['file'],
            'title': filename
        })
        
        # Получаем attachment
        if 'doc' in doc_data:
            doc = doc_data['doc']
            attachment = f"doc{doc['owner_id']}_{doc['id']}"
        else:
            return False
        
        # Отправляем сообщение с документом
        vk_session.method('messages.send', {
            'peer_id': peer_id,
            'attachment': attachment,
            'message': message,
            'random_id': get_random_id()
        })
        
        print(f"✅ Документ отправлен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки документа: {e}")
        return False

# === БАЗА ДАННЫХ ===
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

def register_student(user_id, student_number, student_name):
    """Регистрация студента"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO student_registry (user_id, student_number, student_name, registered_at) VALUES (?, ?, ?, ?)",
            (user_id, student_number, student_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        return False
    finally:
        conn.close()

def get_student_info(user_id):
    """Получение информации о студенте"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT student_number, student_name FROM student_registry WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result if result else None

def create_subject(subject_name, max_reports, created_by):
    """Создание предмета для докладов"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        initial_data = json.dumps({})
        cursor.execute(
            "INSERT INTO reports_system (subject_name, report_data, max_reports_per_student, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
            (subject_name, initial_data, max_reports, created_by, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def add_report_to_subject(subject_name, report_number, report_title):
    """Добавление доклада к предмету"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT report_data FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    report_data = json.loads(result[0])
    report_data[str(report_number)] = {
        "title": report_title,
        "taken_by": None
    }
    
    cursor.execute(
        "UPDATE reports_system SET report_data = ? WHERE subject_name = ?",
        (json.dumps(report_data), subject_name)
    )
    conn.commit()
    conn.close()
    return True

def take_report_for_student(user_id, subject_name, report_number):
    """Взятие доклада студентом"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Проверяем, не взял ли уже студент максимальное количество докладов
    cursor.execute(
        "SELECT COUNT(*) FROM report_assignments WHERE user_id = ? AND subject_name = ?",
        (user_id, subject_name)
    )
    taken_count = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT max_reports_per_student FROM reports_system WHERE subject_name = ?",
        (subject_name,)
    )
    max_reports = cursor.fetchone()
    
    if not max_reports:
        conn.close()
        return "❌ Предмет не найден"
    
    max_reports = max_reports[0]
    
    if taken_count >= max_reports:
        conn.close()
        return f"❌ Вы уже взяли максимальное количество докладов ({max_reports}) по этому предмету"
    
    # Проверяем, свободен ли доклад
    cursor.execute("SELECT report_data FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return "❌ Предмет не найден"
    
    report_data = json.loads(result[0])
    
    if str(report_number) not in report_data:
        conn.close()
        return "❌ Доклад с таким номером не найден"
    
    if report_data[str(report_number)]["taken_by"] is not None:
        conn.close()
        return "❌ Этот доклад уже занят"
    
    # Занимаем доклад
    report_data[str(report_number)]["taken_by"] = user_id
    
    # Получаем информацию о студенте
    student_info = get_student_info(user_id)
    if not student_info:
        conn.close()
        return "❌ Сначала зарегистрируйтесь как студент"
    
    student_number, student_name = student_info
    
    # Обновляем данные и добавляем запись о назначении
    cursor.execute(
        "UPDATE reports_system SET report_data = ? WHERE subject_name = ?",
        (json.dumps(report_data), subject_name)
    )
    
    cursor.execute(
        "INSERT INTO report_assignments (user_id, subject_name, report_number, report_title, assigned_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, subject_name, report_number, report_data[str(report_number)]["title"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    conn.commit()
    conn.close()
    
    return f"✅ Доклад '{report_data[str(report_number)]['title']}' успешно взят!"

def get_subject_reports(subject_name):
    """Получение списка докладов по предмету"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT report_data FROM reports_system WHERE subject_name = ?", (subject_name,))
    result = cursor.fetchone()
    conn.close()
    
    return json.loads(result[0]) if result else None

def get_student_reports(user_id):
    """Получение докладов студента"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT subject_name, report_number, report_title, assigned_at FROM report_assignments WHERE user_id = ? ORDER BY assigned_at",
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
    """Проверка, является ли пользователь админом"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() is not None
    conn.close()
    
    return result

def add_admin(user_id, added_by):
    """Добавление администратора"""
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (user_id, added_by, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def save_schedule(week_data, week_number=None):
    """Сохранение расписания"""
    if week_number is None:
        week_number = CONFIG['current_week']
    
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(
        f"UPDATE schedule_week{week_number} SET data = ?, last_updated = ? WHERE id = 1",
        (json.dumps(week_data), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def load_schedule(week_number=None):
    """Загрузка расписания"""
    if week_number is None:
        week_number = CONFIG['current_week']
    
    conn = sqlite3.connect('schedule.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT data, last_updated FROM schedule_week{week_number} WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return json.loads(result[0]), result[1]
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

# Инициализируем базу данных
init_db()

print("🎯 Бот Тосик запущен и готов к работе!")
print(f"📞 Разрешенные беседы: {CONFIG['allowed_chats']}")

# Главный цикл обработки событий
for event in longpoll.listen():
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.object.message['text'].strip().lower()
            user_id = event.object.message['from_id']
            peer_id = event.object.message['peer_id']
            original_text = event.object.message['text']
            
            print(f"📩 Получено: '{msg}' от {user_id} в {peer_id}")
            
            # Проверяем разрешена ли беседа
            if not is_allowed_chat(peer_id):
                print(f"🚫 Беседа {peer_id} не в списке разрешенных")
                continue
            
            if event.from_chat and CONFIG['chat_id'] is None:
                CONFIG['chat_id'] = peer_id
                print(f"💬 Беседа сохранена: {peer_id}")
            
            if event.from_chat:
                # ========== ОСНОВНЫЕ КОМАНДЫ (работают всегда) ==========
                
                # Расписание
                if msg in ['расписание', 'сегодня']:
                    schedule, last_updated = load_schedule()
                    response = format_schedule_day(schedule, 0)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                    continue
                
                elif msg == 'завтра':
                    schedule, last_updated = load_schedule()
                    response = format_schedule_day(schedule, 1)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                    continue
                
                elif msg == 'неделя':
                    schedule, last_updated = load_schedule()
                    response = format_schedule_week(schedule, 0)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                    continue
                
                elif msg == 'след неделя':
                    next_week = (CONFIG['current_week'] % 4) + 1
                    schedule, last_updated = load_schedule(next_week)
                    response = f"📅 Следующая неделя\n\n" + format_schedule_week(schedule, 1)
                    if last_updated:
                        response += f"\n🔄 Обновлено: {last_updated}"
                    send_message(peer_id, response)
                    continue
                
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
                    continue
                
                elif msg.startswith('доклады по '):
                    subject_name = original_text[11:].strip()
                    reports = get_subject_reports(subject_name)
                    
                    if reports:
                        response = f"📋 Доклады по предмету '{subject_name}':\n\n"
                        free_count = 0
                        
                        for report_num, report_info in sorted(reports.items(), key=lambda x: int(x[0])):
                            status = "✅ Свободен" if not report_info["taken_by"] else f"❌ Занят ({GROUP_LIST.get(str(report_info['taken_by']), 'Неизвестный')})"
                            if not report_info["taken_by"]:
                                free_count += 1
                            
                            response += f"📄 {report_num}. {report_info['title']} - {status}\n"
                        
                        response += f"\n🎯 Свободно: {free_count}/{len(reports)}"
                        response += f"\n📝 Взять: 'Беру доклад [номер] по {subject_name}'"
                    else:
                        response = f"❌ Нет докладов по предмету '{subject_name}' или предмет не найден"
                    send_message(peer_id, response)
                    continue
                
                elif msg.startswith('беру доклад '):
                    # Парсим команду "Беру доклад X по Y"
                    parts = original_text.split()
                    if len(parts) >= 5 and parts[2].isdigit() and parts[3] == 'по':
                        report_number = int(parts[2])
                        subject_name = ' '.join(parts[4:])
                        
                        # Проверяем регистрацию
                        student_info = get_student_info(user_id)
                        if not student_info:
                            send_message(peer_id, "❌ Сначала зарегистрируйтесь: 'Регистрация X' где X - ваш номер в списке группы")
                            continue
                        
                        result = take_report_for_student(user_id, subject_name, report_number)
                        send_message(peer_id, result)
                    else:
                        send_message(peer_id, "❌ Формат: 'Беру доклад X по [название предмета]'")
                    continue
                
                elif msg == 'мои доклады':
                    student_info = get_student_info(user_id)
                    if not student_info:
                        send_message(peer_id, "❌ Сначала зарегистрируйтесь: 'Регистрация X' где X - ваш номер в списке группы")
                        continue
                    
                    reports = get_student_reports(user_id)
                    if reports:
                        response = "📋 Ваши доклады:\n\n"
                        for subject, number, title, date in reports:
                            response += f"📖 {subject} - Доклад {number}: {title}\n"
                            response += f"   📅 Взят: {date}\n\n"
                    else:
                        response = "📭 У вас пока нет взятых докладов"
                    send_message(peer_id, response)
                    continue
                
                # Регистрация
                elif msg.startswith('регистрация '):
                    parts = original_text.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        student_number = parts[1]
                        student_name = GROUP_LIST.get(student_number)
                        
                        if student_name:
                            if register_student(user_id, student_number, student_name):
                                send_message(peer_id, f"✅ {student_name} успешно зарегистрирован под номером {student_number}!")
                            else:
                                send_message(peer_id, "❌ Ошибка регистрации")
                        else:
                            send_message(peer_id, f"❌ Студент с номером {student_number} не найден в списке группы")
                    else:
                        send_message(peer_id, "❌ Формат: 'Регистрация X' где X - ваш номер в списке группы")
                    continue
                
                # Помощь
                elif msg in ['помощь', 'команды', 'help']:
                    help_text = """
🎯 ДОСТУПНЫЕ КОМАНДЫ:

📅 РАСПИСАНИЕ:
• "Расписание" или "Сегодня" - расписание на сегодня
• "Завтра" - расписание на завтра  
• "Неделя" - расписание на неделю
• "След неделя" - расписание на след. неделю

📚 ДОКЛАДЫ:
• "Доклады" - список предметов
• "Доклады по [предмет]" - доклады по предмету
• "Беру доклад X по [предмет]" - взять доклад
• "Мои доклады" - ваши доклады
• "Регистрация X" - регистрация (X - ваш номер)

🎓 РЕФЕРАТЫ:
• "Реферат [тема]" - реферат на 10 страниц
• "Реферат [тема] [N] стр" - реферат на N страниц

🧮 МАТЕМАТИКА:
• "Реши [уравнение]" - решить уравнение
• "Посчитай [выражение]" - вычислить

⚙️ АДМИН-КОМАНДЫ:
• "Добавить предмет [название] [макс]" - новый предмет
• "Добавить доклад [предмет] [номер] [название]" - новый доклад
• "Добавить админа [ID]" - добавить администратора

💡 Просто напишите вопрос или задачу - Тосик постарается помочь!
                    """
                    send_message(peer_id, help_text)
                    continue
                
                # Рефераты
                elif msg.startswith('реферат '):
                    parts = original_text[8:].strip().split()
                    if len(parts) >= 1:
                        # Определяем тему и количество страниц
                        if len(parts) >= 3 and parts[-2] in ['стр', 'страниц', 'страницы'] and parts[-1].isdigit():
                            pages = int(parts[-1])
                            topic = ' '.join(parts[:-2])
                        else:
                            pages = 10
                            topic = ' '.join(parts)
                        
                        if len(topic) < 3:
                            send_message(peer_id, "❌ Укажите тему реферата (минимум 3 символа)")
                            continue
                        
                        # Отправляем сообщение о начале генерации
                        send_message(peer_id, f"📚 Тосик начинает создание реферата на тему: '{topic}'\n⏳ Это займет некоторое время...")
                        
                        # Генерируем реферат
                        doc_file, message = tosik_referat_generator.generate_referat(topic, pages)
                        
                        if doc_file:
                            filename = f"Реферат_{topic.replace(' ', '_')}.docx"
                            if send_document(peer_id, doc_file, filename, message):
                                print(f"✅ Реферат '{topic}' успешно отправлен")
                            else:
                                send_message(peer_id, "❌ Ошибка отправки документа")
                        else:
                            send_message(peer_id, message)
                    else:
                        send_message(peer_id, "❌ Формат: 'Реферат [тема]' или 'Реферат [тема] [N] стр'")
                    continue
                
                # Математика
                elif msg.startswith('реши '):
                    problem = original_text[5:].strip()
                    if problem:
                        result = tosik_assistant.solve_math_problem(problem)
                        send_message(peer_id, result)
                    else:
                        send_message(peer_id, "❌ Укажите задачу для решения")
                    continue
                
                elif msg.startswith('посчитай '):
                    expression = original_text[9:].strip()
                    if expression:
                        result = tosik_assistant.calculate_expression(expression)
                        send_message(peer_id, result)
                    else:
                        send_message(peer_id, "❌ Укажите выражение для вычисления")
                    continue
                
                # ========== АДМИН-КОМАНДЫ ==========
                if is_admin(user_id):
                    # Добавление предмета
                    if msg.startswith('добавить предмет '):
                        parts = original_text[17:].strip().split()
                        if len(parts) >= 2 and parts[-1].isdigit():
                            max_reports = int(parts[-1])
                            subject_name = ' '.join(parts[:-1])
                            
                            if create_subject(subject_name, max_reports, user_id):
                                send_message(peer_id, f"✅ Предмет '{subject_name}' добавлен (макс. {max_reports} докладов на студента)")
                            else:
                                send_message(peer_id, f"❌ Ошибка: предмет '{subject_name}' уже существует")
                        else:
                            send_message(peer_id, "❌ Формат: 'Добавить предмет [название] [максимум докладов]'")
                        continue
                    
                    # Добавление доклада
                    elif msg.startswith('добавить доклад '):
                        parts = original_text[16:].strip().split()
                        if len(parts) >= 4 and parts[0].isdigit():
                            report_number = int(parts[0])
                            # Ищем "по" для разделения
                            if ' по ' in original_text:
                                subject_part = original_text.split(' по ', 1)[1]
                                subject_name = subject_part.strip()
                                report_title = ' '.join(parts[1:parts.index('по')]) if 'по' in parts else ' '.join(parts[1:])
                            else:
                                subject_name = parts[-1]
                                report_title = ' '.join(parts[1:-1])
                            
                            if add_report_to_subject(subject_name, report_number, report_title):
                                send_message(peer_id, f"✅ Доклад {report_number} добавлен к предмету '{subject_name}': {report_title}")
                            else:
                                send_message(peer_id, f"❌ Ошибка: предмет '{subject_name}' не найден")
                        else:
                            send_message(peer_id, "❌ Формат: 'Добавить доклад [номер] [название] по [предмет]'")
                        continue
                    
                    # Добавление админа
                    elif msg.startswith('добавить админа '):
                        parts = original_text[16:].strip().split()
                        if parts and parts[0].isdigit():
                            new_admin_id = int(parts[0])
                            if add_admin(new_admin_id, user_id):
                                send_message(peer_id, f"✅ Пользователь {new_admin_id} добавлен как администратор")
                            else:
                                send_message(peer_id, f"❌ Пользователь {new_admin_id} уже является администратором")
                        else:
                            send_message(peer_id, "❌ Формат: 'Добавить админа [ID пользователя]'")
                        continue
                
                # ========== ОБЩИЕ ВОПРОСЫ ==========
                else:
                    # Простые ответы на common вопросы
                    simple_answers = {
                        'привет': 'Привет! Я Тосик - бот-помощник для студентов! 🎓\nНапиши "Помощь" чтобы узнать что я умею!',
                        'как дела': 'Отлично! Готов помогать с учебой! 📚\nНужна помощь с расписанием, докладами или рефератами?',
                        'спасибо': 'Всегда рад помочь! 😊\nЕсли нужна еще помощь - просто спроси!',
                        'кто ты': 'Я Тосик - умный бот-помощник для студентов! 🎓\nУмею работать с расписанием, докладами, рефератами и даже решать математические задачи!',
                        'что ты умеешь': 'Я умею:\n• Показывать расписание 📅\n• Работать с системой докладов 📚\n• Генерировать рефераты 📝\n• Решать математические задачи 🧮\nНапиши "Помощь" для подробностей!'
                    }
                    
                    if msg in simple_answers:
                        send_message(peer_id, simple_answers[msg])
                        continue
                    
                    # Если сообщение не распознано
                    if len(msg) > 3:  # Игнорируем короткие сообщения
                        send_message(peer_id, "🤔 Не совсем понял ваш вопрос...\n📝 Напишите 'Помощь' чтобы узнать что я умею!")
                        
    except Exception as e:
        print(f"❌ Ошибка в главном цикле: {e}")
        continue
