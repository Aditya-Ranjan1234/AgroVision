import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import os

# Define paths for both models
MODEL_PATHS = {
    "pest": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data preprocessing", "mobilenetv2_model.h5"),
    "disease": os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai", "mobilenetv2_model.h5"),
}

# Load models
disease_model = load_model(MODEL_PATHS["disease"])
pest_model = load_model(MODEL_PATHS["pest"])

# Class labels for disease model
DISEASE_CLASSES = [
    'Pepper__bell___Bacterial_spot',
    'Pepper__bell___healthy',
    'Potato___Early_blight',
    'Potato___Late_blight',
    'Potato___healthy',
    'Tomato_Bacterial_spot',
    'Tomato_Early_blight',
    'Tomato_Late_blight',
    'Tomato_Leaf_Mold',
    'Tomato_Septoria_leaf_spot',
    'Tomato_Spider_mites_Two_spotted_spider_mite',
    'Tomato__Target_Spot',
    'Tomato__Tomato_YellowLeaf__Curl_Virus',
    'Tomato__Tomato_mosaic_virus',
    'Tomato_healthy'
]

# Class labels for pest model
PEST_CLASSES = [
    'aphids',
    'armyworm',
    'beetle',
    'bollworm',
    'grasshopper',
    'mites',
    'mosquito',
    'sawfly',
    'stem_borer'
]

# Prediction function for disease
def predict_disease(img_path):
    img = image.load_img(img_path, target_size=(192, 192))
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)

    predictions = disease_model.predict(img_array)
    predicted_class = DISEASE_CLASSES[np.argmax(predictions[0])]
    confidence = np.max(predictions[0]) * 100  # Convert to percentage

    return {
        "label": predicted_class,
        "confidence": f"{confidence:.2f}%"
    }

# Prediction function for pest
def predict_pest(img_path):
    img = image.load_img(img_path, target_size=(256, 256))
    img_array =np.array(img)
    img_array = np.expand_dims(img_array, axis=0)
    predictions = pest_model.predict(img_array)
    predicted_class = PEST_CLASSES[np.argmax(predictions)]
    confidence = np.max(predictions) * 100  # Convert to percentage
    print(predicted_class, confidence)

    return {
        "label": predicted_class,
        "confidence": f"{confidence:.2f}%"
    }
