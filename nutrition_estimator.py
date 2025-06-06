import re
import pandas as pd
import requests
import json
import base64
from datetime import datetime, timedelta

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

class FatSecretAPI:
    """Cliente para la API de FatSecret usando OAuth 2.0"""
    
    def __init__(self):
        self.client_id = "231f56f270844a0d96dec5af8923c662"
        self.client_secret = "147a661e168d47bbb0dc157d52408d98"
        self.token_url = "https://oauth.fatsecret.com/connect/token"
        self.api_url = "https://platform.fatsecret.com/rest/server.api"
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self):
        """Obtiene un token de acceso OAuth 2.0"""
        try:
            # Crear credenciales básicas
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'basic'
            }
            
            response = requests.post(self.token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 86400)  # Default 24 horas
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                return True
            else:
                print(f"Error obteniendo token: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error en autenticación: {str(e)}")
            return False
    
    def is_token_valid(self):
        """Verifica si el token actual es válido"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Renovar token si expira en menos de 5 minutos
        return datetime.now() < (self.token_expires_at - timedelta(minutes=5))
    
    def ensure_valid_token(self):
        """Asegura que tenemos un token válido"""
        if not self.is_token_valid():
            return self.get_access_token()
        return True
    
    def search_food(self, search_term):
        """Busca alimentos en la base de datos de FatSecret"""
        if not self.ensure_valid_token():
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            params = {
                'method': 'foods.search',
                'search_expression': search_term,
                'format': 'json'
            }
            
            response = requests.post(self.api_url, headers=headers, data=params)
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    
                    # Verificar si hay errores en la respuesta
                    if 'error' in json_response:
                        error_code = json_response['error'].get('code')
                        error_message = json_response['error'].get('message')
                        
                        if error_code == 21:  # Error de IP no autorizada
                            print(f"🚫 IP NO AUTORIZADA: {error_message}")
                            print("📋 SOLUCIÓN:")
                            print("   1. Ve a https://platform.fatsecret.com")
                            print("   2. Accede a tu aplicación registrada")
                            print("   3. Encuentra la sección 'IP Management' o 'Allowed IPs'")
                            print(f"   4. Añade tu IP actual a la lista de permitidas")
                            print("   5. Guarda los cambios y vuelve a intentar")
                            return None
                        else:
                            print(f"❌ Error de API - Código {error_code}: {error_message}")
                            return None
                    
                    return json_response
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Error decodificando JSON: {e}")
                    return None
            else:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error en búsqueda de alimento: {str(e)}")
            return None
    
    def get_food_details(self, food_id):
        """Obtiene detalles nutricionales de un alimento específico"""
        if not self.ensure_valid_token():
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'method': 'food.get',
                'food_id': food_id,
                'format': 'json'
            }
            
            response = requests.post(self.api_url, headers=headers, data=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error obteniendo detalles del alimento {food_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error obteniendo detalles del alimento: {str(e)}")
            return None

def get_real_nutrition(ingredients):
    """Obtiene información nutricional real usando FatSecret API"""
    fatsecret = FatSecretAPI()
    
    total_nutrition = {
        "Calorías": 0,
        "Proteínas": 0,
        "Carbohidratos": 0,
        "Grasas": 0
    }
    
    successful_lookups = 0
    
    try:
        for ingredient in ingredients:
            # Limpiar el ingrediente
            clean_ingredient = ingredient.strip().lower()
            if not clean_ingredient:
                continue
            
            print(f"Buscando información nutricional para: {clean_ingredient}")
            
            # Buscar el alimento
            search_result = fatsecret.search_food(clean_ingredient)
            
            if search_result and 'foods' in search_result:
                foods_data = search_result['foods']
                
                if 'food' in foods_data and len(foods_data['food']) > 0:
                    # Tomar el primer resultado
                    first_food = foods_data['food'][0] if isinstance(foods_data['food'], list) else foods_data['food']
                    food_id = first_food.get('food_id')
                    
                    if food_id:
                        # Obtener detalles nutricionales
                        food_details = fatsecret.get_food_details(food_id)
                        
                        if food_details and 'food' in food_details:
                            food_info = food_details['food']
                            servings = food_info.get('servings', {})
                            
                            if 'serving' in servings:
                                serving_data = servings['serving']
                                if isinstance(serving_data, list):
                                    serving_data = serving_data[0]  # Tomar la primera porción
                                
                                # Extraer información nutricional
                                calories = float(serving_data.get('calories', 0))
                                protein = float(serving_data.get('protein', 0))
                                carbs = float(serving_data.get('carbohydrate', 0))
                                fat = float(serving_data.get('fat', 0))
                                
                                total_nutrition["Calorías"] += calories
                                total_nutrition["Proteínas"] += protein
                                total_nutrition["Carbohidratos"] += carbs
                                total_nutrition["Grasas"] += fat
                                
                                successful_lookups += 1
                                print(f"✓ Encontrado: {clean_ingredient} - {calories} kcal")
                            else:
                                print(f"⚠ No se encontraron porciones para: {clean_ingredient}")
                        else:
                            print(f"⚠ No se pudieron obtener detalles para: {clean_ingredient}")
                    else:
                        print(f"⚠ No se encontró ID para: {clean_ingredient}")
                else:
                    print(f"⚠ No se encontraron resultados para: {clean_ingredient}")
            else:
                print(f"⚠ Error en búsqueda para: {clean_ingredient}")
        
        if successful_lookups > 0:
            print(f"\n✓ Se procesaron exitosamente {successful_lookups} de {len(ingredients)} ingredientes")
            
            return {
                "Calorías": f"{total_nutrition['Calorías']:.1f} kcal",
                "Proteínas": f"{total_nutrition['Proteínas']:.1f}g",
                "Carbohidratos": f"{total_nutrition['Carbohidratos']:.1f}g",
                "Grasas": f"{total_nutrition['Grasas']:.1f}g"
            }
        else:
            print("⚠ No se pudo obtener información nutricional de FatSecret. Usando estimación básica.")
            return estimate_nutrition(ingredients)
            
    except Exception as e:
        print(f"Error general en get_real_nutrition: {str(e)}")
        print("Usando estimación básica como respaldo.")
        return estimate_nutrition(ingredients)

def test_fatsecret_api():
    """Función de prueba para verificar que la API de FatSecret funciona"""
    print("🧪 Probando conexión con FatSecret API...")
    
    test_ingredients = ["manzana", "pollo", "arroz"]
    result = get_real_nutrition(test_ingredients)
    
    print("\n📊 Resultado de la prueba:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    return result

def get_current_ip():
    """Obtiene la dirección IP pública actual"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        if response.status_code == 200:
            return response.json()['ip']
    except Exception as e:
        print(f"Error obteniendo IP: {e}")
    
    try:
        response = requests.get('https://httpbin.org/ip', timeout=5)
        if response.status_code == 200:
            return response.json()['origin']
    except Exception as e:
        print(f"Error obteniendo IP (método 2): {e}")
    
    return "No se pudo determinar"

