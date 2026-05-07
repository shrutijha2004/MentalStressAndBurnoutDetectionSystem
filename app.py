from flask import Flask, render_template, request, redirect, session, jsonify
import random
import pickle
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

app.secret_key = "solene_secret_key"

API_KEY = "AIzaSyDAnIa5pVL8RM-nGoD3CZA4efRONQpTieM"

model_genai = None

try:

    genai.configure(api_key=API_KEY)

    model_genai = genai.GenerativeModel(
        "gemini-2.0-flash"
    )

    print("Gemini AI Loaded")

except Exception as e:

    print("Gemini Error:", e)

users = {}

otp_storage = {}

forgot_password_otp = {}

conversation_memory = {}

try:

    with open("Model/stress_model.pkl", "rb") as f:

        model = pickle.load(f)

    print("ML Model loaded successfully")

except Exception as e:

    model = None

    print("ML Model not found")

symptom_list = [

    "Persistent feelings of stress, anxiety, or nervousness",

    "Emotional exhaustion and mental fatigue",

    "Physical fatigue or lack of energy",

    "Difficulty concentrating and reduced cognitive clarity",

    "Loss of motivation or enthusiasm toward work or studies",

    "Increased irritability or emotional instability",

    "Feeling a lack of control over situations or emotions",

    "Decline in productivity or increased mistakes",

    "Sleep disturbances and lifestyle imbalance",

    "Accumulation of stressful experiences or emotional pressure",

    "Daily screen time or lack of regular breaks during work/study",

    "Feeling overwhelmed or unable to cope with responsibilities"

]

@app.route('/')
def login_page():

    return render_template(
        'login.html'
    )

@app.route('/login', methods=['POST'])
def login():

    login_id = request.form.get(
        'login_id'
    )

    password = request.form.get(
        'password'
    )

    if login_id in users and users[login_id] == password:

        session['user'] = login_id

        if login_id not in conversation_memory:

            conversation_memory[login_id] = []

        return redirect('/dashboard')

    return render_template(

        'login.html',

        error="Invalid credentials"

    )

@app.route('/create-account')
def create_account():

    return render_template(
        'create_account.html'
    )

@app.route('/signup', methods=['POST'])
def signup():

    contact = request.form.get(
        'contact'
    )

    password = request.form.get(
        'password'
    )

    confirm_password = request.form.get(
        'confirm_password'
    )

    if password != confirm_password:

        return render_template(

            'create_account.html',

            error="Passwords do not match"

        )

    otp = str(
        random.randint(1000, 9999)
    )

    otp_storage[contact] = {

        "otp": otp,

        "password": password

    }

    print("OTP:", otp)

    session['pending_user'] = contact

    return render_template(
        'verify.html'
    )

@app.route('/verify', methods=['POST'])
def verify():

    user_otp = request.form.get(
        'otp'
    )

    pending_user = session.get(
        'pending_user'
    )

    if pending_user in otp_storage:

        real_otp = otp_storage[pending_user]['otp']

        if user_otp == real_otp:

            users[pending_user] = otp_storage[pending_user]['password']

            session['user'] = pending_user

            conversation_memory[pending_user] = []

            del otp_storage[pending_user]

            return redirect('/dashboard')

    return render_template(

        'verify.html',

        error="Invalid OTP"

    )

@app.route('/forgot-password', methods=['POST'])
def forgot_password():

    contact = request.form.get('contact')

    otp = request.form.get('otp')

    new_password = request.form.get('new_password')

    confirm_new_password = request.form.get('confirm_new_password')

    action = request.form.get('action')

    if action == "send_otp":

        generated_otp = str(
            random.randint(1000, 9999)
        )

        forgot_password_otp[contact] = generated_otp

        print("Forgot Password OTP:", generated_otp)

        return render_template(

            'login.html',

            success="OTP sent successfully !"

        )

    if action == "reset_password":

        if new_password != confirm_new_password:

            return render_template(

                'login.html',

                error="Passwords do not match"

            )

        if contact not in forgot_password_otp:

            return render_template(

                'login.html',

                error="Please generate OTP first"

            )

        real_otp = forgot_password_otp[contact]

        if otp == real_otp:

            users[contact] = new_password

            del forgot_password_otp[contact]

            return render_template(

                'login.html',

                success="Password updated successfully 🌿 Please login."

            )

        return render_template(

            'login.html',

            error="Invalid OTP"

        )

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect('/')

    return render_template(
        'dashboard.html'
    )

@app.route('/symptoms')
def symptoms():

    if 'user' not in session:

        return redirect('/')

    return render_template(
        'index.html'
    )

