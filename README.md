# المستشار القانوني الذكي

نسخة MVP أولى تعتمد على النصوص القانونية المدرجة في data/laws.json.

## التشغيل محليا

1. أنشئ بيئة Python.
2. ثبّت الحزم:
   pip install -r requirements.txt
3. اختياري لتفعيل التحليل الذكي:
   - Windows PowerShell:
     $env:OPENAI_API_KEY="YOUR_KEY"
   - macOS/Linux:
     export OPENAI_API_KEY="YOUR_KEY"
4. شغّل:
   python app.py
5. افتح:
   http://127.0.0.1:5000

## مهم
النصوص الموجودة في laws.json تجريبية فقط وليست النصوص الرسمية.
استبدلها بالنصوص القانونية الرسمية التي تريد اعتمادها.
