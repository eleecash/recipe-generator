import re
import pandas as pd
import requests

def estimate_nutrition(ingredients):
    """Estima valores nutricionales básicos (versión simplificada)"""
    # Este es un placeholder - en una implementación real usarías una API como Edamam
    nutrition = {
        "Calorías": 0,
        "Proteínas": 0,
        "Carbohidratos": 0,
        "Grasas": 0
    }
    
    # Mapeo simplificado de ingredientes a valores nutricionales
    nutrition_map = {
        "pollo": {"cal": 165, "prot": 31, "carb": 0, "fat": 3.6},
        "arroz": {"cal": 130, "prot": 2.7, "carb": 28, "fat": 0.3},
        "tomate": {"cal": 18, "prot": 0.9, "carb": 3.9, "fat": 0.2},
        "cebolla": {"cal": 40, "prot": 1.1, "carb": 9.3, "fat": 0.1},
        "aceite": {"cal": 120, "prot": 0, "carb": 0, "fat": 14}
    }
    
    for ingredient in ingredients:
        ingredient = ingredient.lower().strip()
        for key, values in nutrition_map.items():
            if key in ingredient:
                nutrition["Calorías"] += values["cal"]
                nutrition["Proteínas"] += values["prot"]
                nutrition["Carbohidratos"] += values["carb"]
                nutrition["Grasas"] += values["fat"]
    
    # Formatear resultados
    return {
        "Calorías": f"{nutrition['Calorías']} kcal",
        "Proteínas": f"{nutrition['Proteínas']}g",
        "Carbohidratos": f"{nutrition['Carbohidratos']}g",
        "Grasas": f"{nutrition['Grasas']}g"
    }

def get_real_nutrition(ingredients):
    app_id = "YOUR_APP_ID"
    app_key = "YOUR_APP_KEY"
    url = f"https://api.edamam.com/api/nutrition-data?app_id={app_id}&app_key={app_key}"
    response = requests.post(url, json={"ingr": ingredients})
    if response.status_code == 200:
        data = response.json()
        return {
            "Calories": f"{data['calories']} kcal",
            "Protein": f"{data['totalNutrients']['PROCNT']['quantity']}g",
            "Carbohydrates": f"{data['totalNutrients']['CHOCDF']['quantity']}g",
            "Fat": f"{data['totalNutrients']['FAT']['quantity']}g"
        }
    return None