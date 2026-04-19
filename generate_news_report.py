import google.genai as genai
from google.cloud import texttospeech
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = EMAIL_SENDER

GENRES = {
    "GENERAL_NEWS": {
        "style": "calm, informative, focused on major world events",
        "articles": [
            "https://feeds.bbci.co.uk/news/world/rss.xml",       
            "https://www.reuters.com/world/",                   
            "https://www.tagesschau.de/infoservices/alle-feeds" 
        ]
    },
    "TECH": {
        "style": "slightly more energetic, modern, clear explanations",
        "articles": [
            "https://news.ycombinator.com/",    
            "https://techcrunch.com/",                
            "https://medium.com/topic/technology",
            "https://www.coindesk.com/",
            "https://cointelegraph.com/"
        ]
    }
}

# ---------------- GENERATE NEWS ----------------

def generate_news(genre, articles):
    config = GENRES[genre]

    formatted_articles = "\n".join(f"- {url}" for url in articles)

    prompt = f"""
You are a professional morning news anchor.

Create a {genre.replace('_', ' ').lower()} briefing. Start with hello everyone and just give out the news report as text. No scenery, no extra no nothing

STYLE:
- Conversational, human, and smooth
- {config['style']}
- Sounds natural when spoken aloud

STRUCTURE:
- Short intro
- 2-3 minutes long
- Smooth transitions
- Short closing

RULES:
- No bullet points
- No repetition
- No "in summary"
- Optimize for speech

ARTICLES:
{formatted_articles}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    return response.text

# ---------------- TEXT TO SPEECH ----------------

def generate_audio(text, genre):
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )

    filename = f"{genre.lower()}.mp3"

    with open(filename, "wb") as f:
        f.write(response.audio_content)

    return filename

# ---------------- EMAIL ----------------

def send_email(files):
    msg = EmailMessage()
    msg["Subject"] = "Your Daily News Briefing"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    msg.set_content("Your daily news briefings are attached 🎧")

    for file in files:
        with open(file, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="audio",
                subtype="mpeg",
                filename=file
            )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ---------------- MAIN ----------------

def main():
    audio_files = []

    for genre, config in GENRES.items():
        print(f"Processing {genre}...")

        news_text = generate_news(genre, config["articles"])
        audio_file = generate_audio(news_text, genre)

        audio_files.append(audio_file)

    send_email(audio_files)

    # Optional cleanup
    for file in audio_files:
        os.remove(file)

    print("Done!")

# ---------------- RUN ----------------

if __name__ == "__main__":
    main()