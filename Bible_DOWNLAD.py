from flask import Flask, request, Response, render_template
import requests
import re
import json
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

GEMATRIA_VALUES = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5,
    "ו": 6, "ז": 7, "ח": 8, "ט": 9, "י": 10,
    "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60,
    "ע": 70, "פ": 80, "צ": 90, "ק": 100, "ר": 200,
    "ש": 300, "ת": 400, "ך": 500, "ם": 600,
    "ן": 700, "ף": 800, "ץ": 900
}

VERSES_PER_PAGE = 10
cache = {}

def jsonify_hebrew(data, status=200):
    json_str = json.dumps(data, ensure_ascii=False)
    return Response(json_str, content_type='application/json; charset=utf-8', status=status)

def remove_nikud_and_tags(text):
    text = re.sub(r'[\u0591-\u05C7]', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\u05D0-\u05EA\u05DA\u05DD\u05DF\u05E3\u05E5\s\-]', '', text)
    return text.strip()

def calculate_gematria(word):
    letters = list(word)
    values = [GEMATRIA_VALUES.get(l, 0) for l in letters]
    total = sum(values)
    return values, total

def process_verse(verse_text):
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
    structure = {}
    chapter_num = 1
    while True:
        if max_chapter and chapter_num > max_chapter:
            break
        verses = load_chapter(book, chapter_num)
        if not verses:
            break
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

def wants_html():
    """פונקציה עזר: בודקת האם הכותרת Accept כוללת text/html"""
    return 'text/html' in request.headers.get('Accept', '')

@app.route("/")
def home():
    if wants_html():
        return render_template("index.html")
    else:
        return jsonify_hebrew({"message": "ברוכים הבאים ל-API של התנ\"ך עם גימטריה"})

@app.route('/tanakh/<book>', methods=['GET'])
def get_book(book):
    structure = build_book_structure(book)
    if structure is None:
        error_msg = "ספר לא נמצא או ריק"
        if wants_html():
            return render_template("error.html", error=error_msg), 404
        else:
            return jsonify_hebrew({"error": error_msg}, status=404)

    if wants_html():
        chapters = list(structure[book].keys())
        return render_template("book.html", book=book, chapters=chapters)
    else:
        return jsonify_hebrew(structure)

@app.route('/tanakh/<book>/<int:chapter>', methods=['GET'])
def get_chapter(book, chapter):
    verses = load_chapter(book, chapter)
    if verses is None:
        error_msg = "פרק לא נמצא"
        if wants_html():
            return render_template("error.html", error=error_msg), 404
        else:
            return jsonify_hebrew({"error": error_msg}, status=404)

    processed_verses = {}
    for idx, verse_text in enumerate(verses, start=1):
        processed_verses[str(idx)] = {
            "text": verse_text,
            "gematria": process_verse(verse_text)
        }

    if wants_html():
        return render_template("chapter.html", book=book, chapter=chapter, verses=processed_verses)
    else:
        return jsonify_hebrew({
            "book": book,
            "chapter": chapter,
            "total_verses": len(verses),
            "verses": processed_verses
        })

@app.route('/tanakh/<book>/<int:chapter>/page/<int:page>', methods=['GET'])
def get_chapter_page(book, chapter, page):
    verses = load_chapter(book, chapter)
    if verses is None:
        error_msg = "פרק לא נמצא"
        if wants_html():
            return render_template("error.html", error=error_msg), 404
        else:
            return jsonify_hebrew({"error": error_msg}, status=404)

    start_index = (page - 1) * VERSES_PER_PAGE
    end_index = start_index + VERSES_PER_PAGE
    page_verses = verses[start_index:end_index]

    if not page_verses:
        error_msg = "עמוד לא נמצא"
        if wants_html():
            return render_template("error.html", error=error_msg), 404
        else:
            return jsonify_hebrew({"error": error_msg}, status=404)

    processed_verses = {}
    for idx, verse_text in enumerate(page_verses, start=start_index + 1):
        processed_verses[str(idx)] = {
            "text": verse_text,
            "gematria": process_verse(verse_text)
        }

    total_pages = (len(verses) + VERSES_PER_PAGE - 1) // VERSES_PER_PAGE

    if wants_html():
        return render_template("chapter_page.html", book=book, chapter=chapter, page=page, total_pages=total_pages, verses=processed_verses)
    else:
        return jsonify_hebrew({
            "book": book,
            "chapter": chapter,
            "page": page,
            "total_pages": total_pages,
            "verses": processed_verses
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
        error_msg = "הספר לא נמצא או ריק"
        if wants_html():
            return render_template("error.html", error=error_msg), 404
        else:
            return jsonify_hebrew({"error": error_msg}, status=404)

    if wants_html():
        return render_template("last_chapter.html", book=book, last_chapter=last_valid_chapter)
    else:
        return jsonify_hebrew({
            "book": book,
            "last_chapter": last_valid_chapter
        })

@app.route('/tanakh/<book>/<int:chapter>/<int:verse>', methods=['GET'])
def get_single_verse(book, chapter, verse):
    verses = load_chapter(book, chapter)
    if verses is None:
        error_msg = "פרק לא נמצא"
        if wants_html():
            return render_template("error.html", error=error_msg), 404
        else:
            return jsonify_hebrew({"error": error_msg}, status=404)

    if verse < 1 or verse > len(verses):
        error_msg = "פסוק לא נמצא"
        if wants_html():
            return render_template("error.html", error=error_msg), 404
        else:
            return jsonify_hebrew({"error": error_msg}, status=404)

    verse_text = verses[verse - 1]
    processed = process_verse(verse_text)

    if wants_html():
        return render_template("verse.html", book=book, chapter=chapter, verse=verse, text=verse_text, gematria=processed)
    else:
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
        error_msg = "שדה 'text' חסר בגוף הבקשה"
        if wants_html():
            return render_template("error.html", error=error_msg), 400
        else:
            return jsonify_hebrew({"error": error_msg}, status=400)

    text = data['text']
    processed = process_verse(text)

    if wants_html():
        # בד"כ POST לא יחזיר HTML, אבל במקרה כזה נחזיר תוצאה פשוטה בדף
        return render_template("gematria_result.html", original_text=text, gematria=processed)
    else:
        return jsonify_hebrew({"original_text": text, "gematria": processed})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
