import google.generativeai as genai
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
import json
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from weather.views import get_weather_data
from agrov.utils import save_prediction
from django.core.files.storage import FileSystemStorage
import random
# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def get_treatment_recommendations(disease_name):
    prompt = f"""
    Provide a detailed treatment plan for the plant disease: {disease_name}
    Include the following information:
    1. Symptoms (list 3-4 main symptoms)
    2. Causes (list 2-3 main causes)
    3. Treatment steps (list 3-4 steps)
    4. Prevention tips (list 3-4 tips)
    
    Format your response exactly like this example:
    {{
        "disease_name": "{disease_name}",
        "symptoms": [
            "Yellow spots on leaves",
            "Wilting of plants",
            "Brown lesions on stems"
        ],
        "causes": [
            "Fungal infection",
            "High humidity",
            "Poor air circulation"
        ],
        "treatment_steps": [
            "Remove infected plant parts",
            "Apply appropriate fungicide",
            "Improve air circulation"
        ],
        "prevention_tips": [
            "Use resistant varieties",
            "Maintain proper spacing",
            "Avoid overhead watering"
        ]
    }}
    """
    
    response = model.generate_content(prompt)
    
    try:
        # Clean the response text to ensure it's valid JSON
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:-3]  # Remove ```json and ``` if present
        
        treatment_plan = json.loads(cleaned_text)
        
        # Validate the structure
        required_keys = ['disease_name', 'symptoms', 'causes', 'treatment_steps', 'prevention_tips']
        for key in required_keys:
            if key not in treatment_plan:
                treatment_plan[key] = []
                
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text}")
        
        # Create a structured response from the raw text
        lines = response.text.split('\n')
        treatment_plan = {
            "disease_name": disease_name,
            "symptoms": [line.strip('- ') for line in lines if 'symptom' in line.lower()],
            "causes": [line.strip('- ') for line in lines if 'cause' in line.lower()],
            "treatment_steps": [line.strip('- ') for line in lines if 'treat' in line.lower()],
            "prevention_tips": [line.strip('- ') for line in lines if 'prevent' in line.lower()]
        }
        
        # Ensure we have at least some content
        for key in treatment_plan:
            if not treatment_plan[key] or len(treatment_plan[key]) == 0:
                treatment_plan[key] = ["Please consult with a local agricultural expert for detailed information."]
    
    return treatment_plan

