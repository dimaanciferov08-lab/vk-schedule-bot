"""
TOSIK VK BOT - single-file implementation (full)
- Telegram earlier, now VK: this file implements a VK community bot that:
  * fetches timetable from https://mauniver.ru/student/timetable/new/
  * selects Institute = "ИПАТ", Course = "1", Direction = "13.03.02" (or group string),
    and Group = "ЭЛ-ЭСб25о-1" (or any provided group)
  * supports user commands (vk messages) and a small keyboard:
      "Расписание" / "Сегодня" / "Завтра" / "Неделя" / "След неделя"
  * supports /setgroup-like command: "установить группу <GROUP>"
  * formats schedule prettily, similar to the screenshot the user showed
  * caches last fetched schedule for a short TTL to avoid repeated scraping
- Single-file: configure VK_TOKEN and GROUP_ID via environment variables or edit below.
- Requirements (pip):
    pip install vk_api selenium beautifulsoup4 python-dotenv
  And install chromedriver/chrome compatible with your environment.
- Notes:
  - Running Selenium on hosting may require headless chrome & chromedriver installation.
  - This code uses Bot Long Poll (VkBotLongPoll). Your community token must be group token
    with rights to messages (messages permission).
  - For production consider better error handling, retries, rate limits, and persistent DB.
"""

import os
import re
import time
import json
import sqlite3
import logging
from datetime import datetime, timedelta, date

from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# VK API imports
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

# Optional: load .env if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# ------------- CONFIG -------------
VK_TOKEN = os.getenv("vk1.a.Y2xBv4alWQ55rd1IxtkpKc48ibKqpQ1x0Wyc9Hv0z18elxu3JaSBfCi7F5sJ9H4eKy1jg3iqFOjQTkQyCIYdnf77mcezdC__MLiyRi9Xwfus_uLz7UWd9AR8VPQDr7uMEiD1NxadTzqUllP7p4uqWixuefYkm6ryhgMbFLPSo-hnXKyt0XQ4qvpfIG5kLWlJoH7Ivew1yhgiKmtDWhbHYw") or "<PUT_YOUR_VK_GROUP_TOKEN_HERE>"
VK_GROUP_ID = int(os.getenv("232761329") or os.getenv("232761329", "0") or 0)

# Timetable site
MAU_TIMETABLE_URL = "https://mauniver.ru/student/timetable/new/"

# Defaults for selection per user's instructions:
DEFAULT_INSTITUTE = "ИПАТ"
DEFAULT_COURSE = "1"
# Direction (code or text) — site offers selection; we attempt to match either code "13.03.02" or the short name
DEFAULT_DIRECTION_CODE = "13.03.02"  # will match on options text containing this
DEFAULT_GROUP_EXAMPLE = "ЭЛ-ЭСб25о-1"

# Cache TTL (seconds) - keep schedule for this many seconds to reduce scraping
SCHEDULE_CACHE_TTL = 60 * 60  # 1 hour

# SQLite DB file for user settings and cached schedules
DB_FILE = "tosik_vk_bot.db"

# Selenium options
CHROME_HEADLESS = True
SELENIUM_PAGE_TIMEOUT = 15

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tosik_vk_bot")

