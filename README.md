# תנ״ך בתרגום גיאומטרי (Gematria Tanakh API)

API מבוסס Flask לתרגום כל התנ״ך לערכים מספריים (גימטריה) לפי אותיות עבריות.  
הפרויקט משתמש בנתוני טקסט מהאתר [sefaria.org](https://www.sefaria.org/) ומחשב גימטריה עבור כל מילה בכל פסוק.

---

## 🚀 דוגמה לשימוש

### בקשת פסוק עם חישוב גימטריה:
GET /tanakh/בראשית/1/5

bash
Copy
Edit

#### תגובת JSON:
```json
{
  "book": "בראשית",
  "chapter": 1,
  "verse": 5,
  "text": "וַיִּקְרָא אֱלֹהִים לָאוֹר יוֹם...",
  "gematria": [
    {
      "word": "ויקרא",
      "values": [6, 10, 100, 200, 1],
      "total": 317
    },
    ...
  ]
}
📘 נתיבים זמינים (API Endpoints)
/tanakh/<book> – כל הספר

/tanakh/<book>/<chapter> – פרק מסוים

/tanakh/<book>/<chapter>/<verse> – פסוק מסוים

/tanakh/<book>/<chapter>/page/<page> – דפדוף לפי עמודים

/tanakh/<book>/last_chapter – הפרק האחרון הקיים בספר

POST /gematria – חישוב גימטריה לטקסט חופשי (גוף הבקשה: JSON עם text)

🛠 התקנה מקומית
bash
Copy
Edit
git clone https://github.com/yogev1520/tanakh-geometric-api.git
cd tanakh-geometric-api
pip install -r requirements.txt
python app.py
🌐 פריסה
ניתן לפרוס את הפרויקט בקלות על Render, Railway או Heroku.

python
Copy
Edit
# הפעלת שרת עם תמיכה בענן
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
✡️ קרדיט
מקור הפסוקים: Sefaria API

חישוב גימטריה לפי ערכי האותיות העבריות כולל סופיות

על ידי יוגב שושן 

אימייל YOGEV1520@GMAIL.COM

טל - 0559729311 

https://tanakh-geometric-api-4.onrender.com <<<<>>>>  גישה לאתר   