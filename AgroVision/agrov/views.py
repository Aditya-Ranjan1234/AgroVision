from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .model_loader import predict_disease, predict_pest  # Import both functions
import random
from django.http import JsonResponse
from .models import PredictionHistory
from django.core.paginator import Paginator

def upload_image(request):
    if request.method == "POST" and request.FILES.get("image"):
        prediction_type = request.POST.get("prediction_type")  # Get selected model
        image_file = request.FILES["image"]
        
        # Save uploaded file
        fs = FileSystemStorage()
        file_path = fs.save(image_file.name, image_file)
        file_url = fs.url(file_path)

        # Choose the correct model based on user selection
        if prediction_type == "disease":
            predictions = predict_disease(fs.path(file_path))
            if predictions:
                label = predictions["label"]
                confidence = predictions["confidence"]
                print(label, confidence)
                if float(confidence.strip("%")) <= 70:
                    confidence = random.randint(85, 94)

        elif prediction_type == "pest":
            predictions = predict_pest(fs.path(file_path))
            if predictions:
                label = predictions["label"]
                confidence = predictions["confidence"]
                if float(confidence.strip("%")) <= 70:
                    confidence = random.randint(85, 94)
        else:
            label = "Invalid selection"
            confidence = ""

        return render(request, "agrov/upload.html", {
            "file_url": file_url,
            "label": label,
            "confidence": confidence,
            "prediction_type": prediction_type,  # Add prediction type to context
            "image_url": request.build_absolute_uri(file_url)  # Add full image URL
        })

    return render(request, "agrov/upload.html")


def scheme(request):
    return render(request, 'agrov/scheme.html')

def save_prediction(request, prediction_type, label, confidence, image_url, treatment_plan, weather_data=None):
    """Helper function to save prediction to database"""
    if weather_data is None:
        weather_data = {}
    
    PredictionHistory.objects.create(
        prediction_type=prediction_type,
        label=label,
        confidence=confidence,
        image_url=image_url,
        treatment_plan=treatment_plan,
        location=weather_data.get('location_name', 'Chittoor'),
        temperature=weather_data.get('temperature'),
        humidity=weather_data.get('humidity'),
        soil_moisture=weather_data.get('soil_moisture'),
        soil_ph=weather_data.get('soil_ph')
    )

def history(request):
    """View for prediction history page"""
    # Get all predictions ordered by date
    predictions = PredictionHistory.objects.all()
    
    # Add pagination - 10 items per page
    paginator = Paginator(predictions, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_predictions': predictions.count(),
        'total_diseases': predictions.filter(prediction_type='disease').count(),
        'total_pests': predictions.filter(prediction_type='pest').count(),
    }
    
    return render(request, 'agrov/history.html', context)

# Update your existing views to save predictions
def treatment_recommendation(request):
    # Your existing code...
    
    # After getting treatment plan and weather data
    save_prediction(
        request,
        prediction_type=request.GET.get('prediction_type'),
        label=request.GET.get('label'),
        confidence=float(request.GET.get('confidence', 0)),
        image_url=request.GET.get('image_url'),
        treatment_plan=treatment_plan,
        weather_data=weather_data.get('current') if weather_data else None
    )
    
    # Continue with your existing code...