from flask import Flask, render_template, request
from flask_socketio import SocketIO, send
import openai
import os
import pandas as pd
import difflib
from langdetect import detect
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app)

#OpenAI API key
openai.api_key = ''

# Load the Excel files
faq_df_en = pd.read_excel('C:/Users/HI/.spyder-py3/chatbot/Web Praxis Help_FAQ.el.en.xlsx')
faq_df_gr = pd.read_excel('C:/Users/HI/.spyder-py3/chatbot/Web Praxis Help_FAQ.xlsx')
video_info_df_en = pd.read_excel('C:/Users/HI/.spyder-py3/chatbot/Web Praxis Help - Videos.el.en.xlsx')
video_info_df_gr = pd.read_excel('C:/Users/HI/.spyder-py3/chatbot/Web Praxis Help - Videos.xlsx')
chapters_df_en = pd.read_excel('C:/Users/HI/.spyder-py3/chatbot/Web Praxis Help_ Chaptres.el.en.xlsx')
chapters_df_gr = pd.read_excel('C:/Users/HI/.spyder-py3/chatbot/Web Praxis Help_ Chaptres.xlsx')

def find_similar_descriptions(user_input, lang):
    df = video_info_df_en if lang == 'en' else video_info_df_gr
    column_name = 'Description' if lang == 'en' else 'Περιγραφή'
    ratios = df[column_name].apply(lambda x: difflib.SequenceMatcher(None, x, user_input).ratio())
    max_ratio = max(ratios)
    similar_descriptions = df[ratios == max_ratio]
    return similar_descriptions

def find_similar_faq(user_input, lang):
    faq_df = faq_df_en if lang == 'en' else faq_df_gr
    question_col = 'Question' if lang == 'en' else 'Ερώτηση'
    answer_col = 'Answer' if lang == 'en' else 'Απάντηση'
    ratios = faq_df[question_col].apply(lambda x: difflib.SequenceMatcher(None, x, user_input).ratio())
    max_ratio = max(ratios)
    similar_faq = faq_df[ratios == max_ratio]
    return similar_faq

def find_similar_chapter(user_input, lang):
    chapters_df = chapters_df_en if lang == 'en' else chapters_df_gr
    column_title = 'Capital Title' if lang == 'en' else 'Κεφαλαιογράμματος Τίτλος'
    column_description = 'Chapter Description' if lang == 'en' else 'Περιγραφή Κεφαλαίου'
    ratios = chapters_df[column_title].apply(lambda x: difflib.SequenceMatcher(None, x, user_input).ratio())
    max_ratio = max(ratios)
    similar_chapter = chapters_df[ratios == max_ratio]
    return similar_chapter


def get_chat_gpt_response(prompt, lang):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.6
    )
    return response.choices[0].message.content.strip()

def get_chapter_description(user_input, lang):
    df = chapters_df_en if lang == 'en' else chapters_df_gr
    column_title = 'Capital Title' if lang == 'en' else 'Κεφαλαιογράμματος Τίτλος'
    column_description = 'Chapter Description' if lang == 'en' else 'Περιγραφή Κεφαλαίου'
    df['similarity'] = df[column_title].apply(lambda x: difflib.SequenceMatcher(None, x, user_input).ratio())
    max_similarity = df['similarity'].max()
    if max_similarity > 0.5:
        description = df.loc[df['similarity'].idxmax(), column_description]
        return description
    return "Title not found." if lang == 'en' else "Δεν βρέθηκε τίτλος."

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handleMessage(msg):
    logging.debug(f"Received message: {msg}")
    
    # Detect language
    try:
        lang = detect(msg)
        logging.debug(f"Detected language: {lang}")
    except Exception as e:
        logging.error(f"Error detecting language: {e}")
        lang = 'en'  # Default to English if detection fails

    # Send the user's question immediately
    send({'messages': [{'role': 'user', 'content': msg}]}, broadcast=True)
    
    # Generate responses
    similar_descriptions = find_similar_descriptions(msg, lang)
    chat_gpt_response = get_chat_gpt_response(msg, lang)
    similar_faq = find_similar_faq(msg, lang)
    similar_chapter = find_similar_chapter(msg, lang)
    
    video_links = []
    for _, row in similar_descriptions.iterrows():
        description = row['Description'] if lang == 'en' else row['Περιγραφή']
        title = row['Title'] if lang == 'en' else row['Τίτλος']
        video_links.append({
            'description': description,
            'video_link': row['YouTube Code'],
            'title': title
        })
    
    faq_answer = None
    if not similar_faq.empty:
        faq_answer = similar_faq.iloc[0]['Answer' if lang == 'en' else 'Απάντηση']
    
    chapter_description = None
    if not similar_chapter.empty:
        chapter_description = similar_chapter.iloc[0]['Chapter Description' if lang == 'en' else 'Περιγραφή Κεφαλαίου']

    response_messages = []
    
    if chat_gpt_response:
        response_messages.append({'role': 'bot', 'content': chat_gpt_response})
    
    if faq_answer:
        response_messages.append({'role': 'bot', 'content': 'According to Praxis:' if lang == 'en' else 'Σύμφωνα με την Πράξη:'})
        response_messages.append({'role': 'bot', 'content': faq_answer})
    
    if chapter_description:
        response_messages.append({'role': 'bot', 'content': 'According to Praxis:' if lang == 'en' else 'Σύμφωνα με την Πράξη:'})
        response_messages.append({'role': 'bot', 'content': chapter_description})

    if video_links:
        response_messages.append({'role': 'bot', 'content': 'Related Videos:' if lang == 'en' else 'Σχετικά Βίντεο:'})
        for item in video_links:
            response_messages.append({
                'role': 'bot',
                'content': f'Description: {item["description"]}'
                           f'<p><a href="#" class="video-link" data-link="https://www.youtube.com/embed/{item["video_link"]}">Click Here to Watch</a></p>'
                           f'<p>Title: {item["title"]}</p>'
            })
    
    # Send the bot's responses
    send({'messages': response_messages}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)