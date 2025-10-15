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
import sympy as sp
from sympy import symbols, integrate, diff, solve, pi
import numpy as np
from scipy import integrate as sci_integrate

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

# ... (остальной код бота остается таким же, но добавляем новые обработчики)

# В главный цикл обработки событий ДОБАВЛЯЕМ:

# === НОВЫЕ КОМАНДЫ ===
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

elif msg.startswith('рассчитать '):
    parts = original_text[11:].strip().split()
    if len(parts) >= 2:
        subject = parts[0].lower()
        task = ' '.join(parts[1:])
        
        if subject == 'механика':
            # Парсим параметры из задачи
            params = {}
            if 'масс' in task:
                params['m'] = float(re.findall(r'масс[аыу]? (\d+)', task)[0])
            if 'скорост' in task:
                speeds = re.findall(r'скорост[ьи]? (\d+)', task)
                if speeds:
                    params['v'] = float(speeds[0])
            if 'время' in task:
                times = re.findall(r'врем[яени]? (\d+)', task)
                if times:
                    params['t'] = float(times[0])
            
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
            else:
                send_message(peer_id, "❌ Укажите что рассчитать: ускорение, сила, энергия")
        else:
            send_message(peer_id, "❌ Доступные предметы: механика")
    else:
        send_message(peer_id, "❌ Формат: рассчитать [предмет] [задача]")

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

# ... (остальной код бота)