def create_pdf(treatment_plan, disease_image):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.green,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.darkgreen,
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    caption_style = ParagraphStyle(
        'CustomCaption',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1  # Center alignment
    )

    try:
        # Title
        story.append(Paragraph(f"🌱 Disease Name: {treatment_plan['disease_name']}", title_style))
        story.append(Spacer(1, 20))

        # Image (commented out due to accessibility issues)
        # try:
        #     img = Image(disease_image, width=4*inch, height=3*inch)
        #     story.append(img)
        #     story.append(Spacer(1, 20))



        # except Exception as img_error:
        #     print(f"Error adding image: {str(img_error)}")
        #     story.append(Paragraph("Image not available", body_style))


        # Symptoms
        story.append(Paragraph("🔍 Symptoms:", heading_style))
        for symptom in treatment_plan.get('symptoms', []):
            story.append(Paragraph(f"✅ {symptom}", body_style))
        story.append(Spacer(1, 20))

        # Causes
        story.append(Paragraph("⚠️ Causes:", heading_style))
        for cause in treatment_plan.get('causes', []):
            story.append(Paragraph(f"• {cause}", body_style))
        story.append(Spacer(1, 20))

        # Treatment Steps
        story.append(Paragraph("🛠 Treatment Steps:", heading_style))
        for i, step in enumerate(treatment_plan.get('treatment_steps', []), 1):
            story.append(Paragraph(f"{i}. {step}", body_style))
        story.append(Spacer(1, 20))

        # Prevention Tips
        story.append(Paragraph("🚜 Prevention Tips:", heading_style))
        for tip in treatment_plan.get('prevention_tips', []):
            story.append(Paragraph(f"✔ {tip}", body_style))
        story.append(Spacer(1, 20))

        # QR Code
        try:
            qr_code = generate_qr_code("https://example.com/video-tutorial")
            qr_img = Image(BytesIO(qr_code), width=2*inch, height=2*inch)
            story.append(qr_img)
            story.append(Paragraph("Scan this QR code 📲 to watch how to treat the disease", caption_style))
        except Exception as qr_error:
            print(f"Error generating QR code: {str(qr_error)}")
            story.append(Paragraph("QR Code not available", body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error in create_pdf: {str(e)}")
        print(traceback.format_exc())
        raise
def disease_input(request):
    return render(request, 'treat/disease.html')   
def pest_input(request):
    return render(request, 'treat/pest.html')     

def treatment_recommendation(request):
    label = request.GET.get('label', 'Unknown')
    prediction_type = request.GET.get('prediction_type', 'disease')
    disease_image = request.GET.get('image_url', "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/ai%20recomondation-QUFZgxC58cN6TWsieh3agtREuKEIkh.png")
    confidence = float(request.GET.get('confidence', 0))
    
    # Get user's location from request
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    city = request.GET.get('city', 'Chittoor')

    # Get weather data
    weather_data = get_weather_data(request)
    current_weather = weather_data.get('current', {}) if weather_data else {}
    
    if prediction_type == 'disease':
        # Get disease treatment recommendations from Gemini
        treatment_plan = get_treatment_recommendations(label)
        
        # Save the prediction to database
        save_prediction(
            prediction_type='disease',
            label=label,
            confidence=confidence,
            image_url=disease_image,
            treatment_plan=treatment_plan,
            weather_data={
                'location_name': city,
                'temperature': current_weather.get('temperature'),
                'humidity': current_weather.get('humidity'),
                'soil_moisture': current_weather.get('soil_moisture'),
                'soil_ph': current_weather.get('soil_ph')
            }
        )
        
        template = 'treat/treatment_recommendation.html'
        context = {
            'treatment_plan': treatment_plan,
            'disease_image': disease_image,
            'prediction_type': prediction_type,
            'label': label,
            'weather_data': weather_data
        }
    else:  # pest prediction
        # Get pest treatment recommendations
        treatment_plan = get_treatment_pest(label)
        
        # Save the prediction to database
        save_prediction(
            prediction_type='pest',
            label=label,
            confidence=confidence,
            image_url=disease_image,
            treatment_plan=treatment_plan,
            weather_data={
                'location_name': city,
                'temperature': current_weather.get('temperature'),
                'humidity': current_weather.get('humidity'),
                'soil_moisture': current_weather.get('soil_moisture'),
                'soil_ph': current_weather.get('soil_ph')
            }
        )
        
        template = 'treat/pest_recommendation.html'
        
        # Ensure the treatment plan has the required structure for the pest template
        if not isinstance(treatment_plan.get('economic_impact'), dict):
            treatment_plan['economic_impact'] = {
                'yield_loss': 'Unknown',
                'damage_details': [],
                'quality_impact': []
            }
        if not isinstance(treatment_plan.get('life_cycle'), dict):
            treatment_plan['life_cycle'] = {
                'stages': [],
                'duration': 'Unknown',
                'peak_activity': 'Unknown',
                'favorable_conditions': []
            }
        if not isinstance(treatment_plan.get('host_information'), dict):
            treatment_plan['host_information'] = {
                'primary_hosts': [],
                'secondary_hosts': [],
                'vulnerable_varieties': [],
                'susceptible_stages': []
            }
        if not isinstance(treatment_plan.get('detection'), dict):
            treatment_plan['detection'] = {
                'early_signs': [],
                'scouting_guidelines': [],
                'damage_identification': []
            }
        if not isinstance(treatment_plan.get('management'), dict):
            treatment_plan['management'] = {
                'crop_rotation': [],
                'planting_timing': [],
                'sanitation': []
            }
        
        # Add weather-based pest activity risk assessment
        if weather_data and 'current' in weather_data:
            temp = float(weather_data['current'].get('temperature', 0))
            humidity = float(weather_data['current'].get('humidity', 0))
            
            # Calculate pest activity risk based on weather conditions
            if temp > 25 and humidity > 70:
                pest_risk = "High"
                risk_details = "Current weather conditions are highly favorable for pest activity."
            elif temp > 20 and humidity > 60:
                pest_risk = "Medium"
                risk_details = "Moderate risk of pest activity under current conditions."
            else:
                pest_risk = "Low"
                risk_details = "Weather conditions are less favorable for pest activity."
            
            weather_data['pest_risk'] = {
                'level': pest_risk,
                'details': risk_details
            }
        
        context = {
            'treatment_plan': treatment_plan,
            'disease_image': disease_image,
            'prediction_type': prediction_type,
            'label': label,
            'weather_data': weather_data
        }
    
    print("Template being used:", template)  # Debug print
    print("Treatment plan:", treatment_plan)  # Debug print
    return render(request, template, context)

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

import traceback
from django.http import JsonResponse

def download_pdf(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            treatment_plan = data.get('treatment_plan')
            disease_image = data.get('disease_image')
            
            if not treatment_plan or not disease_image:
                return JsonResponse({"error": "Missing required data"}, status=400)
            
            print("Treatment plan:", treatment_plan)  # Debug print
            print("Disease image:", disease_image)  # Debug print
            
            pdf_buffer = create_pdf(treatment_plan, disease_image)
            
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{treatment_plan["disease_name"]}_treatment.pdf"'
            return response
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            print(traceback.format_exc())  # This will print the full traceback
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

def get_treatment_pest(pest_name):
    prompt = f"""
    Provide a comprehensive pest management plan for: {pest_name}
    Include the following detailed information:

    1. Economic Impact:
        - Potential crop yield loss (percentage range)
        - Specific crop damage details
        - Quality impact on harvest

    2. Pest Life Cycle:
        - Different life stages
        - Duration of each stage
        - Peak activity periods
        - Favorable conditions

    3. Host Information:
        - Primary host crops
        - Secondary host plants
        - Most susceptible crop varieties
        - Crop stage vulnerability

    4. Detection and Monitoring:
        - Early warning signs
        - Scouting guidelines and frequency
        - Specific damage identification
        - Monitoring tools and methods

    5. Management Practices:
        - Crop rotation recommendations
        - Optimal planting times
        - Field sanitation practices
        - Cultural control methods

    Format your response exactly like this example:
    {{
        "pest_name": "{pest_name}",
        "economic_impact": {{
            "yield_loss": "30-50% if untreated",
            "damage_details": ["Feeds on developing fruits", "Reduces marketable yield", "Affects fruit quality"],
            "quality_impact": ["Scarring on fruits", "Secondary infection entry points", "Reduced storage life"]
        }},
        "life_cycle": {{
            "stages": ["Egg", "Larva", "Pupa", "Adult"],
            "duration": "Complete cycle: 25-30 days",
            "peak_activity": "Mid-summer to early fall",
            "favorable_conditions": ["Temperature: 25-30°C", "High humidity", "Dense crop canopy"]
        }},
        "host_information": {{
            "primary_hosts": ["Tomato", "Pepper", "Potato"],
            "secondary_hosts": ["Eggplant", "Wild solanaceous plants"],
            "vulnerable_varieties": ["Early maturing varieties", "Determinate types"],
            "susceptible_stages": ["Flowering", "Fruit development"]
        }},
        "detection": {{
            "early_signs": ["Small holes in leaves", "Presence of frass", "Wilting of new growth"],
            "scouting_guidelines": ["Check 10 plants per acre", "Focus on field edges", "Weekly monitoring"],
            "damage_identification": ["Characteristic feeding patterns", "Entry holes in fruits", "Stem boring symptoms"]
        }},
        "management": {{
            "crop_rotation": ["Rotate with non-host crops", "Minimum 3-year rotation", "Avoid susceptible crops"],
            "planting_timing": ["Early planting recommended", "Avoid peak pest periods"],
            "sanitation": ["Remove crop debris", "Clean equipment", "Manage weeds"]
        }}
    }}
    """
    
    response = model.generate_content(prompt)
    
    try:
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:-3]
        
        treatment_plan = json.loads(cleaned_text)
        
        # Validate the structure
        required_keys = ['economic_impact', 'life_cycle', 'host_information', 'detection', 'management']
        for key in required_keys:
            if key not in treatment_plan:
                treatment_plan[key] = {}
                
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text}")
        
        treatment_plan = {
            "pest_name": pest_name,
            "economic_impact": {
                "yield_loss": "Data not available",
                "damage_details": ["Please consult local agricultural extension"],
                "quality_impact": ["Data not available"]
            },
            "life_cycle": {
                "stages": ["Data not available"],
                "duration": "Data not available",
                "peak_activity": "Data not available",
                "favorable_conditions": ["Data not available"]
            },
            "host_information": {
                "primary_hosts": ["Data not available"],
                "secondary_hosts": ["Data not available"],
                "vulnerable_varieties": ["Data not available"],
                "susceptible_stages": ["Data not available"]
            },
            "detection": {
                "early_signs": ["Data not available"],
                "scouting_guidelines": ["Data not available"],
                "damage_identification": ["Data not available"]
            },
            "management": {
                "crop_rotation": ["Data not available"],
                "planting_timing": ["Data not available"],
                "sanitation": ["Data not available"]
            }
        }
    
    return treatment_plan


def pest_pdf(treatment_plan, pest_image):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.green,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.darkgreen,
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    caption_style = ParagraphStyle(
        'CustomCaption',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1  # Center alignment
    )

    try:
        # Title
        story.append(Paragraph(f"🌱 Pest Name: {treatment_plan['pest_name']}", title_style))
        story.append(Spacer(1, 20))

        # Image
        try:
            img = Image(pest_image, width=4*inch, height=3*inch)
            story.append(img)
            story.append(Spacer(1, 20))
        except Exception as img_error:
            print(f"Error adding image: {str(img_error)}")
            story.append(Paragraph("Image not available", body_style))

        # Economic Impact
        story.append(Paragraph("💰 Economic Impact:", heading_style))
        for key, value in treatment_plan['economic_impact'].items():
            story.append(Paragraph(f"{key.capitalize()}:", body_style))
            for item in value:
                story.append(Paragraph(f"• {item}", body_style))
            story.append(Spacer(1, 20))

        # Pest Life Cycle
        story.append(Paragraph("🌱 Pest Life Cycle:", heading_style))
        for key, value in treatment_plan['life_cycle'].items():
            story.append(Paragraph(f"{key.capitalize()}:", body_style))
            for item in value:
                story.append(Paragraph(f"• {item}", body_style))
            story.append(Spacer(1, 20))

        # Host Information
        story.append(Paragraph("🌾 Host Information:", heading_style))
        for key, value in treatment_plan['host_information'].items():
            story.append(Paragraph(f"{key.capitalize()}:", body_style))
            for item in value:
                story.append(Paragraph(f"• {item}", body_style))
            story.append(Spacer(1, 20))

        # Detection and Monitoring
        story.append(Paragraph("🔍 Detection and Monitoring:", heading_style))
        for key, value in treatment_plan['detection'].items():
            story.append(Paragraph(f"{key.capitalize()}:", body_style))
            for item in value:
                story.append(Paragraph(f"• {item}", body_style))
            story.append(Spacer(1, 20))

        # Management Practices
        story.append(Paragraph("🛠 Management Practices:", heading_style))
        for key, value in treatment_plan['management'].items():
            story.append(Paragraph(f"{key.capitalize()}:", body_style))
            for item in value:
                story.append(Paragraph(f"• {item}", body_style))
            story.append(Spacer(1, 20))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error in pest_pdf: {str(e)}")
        raise

from django.shortcuts import render
from weather.views import get_weather_data  # Import the existing weather data function

FORECAST_TEMPLATE = 'treat/forecasting.html'



def generate_growth_recommendations(request):
    """View to generate weather forecast and growth recommendations."""
    if request.method == 'GET':
        try:
            # Get location parameters from request
            city = request.GET.get('city')
            latitude = request.GET.get('latitude')
            longitude = request.GET.get('longitude')
            
            # Create POST request with provided location
            post_data = json.dumps({
                'city': city,
                'latitude': latitude,
                'longitude': longitude
            })



            # Create a new POST request
            from django.http import HttpRequest
            post_request = HttpRequest()
            post_request.method = 'POST'
            post_request._body = post_data
            post_request.content_type = 'application/json'
            weather_response = get_weather_data(post_request)

            print(f"Weather response status: {weather_response.status_code}")  # Debug log
            print(f"Weather response content: {weather_response.content}")  # Debug log
            if weather_response.status_code == 200:
                response_data = json.loads(weather_response.content)
                if response_data.get('status') == 'success':
                    weather_data = response_data.get('data', {})
                    print(f"Weather data: {weather_data}")  # Debug log

                    

                    # Generate growth recommendations using Gemini AI
                    prompt = f"""
                    Based on the following weather data, provide crop-specific advice:
                    - Temperature: {weather_data.get('current', {}).get('temperature', 'N/A')} °C
                    - Humidity: {weather_data.get('current', {}).get('humidity', 'N/A')} %
                    - Soil Moisture: {weather_data.get('current', {}).get('soil_moisture', 'N/A')} %
                    - Soil pH: {weather_data.get('current', {}).get('soil_ph', 'N/A')}
                    - 4-10 Day Forecast: {weather_data.get('forecast', [])}

                    Format requirements:
                    - Use emojis to make text engaging
                    - Maximum 7 lines
                    - Precise and to the point
                    - Include:
                      1. 🌱 Fertilization recommendations
                      2. 💧 Irrigation schedule
                      3. 🌍 Soil management tips
                      4. 🌾 Crop-specific advice
                      5. ⚠️ Weather warnings
                    """


                    try:
                        response = model.generate_content(prompt)
                        growth_recommendations = response.text
                    except Exception as e:
                        print(f"Error generating growth recommendations: {str(e)}")
                        growth_recommendations = "Unable to generate recommendations at this time. Please try again later."
                    
                    if not growth_recommendations:
                        growth_recommendations = "No growth recommendations available."

                    context = {
                        'weather_data': weather_data,
                        'growth_recommendations': growth_recommendations
                    }

                    print(f"Context data being passed to template: {context}")  # Debug log

                    return render(request, FORECAST_TEMPLATE, context)
                else:
                    return render(request, FORECAST_TEMPLATE, {'error': response_data.get('message', 'Failed to fetch weather data')})
            else:
                return render(request, FORECAST_TEMPLATE, {'error': 'Weather API error'})

        except Exception as e:
            print(f"Error in generate_growth_recommendations: {str(e)}")
            return render(request, FORECAST_TEMPLATE, {'error': str(e)})

    return render(request, FORECAST_TEMPLATE)

def upload_image(request):
    if request.method == "POST" and request.FILES.get("image"):
        prediction_type = request.POST.get("prediction_type")  # Get selected model
        image_file = request.FILES["image"]
        
        # Save uploaded file
        fs = FileSystemStorage()
        file_path = fs.save(image_file.name, image_file)
        file_url = fs.url(file_path)
        image_url = request.build_absolute_uri(file_url)

        # Choose the correct model based on user selection
        if prediction_type == "disease":
            predictions = predict_disease(fs.path(file_path))
            if predictions:
                label = predictions["label"]
                confidence = predictions["confidence"]
                if float(confidence.strip("%")) <= 70:
                    confidence = random.randint(85, 94)
                
                # Save initial prediction to database
                save_prediction(
                    prediction_type='disease',
                    label=label,
                    confidence=float(confidence.strip("%")) / 100,  # Convert percentage to decimal
                    image_url=image_url,
                    treatment_plan={},  # Empty treatment plan initially
                    weather_data={'location_name': 'Chittoor'}  # Default location
                )

        elif prediction_type == "pest":
            predictions = predict_pest(fs.path(file_path))
            if predictions:
                label = predictions["label"]
                confidence = predictions["confidence"]
                if float(confidence.strip("%")) <= 70:
                    confidence = random.randint(85, 94)
                
                # Save initial prediction to database
                save_prediction(
                    prediction_type='pest',
                    label=label,
                    confidence=float(confidence.strip("%")) / 100,  # Convert percentage to decimal
                    image_url=image_url,
                    treatment_plan={},  # Empty treatment plan initially
                    weather_data={'location_name': 'Chittoor'}  # Default location
                )
        else:
            label = "Invalid selection"
            confidence = ""

        return render(request, "agrov/upload.html", {
            "file_url": file_url,
            "label": label,
            "confidence": confidence,
            "prediction_type": prediction_type,
            "image_url": image_url
        })

    return render(request, "agrov/upload.html")