def show_ip_setup_instructions():
    """Muestra instrucciones para configurar la IP en FatSecret"""
    current_ip = get_current_ip()
    
    print("=" * 60)
    print("🔧 CONFIGURACIÓN REQUERIDA PARA FATSECRET API")
    print("=" * 60)
    print(f"📍 Tu IP actual es: {current_ip}")
    print()
    print("📋 PASOS PARA CONFIGURAR:")
    print("   1. Ve a https://platform.fatsecret.com")
    print("   2. Inicia sesión en tu cuenta de desarrollador")
    print("   3. Ve a 'My Applications' o 'Mis Aplicaciones'")
    print("   4. Selecciona tu aplicación")
    print("   5. Busca la sección 'IP Management', 'Allowed IP Addresses' o similar")
    print(f"   6. Añade esta IP a la lista: {current_ip}")
    print("   7. Guarda los cambios")
    print("   8. Espera unos minutos para que se apliquen los cambios")
    print()
    print("💡 CONSEJOS:")
    print("   • Si tu IP cambia frecuentemente, considera usar un rango de IPs")
    print("   • Para FatSecret PREMIER puedes usar notación CIDR")
    print("   • Algunas aplicaciones permiten múltiples IPs separadas por comas")
    print("=" * 60)

if __name__ == "__main__":
    # Ejecutar prueba si se ejecuta directamente
    test_fatsecret_api()