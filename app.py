import os
import re
import json
from flask import Flask, render_template, request
from google import genai

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "laws.json")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

def normalize_arabic(text):
    text = (text or "").strip().lower()
    replacements = {
        "أ": "ا", "إ": "ا", "آ": "ا",
        "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def load_laws():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def search_articles(question, limit=6):
    q = normalize_arabic(question)
    q_words = {w for w in q.split() if len(w) > 2}
    results = []

    for item in load_laws():
        searchable = normalize_arabic(
            f"{item.get('law_name','')} {item.get('article_number','')} "
            f"{item.get('title','')} {item.get('text','')} "
            f"{' '.join(item.get('keywords', []))}"
        )
        words = set(searchable.split())
        overlap = len(q_words & words)

        # Boost exact keyword matches
        keyword_boost = 0
        for kw in item.get("keywords", []):
            nkw = normalize_arabic(kw)
            if nkw and nkw in q:
                keyword_boost += 3

        score = overlap + keyword_boost
        if score > 0:
            results.append((score, item))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results[:limit]]

def build_sources_text(articles):
    blocks = []
    for a in articles:
        blocks.append(
            f"""القانون: {a['law_name']}
المادة: {a['article_number']}
العنوان: {a.get('title','')}
النص: {a['text']}"""
        )
    return "\n\n---\n\n".join(blocks)

def answer_with_ai(question, articles):
    if not articles:
        return (
            "لم أجد في قاعدة النصوص القانونية الحالية مادة كافية "
            "للإجابة على هذا السؤال."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "لم يتم ضبط GEMINI_API_KEY في إعدادات الموقع."

    client = genai.Client(api_key=api_key)

    sources = build_sources_text(articles)

    prompt = f"""
أنت مستشار قانوني ذكي متخصص في النصوص القانونية الإماراتية.

التزم بالقواعد التالية:
- استخدم فقط النصوص القانونية الموجودة أدناه.
- لا تستخدم أحكاما قضائية.
- لا تستخدم معلومات قانونية من خارج النصوص المقدمة.
- لا تخترع أرقام مواد أو قواعد قانونية.
- إذا كانت النصوص غير كافية، قل بوضوح إن النصوص المتاحة لا تكفي.
- لا تستخدم علامات Markdown مثل ** أو # أو *.
- اكتب العناوين كنص عادي وواضح.
- لا تفترض أي واقعة لم يذكرها المستخدم.
- إذا كانت النتيجة تتوقف على واقعة ناقصة، وضح ذلك صراحة.
- لا تستخدم إلا المواد الموجودة في قاعدة النصوص القانونية.
- لا تذكر أي حكم قضائي أو اجتهاد قضائي.
- لا تخترع أرقام مواد.
- إذا لم تكف النصوص المتاحة، اذكر ذلك بوضوح.

رتب الإجابة كالتالي:

1. الوقائع المستخلصة
2. المسألة القانونية
3. المواد القانونية ذات الصلة
4. التحليل القانوني
5. النتيجة الأولية
6. المعلومات الناقصة إن وجدت

السؤال:
{question}

النصوص القانونية المتاحة:
{sources}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    return response.text
    
@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    articles = []
    question = ""

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if question:
            articles = search_articles(question)
            try:
                answer = answer_with_ai(question, articles)
            except Exception as e:
                answer = f"تعذر إنشاء التحليل الذكي حاليا: {str(e)}"

    return render_template(
        "index.html",
        question=question,
        answer=answer,
        articles=articles
    )

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)
