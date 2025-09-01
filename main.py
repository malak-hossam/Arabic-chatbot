from fastapi import FastAPI
from pydantic import BaseModel
import requests
import google.generativeai as genai
from langchain.memory import ConversationBufferMemory

# إعداد API
app = FastAPI()

# إعداد Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# الذاكرة
user_memories = {}
user_last_questions = {}

def get_user_memory(user_id: str):
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferMemory(return_messages=True)
    return user_memories[user_id]

# توليد رد مع استخدام التاريخ
def generate_with_history(memory, prompt, limit=3):
    chat_history = memory.load_memory_variables({}).get("history", [])
    recent_history = chat_history[-limit:]
    chat_text = "\n".join([m.content if hasattr(m, "content") else str(m) for m in recent_history]) + "\n" + prompt
    return model.generate_content(chat_text).text.strip()

# التعرف على إجابة غير معروفة
def is_unknown_answer(text):
    unknown_phrases = [
        "لا أعرف", "لا ادري", "ما اعرف", "مش عارف", "ما هي الإجابة", "ما الإجابة", "إيه الإجابة", "معرفش", "ممكن الإجابة", "الإجابة إيه"
    ]
    return any(phrase in text.lower() for phrase in unknown_phrases)

# نموذج البيانات
class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    user_id = req.user_id
    user_input = req.message.strip()
    memory = get_user_memory(user_id)

    # التحية
    greetings = ["مساء الخير", "صباح الخير", "السلام عليكم", "أهلا", "أهلاً", "هاي", "هلا", "إزيك", "مرحبا", "hello", "hi"]
    if any(greet in user_input.lower() for greet in greetings):
        reply = "👋 أهلاً وسهلاً! كيف يمكنني مساعدتك اليوم؟"
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(reply)
        return {"response": reply}

    # الرد المباشر
    if "عنوان" in user_input:
        prompt = f"""المستخدم كتب فكرة: "{user_input}"\nاقترح له عنوانًا جذابًا لمقال باللغة العربية."""
        reply = model.generate_content(prompt).text.strip()
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(reply)
        return {"response": reply}

    if "فكرة" in user_input and "اكتب" in user_input:
        prompt = f"""المستخدم كتب فكرة: "{user_input}"\nاكتب له فقرة بلغة فصحى وأسلوب أكاديمي."""
        reply = model.generate_content(prompt).text.strip()
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(reply)
        return {"response": reply}

    if "أعرب" in user_input:
        prompt = f"""المستخدم طلب إعراب الجملة:\n"{user_input}"\nأعربها تفصيليًا وفسّر بلغة بسيطة."""
        reply = model.generate_content(prompt).text.strip()
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(reply)
        return {"response": reply}

    # تحليل النية
    intent_prompt = f"""
    حلل الجملة التالية وحدد:
    - نوع الطلب: معنى / جمع / تضاد / شرح / صرف / كتابة فقرة / سؤال تعليمي / تقييم إجابة.
    - الكلمة أو الدرس أو المحتوى.
    الجملة:
    "{user_input}"
    أجب فقط بهذا الشكل:
    intent: ...
    word: ...
    """
    try:
        analysis = generate_with_history(memory, intent_prompt)
        intent = analysis.split("intent:")[1].split("\n")[0].strip()
        word = analysis.split("word:")[1].strip()
    except:
        intent = ""
        word = ""

    # ✅ إذا الجملة فيها "لا أعرف" أو ما شابه → نرسل الإجابة النموذجية
    if is_unknown_answer(user_input):
        if user_id in user_last_questions:
            lesson = user_last_questions[user_id]["lesson"]
            question = user_last_questions[user_id]["question"]
            answer_prompt = f"""اكتب إجابة نموذجية لهذا السؤال من درس {lesson}:\n{question}"""
            reply = model.generate_content(answer_prompt).text.strip()
        else:
            reply = "❌ لم يتم تحديد السؤال الذي تريد إجابته. اطلب سؤالًا أولاً."
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(reply)
        return {"response": reply}

    # ✅ إذا كان المستخدم لديه سؤال محفوظ وكان intent غير محدد → نعتبرها إجابة
    if user_id in user_last_questions:
        # التحقق من أن الإدخال ليس طلب جديد للمعاني أو الأسئلة
        if intent not in ["معنى", "جمع", "تضاد", "شرح", "صرف", "سؤال تعليمي", "كتابة فقرة"]:
            # التأكد أن الإدخال ليس تحية أو طلب مساعدة عام
            general_requests = ["مساعدة", "help", "ايه", "إيه", "شو", "وش", "كيف"]
            if not any(req in user_input.lower() for req in general_requests):
                intent = "تقييم إجابة"
                word = user_input

    # تنفيذ حسب النية
    if intent in ["كتابة فقرة", "شرح"]:
        prompt = f"اكتب فقرة بسيطة حول: {word}"
        reply = model.generate_content(prompt).text.strip()

    elif intent == "صرف":
        try:
            res = requests.post("https://malak-hossam-morpology.hf.space/morphology", json={"text": word})
            if res.status_code == 200:
                result_list = res.json().get("result", [])
                if result_list and isinstance(result_list, list):
                    output = result_list[0]
                    reply = "\n".join([f"{key}: {val}" for key, val in output.items()])
                else:
                    reply = f"❌ لم أجد التحليل الصرفي للكلمة: {word}."
            else:
                reply = f"❌ لم أتمكن من الاتصال بخدمة التحليل الصرفي."
        except:
            reply = f"❌ حدث خطأ أثناء جلب التحليل الصرفي للكلمة: {word}."

    elif intent in ["معنى", "جمع", "تضاد"]:
        try:
            type_map = {"معنى": "synonyms", "تضاد": "antonyms", "جمع": "plural"}
            res = requests.post("https://malak-hossam-word-meaning.hf.space/analyze/", json={"word": word, "type": type_map[intent]})
            meaning = res.json().get("result", "")
            reply = meaning if meaning else f"❌ لم أجد {intent} للكلمة: {word}."
        except:
            reply = f"❌ حدث خطأ أثناء جلب {intent} للكلمة: {word}."

    elif intent == "سؤال تعليمي":
        difficulty = "صعب" if "صعب" in user_input else "سهل" if "سهل" in user_input else "عادي"
        prompt = f"""
اكتب تمرينًا نحويًا على درس "{word}" بمستوى {difficulty}.
يجب أن يحتوي التمرين على:
- عنوان واضح
- صيغة السؤال
- من 2 إلى 3 جمل للطالب ليعربها أو يحدد عناصرها.
لا تضع الإجابة.
"""
        reply = model.generate_content(prompt).text.strip()
        user_last_questions[user_id] = {"lesson": word, "question": reply}

    elif intent == "تقييم إجابة":
        if user_id not in user_last_questions:
            reply = "❌ لم تقم بطلب سؤال بعد. اطلب سؤال أولًا مثلاً: اديني سؤال على درس كذا."
        else:
            question_data = user_last_questions[user_id]
            question = question_data["question"]
            lesson = question_data["lesson"]
            answer = word
            eval_prompt = f"""
أنت مدقق نحوي محترف. المطلوب منك تقييم إجابة الطالب على السؤال التالي.
🔹 السؤال:
{question}
🔹 إجابة الطالب:
{answer}
📌 التعليمات:
- ابدأ بـ "الإجابة: صحيحة." أو "الإجابة: خاطئة."
- ثم تعليل مختصر.
- لا تستخدم نبرة سلبية.
- لا تكرر نفس السؤال.
الآن قيّم:
"""
            reply = model.generate_content(eval_prompt).text.strip()

    else:
        reply = "❌ لم أتعرف على نوع السؤال. جرب بصيغة أخرى."

    memory.chat_memory.add_user_message(user_input)
    memory.chat_memory.add_ai_message(reply)

    return {"response": reply}
