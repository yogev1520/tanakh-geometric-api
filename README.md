# 📖 תנ"ך בתרגום גיאומטרי – Tanakh Geometric Translation API

API בקוד פתוח אשר מספק תרגום גימטרי (Gematria) לפסוקים מהתנ"ך, עם תמיכה בעברית מלאה ובגישה לפי ספרים, פרקים ופסוקים בודדים.

המערכת משתמשת בטקסטים מתוך [Sefaria.org](https://www.sefaria.org/) ומחזירה תוצאה מפורטת הכוללת את הטקסט המקראי לצד ניתוח גימטרי לכל מילה.

---

## 🚀 מה הפרויקט עושה?

- טוען טקסטים מהתנ"ך (API של ספריא)
- מנתח כל מילה לפי ערך האותיות (גימטריה)
- מחזיר JSON עם כל המידע: טקסט מקראי, מילות הפסוק, ערכי האותיות, וסכום גימטרי
- תומך בעימוד (Paging) של פסוקים
- זמין להפעלה מקומית או פריסה בשרת

---

## 📌 דוגמה לפלט API

קריאה:

GET /tanakh/בראשית/1/1

css
Copy
Edit

תוצאה:

```json
{
  "book": "בראשית",
  "chapter": 1,
  "verse": 1,
  "text": "בְּרֵאשִׁית בָּרָא אֱלֹהִים...",
  "gematria": [
    {
      "word": "בראשית",
      "values": [2, 200, 1, 300, 10, 400],
      "total": 913
    },
    {
      "word": "ברא",
      "values": [2, 200, 1],
      "total": 203
    }
    ...
  ]
}
🔗 נקודות קצה
מסלול	תיאור
/tanakh/<book>	כל הספר
/tanakh/<book>/<chapter>	פרק ספציפי
/tanakh/<book>/<chapter>/<verse>	פסוק בודד
/tanakh/<book>/<chapter>/page/<page>	עמוד (10 פסוקים)
/tanakh/<book>/last_chapter	קבלת הפרק האחרון בספר
/gematria (POST)	שליחת טקסט חופשי וניתוח גימטרי

🛠️ התקנה מקומית
bash
Copy
Edit
git clone https://github.com/your_username/tanakh-geometric-api.git
cd tanakh-geometric-api
pip install -r requirements.txt
python app.py
💡 שימושים
לימוד תנ"ך עם גימטריה

כלי עזר למחקר מקראי

חינוך והעשרה יהודית

יצירת קשרים בין פסוקים בערכי גימטריה

📃 רישיון
פרויקט זה מופץ תחת רישיון MIT – חופשי לשימוש אישי, לימודי ומסחרי.

✨ נבנה באהבה ללימוד,