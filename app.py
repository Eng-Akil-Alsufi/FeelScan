from flask import Flask, render_template, request, jsonify
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import cv2
import numpy as np
from transformers import pipeline
from textblob import TextBlob
from moviepy.editor import VideoFileClip
from fer import FER  
from transformers.utils import logging
logging.set_verbosity_error()

app = Flask(__name__)


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


model_name = "khaledsoudy/arabic-sentiment-bert-model"
sentiment_pipeline = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name)
label_map = {
    "LABEL_0": "حزن",
    "LABEL_1": "غضب",
    "LABEL_2": "سعادة",
    "LABEL_3": "دهشة",
    "LABEL_4": "خوف",
    "LABEL_5": "محايد"
}


emotion_detector = FER()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
   
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    
    if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        result = analyze_image(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        result = process_text(content)

    return jsonify({'result': result})

@app.route('/scan_text', methods=['POST'])
def scan_text():
    text = request.form.get('text')
    result = process_text(text)
    return jsonify({'result': result})

def analyze_image(image_path):
    
    img = cv2.imread(image_path)
    emotions = emotion_detector.detect_emotions(img)
    
    if emotions:
       
        dominant_emotion = max(emotions[0]['emotions'], key=emotions[0]['emotions'].get)
        confidence = emotions[0]['emotions'][dominant_emotion]
        
        
        emotion_translation = {
            "angry": "غاضب",
            "disgust": "اشمئزاز",
            "fear": "خوف",
            "happy": "سعادة",
            "sad": "حزن",
            "surprise": "دهشة",
            "neutral": "محايد"
        }
        
       
        translated_emotion = emotion_translation.get(dominant_emotion, "غير معروف")
        
        return f"المشاعر السائدة في الصورة هي: '{translated_emotion}' ({dominant_emotion}), مع مستوى ثقة يبلغ {confidence:.2f}."
    else:
        return "لم يتم التعرف على أي مشاعر في الصورة."

def process_text(text):
    if any(char in text for char in 'abcdefghijklmnopqrstuvwxyz'):
        blob = TextBlob(text)
        sentiment = blob.sentiment
        sentiment_value = "إيجابي" if sentiment.polarity > 0 else "سلبي" if sentiment.polarity < 0 else "محايد"
        return f"من خلال تحليل النص، يبدو أن المشاعر تعبر عن شعور {sentiment_value}، مع مستوى ثقة يبلغ {sentiment.subjectivity:.2f}."
    else:
        result = sentiment_pipeline(text)
        label = result[0]['label']
        score = result[0]['score']
        sentiment_label = label_map.get(label, "غير معروف")
        return f"من خلال تحليل النص، يبدو أن المشاعر السائدة هي: '{sentiment_label}'، مع مستوى ثقة يبلغ {score:.2f}."

if __name__ == '__main__':
    app.run(debug=True)