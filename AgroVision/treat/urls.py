from django.urls import path
from . import views


urlpatterns = [
    path('', views.disease_input, name='disease_input'),
    path('treatment-recommendation/', views.treatment_recommendation, name='treatment_recommendation'),
    path('download-pdf/', views.download_pdf, name='download_pdf'),
    
    # New URL patterns
    path('pestinput/', views.pest_input, name='pest_input'),  # URL for pest input
    path('get-treatment-pest/<str:pest_name>/', views.get_treatment_pest, name='get_treatment_pest'),  # URL for getting treatment for a pest
    path('pestdf/', views.pest_pdf, name='pest_pdf'),  # URL for downloading pest PDF
    path('forecast-recommendations/', views.generate_growth_recommendations, name='forecast_recommendations'),  # URL for weather forecast and growth recommendations

]
