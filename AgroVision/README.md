# AgroVision
# AI-Powered Agricultural Decision Support System

# OVERVIEW

Our Pest and Disease Prediction System is a high-accuracy, AI-powered solution designed to help farmers identify and manage pests and crop diseases effectively. The system achieves a 95% accuracy rate, identifying 8 types of pests and 15 crop diseases. It integrates real-time weather and soil data to provide customized treatment plans and enhance agricultural decision-making. Our model can be used offline, ensuring accessibility even in remote areas.

Plant diseases classes : 
'Pepper__bell___Bacterial_spot',
 'Potato___Early_blight',
 'Potato___Late_blight',
 'Tomato_Bacterial_spot',
 'Tomato_Early_blight',
 'Tomato_Late_blight',
 'Tomato_Leaf_Mold',
 'Tomato_Septoria_leaf_spot',
 'Tomato_Spider_mites_Two_spotted_spider_mite',
 'Tomato__Target_Spot',
 'Tomato__Tomato_YellowLeaf__Curl_Virus',
 'Tomato__Tomato_mosaic_virus',

Pest classes : 
 'aphids',
 'armyworm',
 'beetle',
 'bollworm',
 'grasshopper',
 'mites',
 'mosquito',
 'sawfly',
 'stem_borer'

we are working on other datasets ....


# FEATURES

# 🌱 AI-Powered Pest & Disease Identification

Uses a fine-tuned custom MobileNetV2 model, optimized for transfer learning.

Identifies 8 pests and 15 crop diseases with 95% accuracy.

Works offline, enabling farmers to diagnose issues without an internet connection.

# 📊 Customized Treatment Plans

Provides AI-generated treatment recommendations based on:

10-day weather forecasts from the OpenWeather API.

Soil pH and moisture data from NASA's API with 99% accuracy.

Gemini API for pest and disease treatment plans.

Dynamically updates based on real-time weather and soil conditions.

# 👨‍🌾 Farmer Community Portal

Facilitates resource sharing, group discussions, and collaboration.

Encourages knowledge exchange between farmers.

# 🤖 Multilingual Chatbot

Assists farmers with agricultural queries.

Supports Tamil and Telugu for regional accessibility.

Powered by a third-party chatbot using Zapier.

# 📜 Government Scheme Portal

Provides a comprehensive listing of government schemes for farmers.

Helps farmers access financial aid and support programs.

# 📱 Offline Mobile-Friendly Web Application

Designed with HTML and Tailwind CSS for efficiency and responsiveness.

Can be accessed offline, ensuring availability even in remote areas.

# TECH STACK

# Frontend:
 HTML, Tailwind CSS

# Backend: 
Django Framework

# Machine Learning Model: 
Fine-tuned custom MobileNetV2 (Transfer Learning for pest and disease detection)

# APIs Used:
OpenWeather API (Weather Forecasts)

NASA API (Soil pH and Moisture Data with 99% accuracy)

Gemini API (Pest and Disease Treatment Plans)

Third-party chatbot using Zapier

# INSTALLATION AND SETUP

# Clone the repository
git clone https://github.com/Stephen13-05/AgroVision.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Run the Django server
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

Your backend will be live at: http://127.0.0.1:8000/

🔗 API Keys Setup
You need API keys for OpenWeather, NASA, and Gemini APIs.

1️⃣ Obtain API Keys

OpenWeather API – For weather forecasts.
NASA API – For soil pH & moisture data.
Gemini API – For AI-generated treatment plans.

2️⃣ Add API Keys to Environment Variables

Create a .env file in the project root and add:

OPENWEATHER_API_KEY=your_openweather_api_key
NASA_API_KEY=your_nasa_api_key
GEMINI_API_KEY=your_gemini_api_key


# Usage Guide

1️⃣ Detect Pests & Diseases
📸 Upload a photo of the affected crop → ✅ AI predicts the issue offline.

2️⃣ Get Treatment Plans
🧪 AI suggests treatment based on weather & soil data.

3️⃣ Check Weather & Soil Data
🌦 Get real-time weather updates & 99% accurate soil pH/moisture data.

4️⃣ Join Farmer Community
👨‍🌾 Discuss & share knowledge with other farmers.

5️⃣ Use the AI Chatbot
🤖 Ask farming questions in Tamil or Telugu → Get instant answers.

6️⃣ Find Government Schemes
📜 Browse & apply for farming subsidies and support programs.

7️⃣ Offline Web App
📱 Use the app anytime, anywhere – no internet needed!



🌱 Boost crop health & prevent losses with AI-powered farming! 🚜

It is the output of the 36 hr hackathon held at # IIIT Sricity ABHISARG 25















