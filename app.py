import streamlit as st
import requests
import sqlite3
from datetime import datetime
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import base64

# Database setup
conn = sqlite3.connect('recipes.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredients TEXT,
    recipe TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()

# Spoonacular API key
API_KEY = "9714989c384a4a5595583c90db947"

# Recipe fetch function
def fetch_recipe_from_spoonacular(ingredients):
    base_url = "https://api.spoonacular.com/recipes/findByIngredients"
    info_url = "https://api.spoonacular.com/recipes/{id}/information"

    try:
        response = requests.get(base_url, params={
            "ingredients": ingredients,
            "number": 1,
            "apiKey": API_KEY
        })

        if response.status_code == 200 and response.json():
            recipe_data = response.json()[0]
            recipe_id = recipe_data["id"]

            full_info = requests.get(info_url.format(id=recipe_id), params={"apiKey": API_KEY}).json()
            title = full_info.get("title", "Unknown Recipe")
            instructions = full_info.get("instructions", "Instructions not available.")
            image_url = full_info.get("image", "")
            return title, instructions, image_url
        else:
            return None, "No matching recipe found.", None
    except Exception as e:
        return None, f"Error: {e}", None

# Translation function
def translate_to_malayalam(text):
    try:
        return GoogleTranslator(source='auto', target='ml').translate(text)
    except Exception as e:
        print("Translation error:", e)
        return text

# Voice function with HTML audio player (for Streamlit Cloud)
def speak_text(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            audio_path = fp.name

        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            b64 = base64.b64encode(audio_bytes).decode()

        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Voice error: {e}")

# Streamlit UI
st.set_page_config(page_title="Pachakapura", layout="centered")

# Style
st.markdown("""
<style>
.title-animated {
    text-align: center;
    font-size: 2.2rem;
    font-weight: bold;
    background: linear-gradient(270deg, #ff6ec4, #7873f5, #48c6ef);
    background-size: 600% 600%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientAnimation 6s ease infinite;
    font-family: 'Segoe UI', sans-serif;
    margin-bottom: 1rem;
}
@keyframes gradientAnimation {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.chat-box {
    background-color: #e1ffc7;
    padding: 12px 18px;
    border-radius: 18px;
    margin-bottom: 10px;
    max-width: 75%;
    align-self: flex-end;
    margin-left: auto;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    font-size: 16px;
    font-family: 'Segoe UI', sans-serif;
    line-height: 1.4;
    word-wrap: break-word;
    color: black;
}
.bot-box {
    background-color: #ffffff;
    padding: 12px 18px;
    border-radius: 18px;
    margin-bottom: 10px;
    max-width: 75%;
    align-self: flex-start;
    margin-right: auto;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    font-size: 16px;
    font-family: 'Segoe UI', sans-serif;
    line-height: 1.4;
    word-wrap: break-word;
    color: black;
}
img {
    border-radius: 10px;
    margin-top: 10px;
}
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<div class='title-animated'>PACHAKAPURA</div>", unsafe_allow_html=True)
st.markdown("Enter the ingredients you have, and I’ll suggest a recipe for you!")

# Input
language = st.selectbox("🌐 Choose Language", ["English", "Malayalam"])
raw_ingredients = st.text_input("🍅 Ingredients (comma-separated)")
ingredients = ','.join(i.strip().lower() for i in raw_ingredients.split(',') if i.strip())

# Button
if st.button("📤 Send") and ingredients:
    with st.spinner("Typing..."):
        title, instructions, image_url = fetch_recipe_from_spoonacular(ingredients)
        if title:
            speak_lang = 'ml' if language == "Malayalam" else 'en'
            if language == "Malayalam":
                title = translate_to_malayalam(title)
                instructions = translate_to_malayalam(instructions)

            st.markdown(f"<div class='chat-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='chat-box'><b>You:</b><br>{ingredients}</div>", unsafe_allow_html=True)
            bot_reply = f"<b>{title}</b><br>"
            if image_url:
                bot_reply += f"<img src='{image_url}' width='100%'><br>"
            bot_reply += f"{instructions}"
            st.markdown(f"<div class='bot-box'><b>🤖 BOT:</b><br>{bot_reply}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            speak_text(f"{title}. {instructions}", lang=speak_lang)

            cursor.execute("INSERT INTO recipes (ingredients, recipe) VALUES (?, ?)", (ingredients, title + ": " + instructions))
            conn.commit()
        else:
            st.warning(instructions)

# History
if st.checkbox("📜 Show previous recipes"):
    st.markdown("### 🕒 Recipe History")
    rows = cursor.execute("SELECT ingredients, recipe, date FROM recipes ORDER BY id DESC LIMIT 5").fetchall()
    for ingredients, recipe, date in rows:
        st.markdown(f"<div class='bot-box'><b>{date}</b><br><b>You:</b> {ingredients}<br><b>Recipe:</b> {recipe}</div>", unsafe_allow_html=True)

st.markdown("<div style='text-align:center; color:#666; margin-top: 30px;'>© 2025 | Published by Aju Krishna</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