# ------------- DB helpers -------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            group_name TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS schedule_cache (
            key TEXT PRIMARY KEY,
            data TEXT,
            fetched_at TEXT
        )"""
    )
    conn.commit()
    conn.close()


def set_user_group(user_id: int, group_name: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO user_settings (user_id, group_name) VALUES (?, ?)",
        (user_id, group_name),
    )
    conn.commit()
    conn.close()


def get_user_group(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT group_name FROM user_settings WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
    def cache_schedule_put(key: str, data: dict):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
        "INSERT OR REPLACE INTO schedule_cache (key, data, fetched_at) VALUES (?, ?, ?)",
        (key, json.dumps(data, ensure_ascii=False), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def cache_schedule_get(key: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT data, fetched_at FROM schedule_cache WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    data_json, fetched_at = row
    fetched = datetime.fromisoformat(fetched_at)
    if datetime.utcnow() - fetched > timedelta(seconds=SCHEDULE_CACHE_TTL):
        return None
    try:
        return json.loads(data_json)
    except Exception:
        return None


# ------------- Selenium scraper helpers -------------
def get_driver():
    opts = Options()
    if CHROME_HEADLESS:
        # newer headless mode
        opts.add_argument("--headless=new")
    else:
        opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    # You may need to set the path to chromedriver: webdriver.Chrome(executable_path=..., options=opts)
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(SELENIUM_PAGE_TIMEOUT)
    return driver


def safe_find_element(driver, by, selector, timeout=8):
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.presence_of_element_located((by, selector)))


def attempt_click(element):
    try:
        element.click()
    except Exception:
        try:
            element.send_keys("\n")
        except Exception:
            pass


def _text_contains(a: str, b: str):
    return b.lower() in (a or "").lower()


def select_option_by_text(select_element, wanted_text):
    """Try to select option which contains wanted_text (case-insensitive)."""
    try:
        sel = Select(select_element)
        for opt in sel.options:
            if wanted_text.lower() in opt.text.lower():
                sel.select_by_visible_text(opt.text)
                return True
    except Exception:
        # fallback: try clicking option by executing JS
        try:
            opts = select_element.find_elements(By.TAG_NAME, "option")
            for o in opts:
                if wanted_text.lower() in o.text.lower():
                    driver = select_element.parent
                    o.click()
                    return True
        except Exception:
            return False
    return False


def parse_table_html_to_entries(html):
    """
    Given the page source after the timetable is loaded, parse lessons.
    The site structure may vary; we'll try:
    - find main timetable <table> elements
    - fallback to blocks with classes 'lesson' / 'timetable-row' / 'schedule-row'
    Return: list of entries; each entry is a dict:
      {
        'date': '2025-09-25',
        'weekday': 'Четверг',
        'pair_number': '3 пара',
        'time': '12:40–14:15',
        'subject': 'Химия',
        'kind': 'Лабораторная',
        'teacher': 'Долгопятова Н.В.',
        'room': '505Л',
        'building': 'пр. Кирова, д.1'
      }
    """
    soup = BeautifulSoup(html, "html.parser")
    lessons = []

    # Try locate main timetable table(s)
    tables = soup.find_all("table")
    if tables:
        # find the largest table (by rows) perhaps main schedule
        main_table = max(tables, key=lambda t: len(t.find_all("tr")))
        for tr in main_table.find_all("tr"):
            cols = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            if not cols:
                continue
                # Heuristic parsing depending on number of columns
            # common formats: [week day/date, time, subject, teacher, room, groups]
            entry = {
                "raw_cols": cols,
                "date": "",
                "weekday": "",
                "pair_number": "",
                "time": "",
                "subject": "",
                "kind": "",
                "teacher": "",
                "room": "",
                "building": "",
            }
            # naive parsing:
            if len(cols) >= 5:
                # try detect time pattern
                time_pat = re.compile(r"\d{1,2}[:.]\d{2}\s*[-–]\s*\d{1,2}[:.]\d{2}")
                for c in cols:
                    if time_pat.search(c):
                        entry["time"] = time_pat.search(c).group()
                        break
                # subject likely in 2nd/3rd column
                entry["subject"] = cols[2] if len(cols) > 2 else cols[1]
                # teacher in next
                entry["teacher"] = cols[3] if len(cols) > 3 else ""
                # room
                entry["room"] = cols[4] if len(cols) > 4 else ""
            else:
                # fallback: combine text
                entry["subject"] = " / ".join(cols)
            lessons.append(entry)
        return lessons

    # Fallback: blocks
    for block in soup.select(".lesson, .timetable-row, .schedule-row"):
        text = block.get_text(" ", strip=True)
        lessons.append({"raw_text": text})
    return lessons


def scrape_schedule_for_group(group_name: str, institute=DEFAULT_INSTITUTE, course=DEFAULT_COURSE, direction_code=DEFAULT_DIRECTION_CODE):
    """
    Main routine: open the timetable page, select filters and return parsed lessons.
    Attempts to:
      1) open page
      2) choose mode "По группам" if needed
      3) select institute, course, direction (by code or text), and group
      4) press show and wait for table
      5) parse result and return list
    Returns dict: { "group": group_name, "fetched_at": iso, "lessons": [...] }
    """
    # Check cache first (key per group+institute+course+direction)
    cache_key = f"{institute}|{course}|{direction_code}|{group_name}"
    cached = cache_schedule_get(cache_key)
    if cached:
        logger.info("Using cached schedule for key %s", cache_key)
        return cached

    driver = None
    try:
        driver = get_driver()
        driver.get(MAU_TIMETABLE_URL)
        wait = WebDriverWait(driver, 12)

        time.sleep(0.8)  # small pause for dynamic scripts

        # 1) Try to find a selector or input for choosing "По группам" — many university pages have tabs
        try:
            # find elements that could be the "По группам" tab; match by text
            possible_tabs = driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ПОГРУППАМ','погруппам'), 'погрупп') or contains(translate(text(),'ПО ГРУППАМ','по группам'),'по груп')]")
            for t in possible_tabs:
                try:
                    if "групп" in (t.text or "").lower():
                        attempt_click(t)
                        time.sleep(0.4)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # 2) Try selects for Institute, Course, Direction, Group
        # Strategy: find selects on page and try to match by visible text
        selects = driver.find_elements(By.TAG_NAME, "select")
        # We'll try heuristics: institute select contains text like "Институт" or "ИПАТ"
        def find_and_select(selects, wanted_texts):
            for s in selects:
                try:
                    options_texts = " ".join([o.text for o in Select(s).options if o.text])
                    for wt in wanted_texts:
                        if wt.lower() in options_texts.lower():
                            success = select_option_by_text(s, wt)
                            if success:
                                time.sleep(0.35)
                                return True
                except Exception:
                    continue
            return False

        # Select institute
        find_and_select(selects, [institute, "институт"])

        # Select course (1)
        find_and_select(selects, [course, f"{course} курс", "курс"])

        # Select direction: match code '13.03.02' or part of direction name
        find_and_select(selects, [direction_code])

        # Finally select group by name
        find_and_select(selects, [group_name])

        # Sometimes the form uses inputs with autocomplete instead of selects; try inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            ph = (inp.get_attribute("placeholder") or "").lower()
            name = (inp.get_attribute("name") or "").lower()
            if "группа" in ph or "группа" in name:
                try:
                    inp.clear()
                    inp.send_keys(group_name)
                    time.sleep(0.4)
                    inp.send_keys("\n")
                    break
                except Exception:
                    continue

        # Click "Показать" or similar button
        try:
            # look for button with text "Показать" or "Показать расписание"
            btn = driver.find_element(By.XPATH, "//button[contains(translate(.,'ПОКАЗАТЬ','показать'),'показ')]")
            attempt_click(btn)
        except Exception:
            # search input type=submit
            try:
                btn = driver.find_element(By.XPATH, "//input[@type='submit']")
                attempt_click(btn)
            except Exception:
                pass

        # Wait until table appears
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(0.5)
        except Exception:
            # maybe content in div; wait a bit more
            time.sleep(1.0)

        html = driver.page_source
        lessons = parse_table_html_to_entries(html)

        result = {"group": group_name, "fetched_at": datetime.utcnow().isoformat(), "lessons": lessons}
        cache_schedule_put(cache_key, result)
        return result
    except Exception as e:
        logger.exception("Error scraping schedule: %s", e)
        return {"group": group_name, "fetched_at": datetime.utcnow().isoformat(), "lessons": [], "error": str(e)}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


# ------------- Formatting helpers -------------
WEEKDAY_RU = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"}


def format_pretty_schedule_for_date(scraped: dict, target_date: date):
    """
    From scraped['lessons'] attempt to filter entries for the target_date.
    Because site parsing is heuristic, this function tries to detect dates/weekday mentions.
    If no per-date info present, returns full list.
    """
    lessons = scraped.get("lessons", [])
    filtered = []

    # Try to find date strings inside entries (raw_cols) that match dd.mm.yyyy or weekday names
    for ent in lessons:
        # If parser produced 'date' or 'raw_cols', check them
        matched = False
        # check known date fields
        if ent.get("date"):
            # parse dd.mm.yyyy inside
            m = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", ent["date"])
            if m:
                try:
                    d = datetime.strptime(m.group(1), "%d.%m.%Y").date()
                    if d == target_date:
                        filtered.append(ent)
                        matched = True
                except Exception:
                    pass
        # check raw_cols
        if not matched and ent.get("raw_cols"):
            cols_join = " ".join(ent["raw_cols"])
            m = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", cols_join)
            if m:
                try:
                    d = datetime.strptime(m.group(1), "%d.%m.%Y").date()
                    if d == target_date:
                        filtered.append(ent)
                        matched = True
                except Exception:
                    pass
        # check raw_text
        if not matched and ent.get("raw_text"):
            m = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", ent["raw_text"])
            if m:
                try:
                    d = datetime.strptime(m.group(1), "%d.%m.%Y").date()
                    if d == target_date:
                        filtered.append(ent)
                        matched = True
                except Exception:
                    pass

    # if we found none by date, attempt to filter by weekday name present in text (e.g., "Четверг")
    if not filtered:
        wd_name = WEEKDAY_RU[target_date.weekday()]
        for ent in lessons:
            text = " ".join(ent.get("raw_cols", [])) if ent.get("raw_cols") else ent.get("raw_text", "")
            if not text:
                text = " ".join([v for v in ent.values() if isinstance(v, str)])
            if wd_name.lower() in text.lower():
                filtered.append(ent)

    # if still nothing, as fallback return the whole list
    if not filtered:
        filtered = lessons

    # format entries to textual blocks
    blocks = []
    for e in filtered:
        # Attempt to extract meaningful fields
        subj = e.get("subject") or (e.get("raw_cols")[2] if e.get("raw_cols") and len(e["raw_cols"]) > 2 else (e.get("raw_text") if e.get("raw_text") else "Предмет"))
        time_field = e.get("time") or (e.get("raw_cols")[1] if e.get("raw_cols") and len(e["raw_cols"]) > 1 else "")
        teacher = e.get("teacher") or ""
        room = e.get("room") or ""
        kind = e.get("kind") or ""
        # build block
        lines = []
        if time_field:
            lines.append(f"⏰ {time_field}")
        lines.append(f"📚 Предмет: {subj.strip()}")
        if kind:
            lines.append(f"🏛️ Тип: {kind}")
        if teacher:
            lines.append(f"👨‍🏫 Преподаватель: {teacher}")
        if room:
            lines.append(f"🚪 Аудитория: {room}")
        blocks.append("\n".join(lines))
    return blocks


def build_vk_message_for_date(group_name: str, pretty_blocks: list, target_date: date):
    header = f"📘 Расписание: {group_name}\n──────────────────────────────\n"
    header += f"📅 {WEEKDAY_RU[target_date.weekday()]}, {target_date.strftime('%d.%m.%Y')}\n──────────────────────────────\n"
    if not pretty_blocks:
        body = "Пары не найдены на эту дату."
    else:
        body = "\n\n".join(pretty_blocks)
    footer = f"\n\n🕒 Обновлено: {datetime.utcnow().strftime('%d.%m.%Y %H:%M UTC')}\n──────────────────────────────"
    # Buttons will be added via keyboard in VK event handler
    return header + body + footer


# ------------- VK Bot core -------------
def create_keyboard():
    """
    Return keyboard JSON for VK messages (simple three buttons: Сегодня, Неделя, След. неделя)
    """
    keyboard = {
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": "Сегодня"}, "color": "primary"},
             {"action": {"type": "text", "label": "Завтра"}, "color": "primary"},
             {"action": {"type": "text", "label": "Неделя"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "След. неделя"}, "color": "secondary"},
            {"action": {"type": "text", "label": "Установить группу"}, "color": "negative"},
             {"action": {"type": "text", "label": "Моя группа"}, "color": "positive"}],
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False).encode('utf-8')


def handle_text_message(vk, event, text):
    """
    Main text handler: decides what to do based on lowercase text.
    """
    user_id = event.obj["message"]["from_id"]
    text_stripped = text.strip()

    # Quick commands
    lc = text_stripped.lower()
    # set group: "установить группу <name>" or "установить группу" (prompt)
    if lc.startswith("установить группу"):
        # extract group name after command
        parts = text_stripped.split(maxsplit=2)
        if len(parts) >= 3:
            group_name = parts[2].strip()
            set_user_group(user_id, group_name)
            vk.messages.send(peer_id=user_id, message=f"Группа установлена: {group_name}", random_id=get_random_id())
        else:
            vk.messages.send(peer_id=user_id, message="Напиши: Установить группу ЭЛ-ЭСб25о-1", random_id=get_random_id())
        return

    if lc == "моя группа":
        g = get_user_group(user_id)
        if g:
            vk.messages.send(peer_id=user_id, message=f"Ваша группа: {g}", random_id=get_random_id())
        else:
            vk.messages.send(peer_id=user_id, message="Группа не установлена. Напиши: Установить группу <ГРУППА>", random_id=get_random_id())
        return

    # which group to use
    group = get_user_group(user_id) or DEFAULT_GROUP_EXAMPLE

    # schedule requests
    if lc in ["расписание", "сегодня"]:
        target = date.today()
        scraped = scrape_schedule_for_group(group, institute=DEFAULT_INSTITUTE, course=DEFAULT_COURSE, direction_code=DEFAULT_DIRECTION_CODE)
        pretty = format_pretty_schedule_for_date(scraped, target)
        msg = build_vk_message_for_date(group, pretty, target)
        vk.messages.send(peer_id=user_id, message=msg, keyboard=create_keyboard(), random_id=get_random_id())
        return

    if lc == "завтра":
        target = date.today() + timedelta(days=1)
        scraped = scrape_schedule_for_group(group, institute=DEFAULT_INSTITUTE, course=DEFAULT_COURSE, direction_code=DEFAULT_DIRECTION_CODE)
        pretty = format_pretty_schedule_for_date(scraped, target)
        msg = build_vk_message_for_date(group, pretty, target)
        vk.messages.send(peer_id=user_id, message=msg, keyboard=create_keyboard(), random_id=get_random_id())
        return

    if lc == "неделя":
        # show week: iterate days Mon-Sun for current week (starting monday)
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        all_blocks = []
        scraped = scrape_schedule_for_group(group, institute=DEFAULT_INSTITUTE, course=DEFAULT_COURSE, direction_code=DEFAULT_DIRECTION_CODE)
        for d in [monday + timedelta(days=i) for i in range(7)]:
            pretty = format_pretty_schedule_for_date(scraped, d)
            header = f"📅 {WEEKDAY_RU[d.weekday()]} {d.strftime('%d.%m.%Y')}\n"
            if pretty:
                all_blocks.append(header + "\n".join(pretty))
            else:
                all_blocks.append(header + "— Пары отсутствуют")
        full_msg = f"📘 Расписание группы {group} (на текущую неделю)\n──────────────────────────────\n" + "\n\n".join(all_blocks) + f"\n\n🕒 Обновлено: {datetime.utcnow().strftime('%d.%m.%Y %H:%M UTC')}"
        vk.messages.send(peer_id=user_id, message=full_msg, keyboard=create_keyboard(), random_id=get_random_id())
        return

    if lc in ["след. неделя", "след неделя", "следняя неделя", "след.неделя"]:
        # next week
        today = date.today()
        next_monday = today - timedelta(days=today.weekday()) + timedelta(days=7)
        all_blocks = []
        scraped = scrape_schedule_for_group(group, institute=DEFAULT_INSTITUTE, course=DEFAULT_COURSE, direction_code=DEFAULT_DIRECTION_CODE)
        for d in [next_monday + timedelta(days=i) for i in range(7)]:
            pretty = format_pretty_schedule_for_date(scraped, d)
            header = f"📅 {WEEKDAY_RU[d.weekday()]} {d.strftime('%d.%m.%Y')}\n"
            if pretty:
                all_blocks.append(header + "\n".join(pretty))
            else:
                all_blocks.append(header + "— Пары отсутствуют")
        full_msg = f"📘 Расписание группы {group} (на следующую неделю)\n──────────────────────────────\n" + "\n\n".join(all_blocks) + f"\n\n🕒 Обновлено: {datetime.utcnow().strftime('%d.%m.%Y %H:%M UTC')}"
        vk.messages.send(peer_id=user_id, message=full_msg, keyboard=create_keyboard(), random_id=get_random_id())
        return

    # small talk: "тосик, шутка" or "тосик, факт"
    if lc.startswith("тосик"):
        body = text_stripped[5:].strip().lower()
        if body.startswith("шут"):
            vk.messages.send(peer_id=user_id, message="— Почему программисту холодно? — Потому что он забыл закрыть скобку 😂", random_id=get_random_id())
            return
        if body.startswith("факт"):
            vk.messages.send(peer_id=user_id, message="Интересный факт: электричество в 18 веке изучали в основном как развлечение — для 'шок-выступлений' и демонстраций.", random_id=get_random_id())
            return
        # fallback small chat
        vk.messages.send(peer_id=user_id, message="Я Тосик — помогу с расписанием, рефератами и ответами. Напиши: 'Сегодня' / 'Завтра' / 'Неделя' или 'Установить группу <ГРУППА>'.", random_id=get_random_id())
        return

    # unknown
    vk.messages.send(peer_id=user_id, message="Не понял команду. Используй: Сегодня, Завтра, Неделя, След. неделя или 'Установить группу <ГРУППА>'.", random_id=get_random_id())


def main():
    if not VK_TOKEN or not VK_GROUP_ID:
        print("Ошибка: VK_TOKEN и VK_GROUP_ID должны быть указаны (environment vars or edit the script).")
        return

    init_db()

    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()

    longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

    print("Тосик VK бот запущен. Ожидание сообщений...")

    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                # event.obj holds data
                msg = event.obj["message"]
                text = msg.get("text", "")
                peer_id = msg.get("peer_id")
                from_id = msg.get("from_id")
                # For community chats peer_id differs; we respond to peer_id
                # If text empty - skip
                if not text:
                    continue

                # If the message is "Установить группу" button (we expect user to type after pressed)
                # We handle text commands centrally
                logger.info("Received msg from %s: %s", from_id, text)
                handle_text_message(vk, event, text)

        except Exception as e:
            logger.exception("Error handling event: %s", e)


if __name__ == "__main__":
    main()



