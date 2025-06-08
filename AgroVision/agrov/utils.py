from .models import PredictionHistory

def save_prediction(prediction_type, label, confidence, image_url, treatment_plan, weather_data=None):
    """Helper function to save prediction to database"""
    if weather_data is None:
        weather_data = {}
    
    # Try to find an existing prediction with the same image_url and label
    existing_prediction = PredictionHistory.objects.filter(
        image_url=image_url,
        label=label,
        prediction_type=prediction_type
    ).first()
    
    if existing_prediction:
        # Update existing prediction with new data
        existing_prediction.confidence = confidence
        existing_prediction.treatment_plan = treatment_plan
        existing_prediction.location = weather_data.get('location_name', 'Chittoor')
        existing_prediction.temperature = weather_data.get('temperature')
        existing_prediction.humidity = weather_data.get('humidity')
        existing_prediction.soil_moisture = weather_data.get('soil_moisture')
        existing_prediction.soil_ph = weather_data.get('soil_ph')
        existing_prediction.save()
        return existing_prediction
    else:
        # Create new prediction
        return PredictionHistory.objects.create(
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