import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import io
import uuid # For unique filenames
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiseaseDetector:
    def __init__(self, voice_handler=None):
        self.voice_handler = voice_handler
        # Define class labels
        self.DISEASE_CLASSES = [
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
        
        self.PEST_CLASSES = [
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
        
        # Load models
        self.disease_model = self._load_model('disease')
        self.pest_model = self._load_model('pest')
        
        # Directory for saving uploaded images
        self.upload_dir = os.path.join('static', 'uploads')
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def _load_model(self, model_type):
        """Load the appropriate model based on type (disease or pest)"""
        model_path = os.path.join('models', f'{model_type}_model.h5')
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return None # Return None if model is not found
        try:
            model = load_model(model_path)
            logger.info(f"Successfully loaded {model_type} model from {model_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading {model_type} model from {model_path}: {str(e)}")
            return None

    def detect_disease(self, image_bytes, lang_code='en'):
        """Unified method to detect both disease and pest from image data"""
        try:
            # Convert bytes to PIL Image
            pil_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Save the uploaded image (or a copy) to a static path
            unique_filename = f"{uuid.uuid4()}.jpg"
            image_path_full = os.path.join(self.upload_dir, unique_filename)
            pil_img.save(image_path_full)
            image_static_url = os.path.join('uploads', unique_filename).replace('\\', '/') # Path for web access, ensure forward slashes

            # --- Disease Prediction ---
            disease_img = pil_img.resize((192, 192))
            disease_img_array = np.array(disease_img)
            disease_img_array = np.expand_dims(disease_img_array, axis=0) / 255.0

            disease_info = {
                'label': "No disease detected",
                'confidence': 0.0,
                'treatment_info': self._get_treatment('disease', 'healthy', lang_code) # Default healthy info
            }

            if self.disease_model:
                disease_predictions = self.disease_model.predict(disease_img_array, verbose=0)
                predicted_disease_index = np.argmax(disease_predictions[0])
                disease_label = self.DISEASE_CLASSES[predicted_disease_index]
                disease_confidence = float(np.max(disease_predictions[0]) * 100)
                disease_treatment_info = self._get_treatment('disease', disease_label, lang_code)
                
                disease_info = {
                    'label': disease_label,
                    'confidence': round(disease_confidence, 2),
                    'treatment_info': disease_treatment_info
                }
            else:
                logger.warning("Disease model not loaded. Skipping disease prediction.")

            # --- Pest Prediction ---
            pest_img = pil_img.resize((256, 256))
            pest_img_array = np.array(pest_img)
            pest_img_array = np.expand_dims(pest_img_array, axis=0) / 255.0

            pest_info = {
                'label': "No pest detected",
                'confidence': 0.0,
                'treatment_info': self._get_treatment('pest', 'healthy', lang_code) # Default healthy info for pest if applicable
            }
            
            if self.pest_model:
                pest_predictions = self.pest_model.predict(pest_img_array, verbose=0)
                predicted_pest_index = np.argmax(pest_predictions[0])
                pest_label = self.PEST_CLASSES[predicted_pest_index]
                pest_confidence = float(np.max(pest_predictions[0]) * 100)
                pest_treatment_info = self._get_treatment('pest', pest_label, lang_code)
                
                pest_info = {
                    'label': pest_label,
                    'confidence': round(pest_confidence, 2),
                    'treatment_info': pest_treatment_info
                }
            else:
                logger.warning("Pest model not loaded. Skipping pest prediction.")
            
            # Return separate results for disease and pest
            return {
                'disease_result': disease_info,
                'pest_result': pest_info,
                'image_path': image_static_url
            }

        except Exception as e:
            logger.error(f"Error in detect_disease: {str(e)}")
            return None

    def _get_treatment(self, prediction_type, label, lang_code='en'):
        """Get detailed treatment recommendations including symptoms, causes, and prevention."""
        default_info = {
            'treatment': "No specific treatment information available. Please consult an agricultural expert.",
            'symptoms': "Symptoms not specifically listed or N/A.",
            'causes': "Causes not specifically listed or N/A.",
            'prevention': "Prevention methods not specifically listed or N/A."
        }

        treatments = {
            'disease': {
                'Tomato_Early_blight': {
                    'treatment': 'Apply copper-based fungicides and practice crop rotation.',
                    'symptoms': 'Small, dark, circular spots on older leaves, often with concentric rings. May also affect stems and fruits.',
                    'causes': 'Caused by the fungus Alternaria solani. Favored by warm, humid conditions.',
                    'prevention': 'Use resistant varieties, rotate crops, space plants properly for air circulation, water at the base of plants, and remove infected plant debris.'
                },
                'Tomato_Late_blight': {
                    'treatment': 'Use fungicides containing chlorothalonil or mancozeb. Destroy infected plants immediately.',
                    'symptoms': 'Large, irregular, water-soaked spots on leaves that rapidly turn brown/black. White, fuzzy mold may appear on the undersides of leaves.',
                    'causes': 'Caused by the oomycete Phytophthora infestans. Favored by cool, wet conditions.',
                    'prevention': 'Use resistant varieties, ensure good drainage, avoid overhead irrigation, and apply preventative fungicides.'
                },
                'Tomato_Leaf_Mold': {
                    'treatment': 'Improve air circulation, reduce humidity, and apply appropriate fungicides.',
                    'symptoms': 'Pale green or yellow spots on upper leaf surfaces, with olive-green to brown velvety patches on the undersides.',
                    'causes': 'Caused by the fungus Fulvia fulva (formerly Cladosporium fulvum). Favored by high humidity.',
                    'prevention': 'Improve ventilation in greenhouses, space plants adequately, and remove lower leaves.'
                },
                'Tomato_Septoria_leaf_spot': {
                    'treatment': 'Remove infected leaves and apply copper-based fungicides or fungicides containing chlorothalonil.',
                    'symptoms': 'Numerous small, circular spots with dark brown margins and tan centers, often with tiny black specks (pycnidia) in the center.',
                    'causes': 'Caused by the fungus Septoria lycopersici. Favored by warm, wet weather.',
                    'prevention': 'Practice crop rotation, remove infected debris, avoid overhead watering, and ensure good air circulation.'
                },
                'Tomato_Spider_mites_Two_spotted_spider_mite': {
                    'treatment': 'Use miticides or insecticidal soaps. Encourage natural predators like predatory mites. Increase humidity.',
                    'symptoms': 'Tiny yellow or white stipples on leaves. Fine webbing on the undersides of leaves or between leaves and stems. Leaves may turn yellow and drop.',
                    'causes': 'Caused by spider mites (Tetranychus urticae). Favored by hot, dry conditions.',
                    'prevention': 'Regularly inspect plants, spray with water to disrupt mites, and maintain good plant hygiene.'
                },
                'Tomato__Target_Spot': {
                    'treatment': 'Apply fungicides and practice good field sanitation. Use resistant varieties.',
                    'symptoms': 'Circular or irregularly shaped spots on leaves, stems, and fruits. Spots have concentric rings and often a yellow halo.',
                    'causes': 'Caused by the fungus Corynespora cassiicola. Favored by warm, humid conditions.',
                    'prevention': 'Crop rotation, sanitation, and proper plant spacing.'
                },
                'Tomato__Tomato_YellowLeaf__Curl_Virus': {
                    'treatment': 'Control whiteflies, remove infected plants immediately, and use virus-resistant varieties.',
                    'symptoms': 'Severe stunting of plants, upward curling and yellowing of leaves, small flowers and fruits.',
                    'causes': 'Caused by Tomato Yellow Leaf Curl Virus, transmitted by whiteflies.',
                    'prevention': 'Manage whitefly populations, use silver reflective mulch, and select resistant cultivars.'
                },
                'Tomato__Tomato_mosaic_virus': {
                    'treatment': 'Remove infected plants and control aphids. Disinfect tools.',
                    'symptoms': 'Mosaic pattern (light and dark green areas) on leaves, leaf distortion, stunting, and reduced fruit quality.',
                    'causes': 'Caused by Tomato Mosaic Virus (ToMV), highly contagious, spread by contact and aphids.',
                    'prevention': 'Use resistant varieties, practice good sanitation, and control aphids.'
                },
                'Tomato_healthy': {
                    'treatment': 'No treatment needed. Your plant appears healthy!',
                    'symptoms': 'Vibrant green leaves, strong stems, and healthy fruit development.',
                    'causes': 'N/A',
                    'prevention': 'Continue good agricultural practices.'
                },
                'Pepper__bell___Bacterial_spot': {
                    'treatment': 'Use copper-based bactericides and practice crop rotation. Remove infected leaves.',
                    'symptoms': 'Small, circular, water-soaked spots on leaves that turn brown/black with a yellow halo. Can also affect fruits.',
                    'causes': 'Caused by bacteria (Xanthomonas campestris pv. vesicatoria). Favored by warm, wet weather.',
                    'prevention': 'Use disease-free seeds/transplants, practice crop rotation, and avoid overhead irrigation.'
                },
                'Pepper__bell___healthy': {
                    'treatment': 'No treatment needed. Your plant appears healthy!',
                    'symptoms': 'Lush green leaves, strong stems, and uniform fruit development.',
                    'causes': 'N/A',
                    'prevention': 'Maintain good growing conditions.'
                },
                'Potato___Early_blight': {
                    'treatment': 'Apply fungicides and avoid overhead irrigation. Practice crop rotation.',
                    'symptoms': 'Dark, circular spots with concentric rings on older leaves, often surrounded by a yellow halo. Can also affect stems and tubers.',
                    'causes': 'Caused by the fungus Alternaria solani. Favored by warm, humid conditions.',
                    'prevention': 'Use resistant varieties, ensure proper plant spacing, and remove infected plant debris.'
                },
                'Potato___Late_blight': {
                    'treatment': 'Use appropriate fungicides (e.g., containing chlorothalonil) and remove infected plants immediately.',
                    'symptoms': 'Large, irregular, dark brown or black spots on leaves, often with a fuzzy white mold on the undersides in humid conditions. Rapid wilting and collapse of plants.',
                    'causes': 'Caused by the oomycete Phytophthora infestans. Favored by cool, wet conditions.',
                    'prevention': 'Plant resistant varieties, ensure good drainage, and apply preventative fungicides.'
                },
                'Potato___healthy': {
                    'treatment': 'No treatment needed. Your plant appears healthy!',
                    'symptoms': 'Vigorous growth, healthy foliage, and no signs of discoloration or lesions.',
                    'causes': 'N/A',
                    'prevention': 'Continue good agricultural practices.'
                }
            },
            'pest': {
                'aphids': {
                    'treatment': 'Use insecticidal soap or neem oil. Encourage natural predators like ladybugs.',
                    'symptoms': 'Curled, yellowing leaves; sticky honeydew on leaves and stems; presence of small, pear-shaped insects on new growth.',
                    'causes': 'Infestation by various species of aphids. Rapid reproduction.',
                    'prevention': 'Monitor plants regularly, introduce beneficial insects, and use row covers.'
                },
                'armyworm': {
                    'treatment': 'Apply appropriate insecticides or use biological controls like Bacillus thuringiensis (Bt).',
                    'symptoms': 'Ragged holes in leaves, defoliation, damage to stems and fruits. Caterpillars may be visible on plants.',
                    'causes': 'Larvae of various moth species (e.g., Spodoptera frugiperda).',
                    'prevention': 'Monitor fields for eggs and larvae, rotate crops, and control weeds.'
                },
                'beetle': {
                    'treatment': 'Handpick beetles or use appropriate insecticides. Use row covers.',
                    'symptoms': 'Chewing damage on leaves, stems, or roots. Visible adult beetles or larvae.',
                    'causes': 'Infestation by various beetle species (e.g., Colorado potato beetle, flea beetle).',
                    'prevention': 'Crop rotation, good sanitation, and physical barriers.'
                },
                'bollworm': {
                    'treatment': 'Use Bt (Bacillus thuringiensis) or spinosad-based insecticides. Release beneficial insects.',
                    'symptoms': 'Holes in cotton bolls or other fruits/buds, internal feeding damage, premature shedding of bolls.',
                    'causes': 'Larvae of Helicoverpa armigera or related species.',
                    'prevention': 'Monitor pest populations, plant resistant varieties, and practice crop rotation.'
                },
                'grasshopper': {
                    'treatment': 'Use carbaryl or bifenthrin-based insecticides. Remove weeds that serve as alternate hosts.',
                    'symptoms': 'Irregular holes or ragged edges on leaves and stems. Visible grasshoppers jumping or flying.',
                    'causes': 'Infestation by various grasshopper species. Favored by warm, dry conditions.',
                    'prevention': 'Maintain clean fields, use physical barriers for small gardens, and encourage natural predators.'
                },
                'mites': {
                    'treatment': 'Use miticides or insecticidal soaps. Increase humidity to deter mites. Release predatory mites.',
                    'symptoms': 'Stippling (tiny yellow or white dots) on leaves, bronze or yellow discoloration, fine webbing on undersides of leaves.',
                    'causes': 'Infestation by various mite species (e.g., two-spotted spider mite).',
                    'prevention': 'Regularly inspect plants, spray with water to dislodge mites, and ensure adequate humidity.'
                },
                'mosquito': {
                    'treatment': 'Remove standing water. Use larvicides in water that cannot be drained. Use mosquito nets.',
                    'symptoms': 'Presence of adult mosquitoes, bites on workers or livestock, potential for disease transmission.',
                    'causes': 'Presence of stagnant water sources for breeding.',
                    'prevention': 'Eliminate standing water, use biological control agents in water, and practice good sanitation.'
                },
                'sawfly': {
                    'treatment': 'Handpick larvae or use appropriate insecticides. Encourage natural enemies.',
                    'symptoms': 'Defoliation of plants, often with characteristic feeding patterns (e.g., skeletonized leaves). Larvae resemble caterpillars.',
                    'causes': 'Infestation by various sawfly species. Larvae feed on plant foliage.',
                    'prevention': 'Monitor plants, apply insecticidal soaps, and maintain plant health.'
                },
                'stem_borer': {
                    'treatment': 'Use appropriate systemic insecticides. Remove and destroy infested plants. Practice deep plowing.',
                    'symptoms': 'Wilting of central leaves or entire plants, stunted growth, exit holes on stems, frass (excrement) inside stems.',
                    'causes': 'Larvae of various moth species (e.g., Chilo partellus) boring into plant stems.',
                    'prevention': 'Crop rotation, early planting, use of resistant varieties, and removal of infested plant debris.'
                }
            }
        }
        
        info = treatments.get(prediction_type, {}).get(label, default_info)

        # Add translation logic here if voice_handler is available
        if lang_code != 'en' and self.voice_handler:
            try:
                logger.info(f"Translating treatment info to {lang_code}")
                translated_info = {
                    'treatment': self.voice_handler.translate_text(info['treatment'], 'en', lang_code),
                    'symptoms': self.voice_handler.translate_text(info['symptoms'], 'en', lang_code),
                    'causes': self.voice_handler.translate_text(info['causes'], 'en', lang_code),
                    'prevention': self.voice_handler.translate_text(info['prevention'], 'en', lang_code)
                }
                return translated_info
            except Exception as e:
                logger.error(f"Error translating treatment info: {e}")
        return info