@app.route('/predict', methods=['POST'])
def predict():

    values = []

    selected_symptoms = []

    for i in range(1, 13):

        val = int(
            request.form.get(
                f'q{i}',
                0
            )
        )

        values.append(val)

        if val == 1:

            selected_symptoms.append(
                symptom_list[i - 1]
            )

    score = sum(values)

    if score <= 3:

        prediction = "Low"

        burnout = "Low"

        progress = 25

        message = (
            "Your emotional wellness currently appears relatively balanced. "
            "Maintaining healthy routines, proper sleep, hydration, movement, and emotional support "
            "can help preserve long-term mental wellbeing 🌸"
        )

    elif score <= 7:

        prediction = "Moderate"

        burnout = "Moderate"

        progress = 55

        message = (
            "Your responses suggest moderate emotional stress and mental fatigue. "
            "Long-term stress may affect concentration, sleep quality, emotional balance, "
            "motivation, and productivity. Prioritizing recovery and emotional self-care may help 💛"
        )

    else:

        prediction = "High"

        burnout = "High"

        progress = 90

        message = (
            "Your responses suggest high stress and burnout risk. "
            "Persistent emotional overload may affect sleep, energy levels, motivation, "
            "concentration, emotional regulation, and overall wellbeing. "
            "Gentle recovery, structured rest, emotional support, and professional guidance "
            "may be beneficial 🌿"
        )

    session['stress_level'] = prediction

    session['burnout_level'] = burnout

    return render_template(

        'result.html',

        prediction=prediction,

        burnout=burnout,

        progress=progress,

        message=message,

        symptoms=selected_symptoms

    )

@app.route('/chat')
def chat():

    if 'user' not in session:

        return redirect('/')

    return render_template(
        'chat.html'
    )

