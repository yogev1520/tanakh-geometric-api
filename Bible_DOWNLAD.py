from flask import Flask, request, Response, render_template
import requests
import re
import json
import os
import logging

app = Flask(__name__)

# הגדרת לוגינג
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# מילון גימטריה
GEMATRIA_VALUES = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5,
    "ו": 6, "ז": 7, "ח": 8, "ט": 9, "י": 10,
    "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60,
    "ע": 70, "פ": 80, "צ": 90, "ק": 100, "ר": 200,
    "ש": 300, "ת": 400, "ך": 500, "ם": 600,
    "ן": 700, "ף": 800, "ץ": 900
}

VERSES_PER_PAGE = 10

# Cache בזיכרון - מילון: { book: { chapter: [פסוקים] } }
cache = {}

def jsonify_hebrew(data, status=200):
    """מחזיר JSON עם עברית קריאה (UTF-8)"""
    json_str = json.dumps(data, ensure_ascii=False)
    return Response(json_str, content_type='application/json; charset=utf-8', status=status)

def remove_nikud_and_tags(text):
    """
    מסיר ניקוד, תגיות HTML ותווים לא עבריים
    """
    text = re.sub(r'[\u0591-\u05C7]', '', text)  # ניקוד וטרגוט
    text = re.sub(r'<[^>]+>', '', text)          # תגיות HTML
    text = re.sub(r'[^\u05D0-\u05EA\u05DA\u05DD\u05DF\u05E3\u05E5\s\-]', '', text)  # אותיות עבריות ותווים מותרים
    return text.strip()

def calculate_gematria(word):
    """
    מחשב גימטריה עבור מילה נתונה
    """
    letters = list(word)
    values = [GEMATRIA_VALUES.get(l, 0) for l in letters]
    total = sum(values)
    return values, total

def process_verse(verse_text):
    """
    מעבד פסוק: מחזיר רשימה של מילים עם גימטריה
    """
    clean_text = remove_nikud_and_tags(verse_text)
    words = re.findall(r'[\u05D0-\u05EA\u05DA\u05DD\u05DF\u05E3\u05E5\-]+', clean_text)
    processed_words = []
    for word in words:
        values, total = calculate_gematria(word)
        processed_words.append({
            "word": word,
            "values": values,
            "total": total
        })
    return processed_words

def load_chapter(book, chapter):
    if book not in cache:
        cache[book] = {}

    if chapter in cache[book]:
        logging.info(f"Cache hit for {book} chapter {chapter}")
        return cache[book][chapter]

    url = f"https://www.sefaria.org/api/texts/{book}.{chapter}?lang=he"
    logging.info(f"Loading URL: {url}")
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        verses = data.get('he', [])
        logging.info(f"Received {len(verses)} verses for {book} chapter {chapter}")
        cache[book][chapter] = verses
        return verses
    except requests.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        return None

def build_book_structure(book, max_chapter=None):
    """
    בונה מילון מסודר עם כל הפרקים והפסוקים של הספר,
    עד max_chapter (אם לא מוגדר, טוען עד אין סוף).
    """
    structure = {}
    chapter_num = 1

    while True:
        if max_chapter and chapter_num > max_chapter:
            break

        verses = load_chapter(book, chapter_num)
        if not verses:
            break  # אין פרק כזה

        chapter_dict = {}
        for idx, verse_text in enumerate(verses, start=1):
            gematria = process_verse(verse_text)
            chapter_dict[str(idx)] = {
                "text": verse_text,
                "gematria": gematria
            }
        structure[str(chapter_num)] = chapter_dict
        chapter_num += 1

    if not structure:
        return None
    return {book: structure}

@app.route("/")
def home():
    # מחזיר את דף ה־HTML במקום JSON
    return render_template("index.html")

@app.route('/tanakh/<book>', methods=['GET'])
def get_book(book):
    structure = build_book_structure(book)
    if structure is None:
        return jsonify_hebrew({"error": "ספר לא נמצא או ריק"}, status=404)
    return jsonify_hebrew(structure)

@app.route('/tanakh/<book>/<int:chapter>', methods=['GET'])
def get_chapter(book, chapter):
    verses = load_chapter(book, chapter)
    if verses is None:
        return jsonify_hebrew({"error": "פרק לא נמצא"}, status=404)

    result = {}
    for idx, verse_text in enumerate(verses, start=1):
        processed = process_verse(verse_text)
        result[str(idx)] = {
            "text": verse_text,
            "gematria": processed
        }
    return jsonify_hebrew({
        "book": book,
        "chapter": chapter,
        "total_verses": len(verses),
        "verses": result
    })

@app.route('/tanakh/<book>/<int:chapter>/page/<int:page>', methods=['GET'])
def get_chapter_page(book, chapter, page):
    verses = load_chapter(book, chapter)
    if verses is None:
        return jsonify_hebrew({"error": "פרק לא נמצא"}, status=404)

    start_index = (page - 1) * VERSES_PER_PAGE
    end_index = start_index + VERSES_PER_PAGE
    page_verses = verses[start_index:end_index]

    if not page_verses:
        return jsonify_hebrew({"error": "עמוד לא נמצא"}, status=404)

    result = {}
    for idx, verse_text in enumerate(page_verses, start=start_index + 1):
        processed = process_verse(verse_text)
        result[str(idx)] = {
            "text": verse_text,
            "gematria": processed
        }

    total_pages = (len(verses) + VERSES_PER_PAGE - 1) // VERSES_PER_PAGE

    return jsonify_hebrew({
        "book": book,
        "chapter": chapter,
        "page": page,
        "total_pages": total_pages,
        "verses": result
    })

@app.route('/tanakh/<book>/last_chapter', methods=['GET'])
def get_last_chapter(book):
    chapter = 1
    last_valid_chapter = 0
    while True:
        verses = load_chapter(book, chapter)
        if verses is None or len(verses) == 0:
            break
        last_valid_chapter = chapter
        chapter += 1
    if last_valid_chapter == 0:
        return jsonify_hebrew({"error": "הספר לא נמצא או ריק"}, status=404)
    return jsonify_hebrew({
        "book": book,
        "last_chapter": last_valid_chapter
    })

@app.route('/tanakh/<book>/<int:chapter>/<int:verse>', methods=['GET'])
def get_single_verse(book, chapter, verse):
    verses = load_chapter(book, chapter)
    if verses is None:
        return jsonify_hebrew({"error": "פרק לא נמצא"}, status=404)
    if verse < 1 or verse > len(verses):
        return jsonify_hebrew({"error": "פסוק לא נמצא"}, status=404)

    verse_text = verses[verse - 1]
    processed = process_verse(verse_text)

    return jsonify_hebrew({
        "book": book,
        "chapter": chapter,
        "verse": verse,
        "text": verse_text,
        "gematria": processed
    })

@app.route('/gematria', methods=['POST'])
def gematria_endpoint():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify_hebrew({"error": "שדה 'text' חסר בגוף הבקשה"}, status=400)

    text = data['text']
    processed = process_verse(text)
    return jsonify_hebrew({"original_text": text, "gematria": processed})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