@app.route('/chatbot', methods=['POST'])
def chatbot():

    data = request.get_json()

    user_message = data.get(
        'message',
        ''
    ).strip()

    lower = user_message.lower()

    user = session.get(
        'user',
        'guest'
    )

    if user not in conversation_memory:

        conversation_memory[user] = []

    conversation_memory[user].append({

        "message": user_message,

        "time": str(datetime.now())

    })

    greetings = [

        "hi", "hello", "hey",
        "hii", "heyy",
        "good morning",
        "good evening"

    ]

    goodbye_words = [

        "bye", "goodbye",
        "take care", "good night"

    ]

    suicide_words = [

        "suicide",
        "kill myself",
        "end my life",
        "self harm",
        "want to die"

    ]

    stress_words = [

        "stress",
        "stressed",
        "pressure",
        "burnout",
        "overwhelmed"

    ]

    anxiety_words = [

        "anxiety",
        "panic",
        "worried",
        "fear",
        "overthinking"

    ]

    depression_words = [

        "sad",
        "depressed",
        "hopeless",
        "lonely",
        "crying",
        "empty"

    ]

    sleep_words = [

        "sleep",
        "insomnia",
        "can't sleep",
        "sleeping"

    ]

    positive_words = [

        "happy",
        "good",
        "great",
        "better",
        "amazing",
        "awesome",
        "cheerful"

    ]

    if lower in greetings:

        greeting_replies = [

            "Hello 🌸\n\nI'm really glad you're here today. How have you been feeling emotionally lately? 💛",

            "Hi there 🌿\n\nYou can talk to me openly about stress, emotions, anxiety, sleep, burnout, studies, work pressure, or anything on your mind 💛",

            "Hey 🌸\n\nI'm here to support your emotional wellbeing and mental wellness. What’s been on your mind lately?"
        ]

        return jsonify({

            "reply":
            random.choice(greeting_replies)

        })

    if any(word in lower for word in goodbye_words):

        goodbye_replies = [

            "Take care of yourself 🌿\n\nRemember that emotional healing takes time. Please rest properly and be gentle with yourself 💛",

            "Goodbye 🌸\n\nI hope you take a few moments for yourself today. Small acts of self-care matter too 💛",

            "See you soon 🌿\n\nPlease remember that your wellbeing matters and you deserve emotional rest too 💖"
        ]

        return jsonify({

            "reply":
            random.choice(goodbye_replies)

        })

    if any(word in lower for word in suicide_words):

        return jsonify({

            "reply":
            "I'm really sorry you're feeling this way 💛\n\n"
            "Please contact someone you trust or a mental health professional immediately.\n\n"
            "📞 Kiran Mental Health Helpline: 1800-599-0019\n"
            "📞 AASRA Suicide Prevention: +91-9820466726\n\n"
            "You are not alone and support is available 🌸"

        })

    if any(word in lower for word in stress_words):

        stress_tips = [

            "• Deep breathing exercises",
            "• Taking structured recovery breaks",
            "• Reducing multitasking",
            "• Drinking enough water",
            "• Journaling thoughts",
            "• Light stretching or walking",
            "• Listening to calming music",
            "• Taking screen breaks",
            "• Prioritizing rest without guilt"
        ]

        random.shuffle(stress_tips)

        return jsonify({

            "reply":
            "It sounds like your mind has been carrying a lot lately 🌿\n\n"
            "Stress can affect concentration, sleep, emotional balance, physical energy, and even motivation.\n\n"
            "Here are some supportive stress recovery techniques:\n\n"
            + "\n".join(stress_tips[:6]) +
            "\n\nWould you like calming exercises, productivity recovery tips, burnout guidance, or sleep improvement suggestions next?"

        })

    if any(word in lower for word in anxiety_words):

        return jsonify({

            "reply":
            "Anxiety can feel mentally exhausting 🌸\n\n"
            "When the nervous system becomes overloaded, thoughts may begin racing and situations can feel overwhelming.\n\n"
            "Grounding techniques that may help:\n\n"
            "• Box breathing\n"
            "• 5-4-3-2-1 grounding method\n"
            "• Reducing overstimulation temporarily\n"
            "• Relaxing shoulders and jaw tension\n"
            "• Focusing on one small step at a time\n"
            "• Avoiding catastrophic thinking\n\n"
            "Would you like calming breathing exercises, sleep relaxation tips, or emotional coping techniques next?"

        })

    if any(word in lower for word in depression_words):

        return jsonify({

            "reply":
            "I'm really sorry you're feeling emotionally exhausted 💛\n\n"
            "Persistent sadness or emotional heaviness can make even simple tasks feel difficult sometimes.\n\n"
            "Gentle self-care approaches that may help:\n\n"
            "• Stay connected to supportive people\n"
            "• Get sunlight and fresh air\n"
            "• Keep tiny manageable goals\n"
            "• Hydrate and eat regularly\n"
            "• Allow yourself emotional rest\n"
            "• Practice self-compassion instead of self-criticism\n\n"
            "If these feelings continue affecting your daily functioning for long periods, speaking with a mental health professional may really help 🌿\n\n"
            "Would you like calming exercises, confidence-building support, or motivation recovery suggestions next?"

        })

    if any(word in lower for word in sleep_words):

        sleep_tips = [

            "• Avoid screens before sleeping",
            "• Reduce caffeine at night",
            "• Keep lights dim before bed",
            "• Listen to calming sounds",
            "• Maintain a fixed sleep schedule",
            "• Try slow breathing while lying down",
            "• Keep your room cool and comfortable",
            "• Avoid heavy meals late at night"
        ]

        random.shuffle(sleep_tips)

        return jsonify({

            "reply":
            "🌙 Sleep difficulties are very common during periods of stress or emotional overload.\n\n"
            "Improving sleep quality may significantly support emotional recovery, focus, and energy.\n\n"
            "Sleep recovery suggestions:\n\n"
            + "\n".join(sleep_tips[:6]) +
            "\n\nWould you like bedtime calming exercises or stress reduction techniques next?"

        })

    if any(word in lower for word in positive_words):

        positive_replies = [

            "That’s genuinely wonderful to hear 🌸✨\n\nPlease continue taking care of your emotional wellbeing and celebrating small positive moments 💛",

            "I'm really happy things are feeling better for you 🌿\n\nPositive moments, even small ones, are important for emotional recovery 💖",

            "That sounds really encouraging 🌸\n\nI hope you continue prioritizing rest, balance, and self-care too 💛"
        ]

        return jsonify({

            "reply":
            random.choice(positive_replies)

        })

    try:

        if model_genai:

            prompt = f"""
            You are Solene,
            an emotionally intelligent AI wellness assistant.

            User message:
            {user_message}

            Respond warmly, supportively, and psychologically intelligently.

            Keep responses emotionally validating.

            Suggest practical coping techniques when appropriate.

            Avoid robotic repetition.

            Make responses feel human, calm, and emotionally supportive.
            """

            response = model_genai.generate_content(
                prompt
            )

            reply = response.text

        else:

            reply = (
                "🌸 I'm here with you.\n\n"
                "Tell me more about what's been on your mind lately 💛"
            )

    except Exception as e:

        print("GEMINI ERROR:", e)

        reply = (
            "🌸 I'm here with you.\n\n"
            "Tell me more about what's been bothering you lately 💛"
        )

    return jsonify({

        "reply": reply

    })

@app.route('/resources')
def resources():

    return render_template(
        'resources.html'
    )

@app.route('/exercises')
def exercises():

    return render_template(
        'exercises.html'
    )

@app.route('/help')
def help_page():

    return render_template(
        'help.html'
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

if __name__ == '__main__':

    app.run(
        debug=True,
        port=5000
    )