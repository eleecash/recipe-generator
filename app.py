import streamlit as st
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import re
from fpdf import FPDF
import base64
import random
# Importar nuestro sistema de nutrición
from nutrition_estimator import get_real_nutrition, estimate_nutrition, show_ip_setup_instructions

# Cargar modelos (usar caché para mejor rendimiento)
@st.cache_resource
def load_models():
    # Modelo para clasificación de restricciones
    classifier = pipeline(
        "text-classification", 
        model="bert-base-uncased",
        top_k=None
    )
    
    # Modelo para generación de recetas (T5 fine-tuned)
    model_name = "flax-community/t5-recipe-generation"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    generator = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    
    return classifier, tokenizer, generator

def parse_generated_recipe(text):
    """Organiza la receta generada en secciones estructuradas"""
    sections = {
        "title": "",
        "ingredients": [],
        "instructions": [],
        "notes": ""
    }
    # El modelo genera secciones con encabezados: title:, ingredients:, directions:
    title_match = re.search(r"title:(.+)", text, re.IGNORECASE)
    if title_match:
        sections["title"] = title_match.group(1).strip()
    ingredients_match = re.search(r"ingredients:(.+?)(?:directions:|$)", text, re.IGNORECASE | re.DOTALL)
    if ingredients_match:
        # Los ingredientes suelen estar separados por "--"
        ingredients = [i.strip("- ") for i in ingredients_match.group(1).split("--") if i.strip()]
        sections["ingredients"] = ingredients
    instructions_match = re.search(r"directions:(.+)", text, re.IGNORECASE | re.DOTALL)
    if instructions_match:
        steps = [s.strip("- ") for s in instructions_match.group(1).split("--") if s.strip()]
        sections["instructions"] = [f"{i+1}. {step}" for i, step in enumerate(steps)]
    return sections

def validate_ingredients(ingredients, diet):
    """Valida los ingredientes según las restricciones dietéticas"""
    conflicts = []
    non_vegan = ["meat", "beef", "pork", "chicken", "fish", "egg", "milk", "cheese", "butter", "yogurt", "cream"]
    gluten = ["wheat", "barley", "rye", "bread", "pasta", "flour", "couscous", "farro", "spelt", "breadcrumbs"]
    
    if "Vegan" in diet:
        for item in non_vegan:
            if item in ingredients.lower():
                conflicts.append(f"⚠️ {item.capitalize()} is not vegan")
    
    if "Gluten Free" in diet:
        for item in gluten:
            if item in ingredients.lower():
                conflicts.append(f"⚠️ {item.capitalize()} contains gluten")
    
    return conflicts

def get_random_chef_tip():
    """Devuelve un tip aleatorio del chef"""
    tips = [
        "For extra flavor, add a pinch of smoked paprika.",
        "Always taste and adjust seasoning before serving.",
        "Let the dish rest for a few minutes before serving to allow flavors to meld.",
        "Use fresh herbs for a brighter taste.",
        "Toast spices in a dry pan to enhance their aroma.",
        "Add a splash of acid (lemon juice or vinegar) to balance rich flavors.",
        "Don't overcrowd the pan when searing to get a better crust.",
        "Reserve some pasta water to adjust sauce consistency.",
        "Chop ingredients uniformly for even cooking.",
        "Use high-quality olive oil for finishing dishes."
    ]
    return random.choice(tips)

def create_pdf(recipe):
    """Creates a PDF with modern and clean design"""
    pdf = FPDF()
    pdf.add_page()
    
    # Modern color palette
    primary_blue = (52, 152, 219)       # Professional blue
    light_blue = (235, 245, 255)       # Very light blue background
    dark_gray = (44, 62, 80)           # Dark text
    medium_gray = (127, 140, 141)       # Medium gray
    light_gray = (236, 240, 241)       # Light gray borders
    success_green = (46, 204, 113)     # Green accents
    white = (255, 255, 255)            # White
    
    # Check if there's content to show
    has_content = (recipe["title"] or recipe["ingredients"] or recipe["instructions"])
    if not has_content:
        return b""  # Return empty PDF if no content
    
    # ==================== HEADER SECTION ====================
    # Clean white background
    pdf.set_fill_color(*white)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Top accent bar
    pdf.set_fill_color(*primary_blue)
    pdf.rect(0, 0, 210, 8, 'F')
    
    # Main title with elegant styling
    pdf.set_y(25)
    recipe_title = recipe["title"] if recipe["title"] else "Generated Recipe"
    
    # Title background box
    pdf.set_fill_color(*light_blue)
    title_height = 20
    pdf.rect(20, 25, 170, title_height, 'F')
    
    # Title border
    pdf.set_draw_color(*primary_blue)
    pdf.set_line_width(1)
    pdf.rect(20, 25, 170, title_height)
    
    # Title text
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(*dark_gray)
    pdf.set_xy(25, 30)
    if len(recipe_title) > 35:
        pdf.set_font("Arial", 'B', 14)
    pdf.cell(160, 10, txt=to_latin1(recipe_title), ln=True, align='C')
    
    # Subtitle line
    pdf.set_y(50)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(*medium_gray)
    pdf.cell(0, 5, txt=to_latin1("Recipe generated by AI"), ln=True, align='C')
    
    # ==================== INGREDIENTS SECTION ====================
    current_y = 70
    
    if recipe["ingredients"]:
        # Section header with background
        pdf.set_fill_color(*success_green)
        pdf.rect(20, current_y, 170, 12, 'F')
        
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(*white)
        pdf.set_xy(25, current_y + 3)
        pdf.cell(0, 6, txt=to_latin1("INGREDIENTS"), ln=True)
        
        current_y += 18
        
        # Ingredients container
        ingredients_height = len(recipe["ingredients"]) * 7 + 15
        pdf.set_fill_color(*light_gray)
        pdf.rect(20, current_y, 170, ingredients_height, 'F')
        
        # Container border
        pdf.set_draw_color(*medium_gray)
        pdf.set_line_width(0.5)
        pdf.rect(20, current_y, 170, ingredients_height)
        
        # Ingredients list
        pdf.set_font("Arial", size=10)
        pdf.set_text_color(*dark_gray)
        item_y = current_y + 8
        
        for i, item in enumerate(recipe["ingredients"]):
            if item_y > current_y + ingredients_height - 8:
                break
            
            # Bullet point
            pdf.set_xy(25, item_y)
            pdf.set_text_color(*success_green)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(5, 5, txt=str(i + 1) + ".", ln=0)
            
            # Ingredient text
            pdf.set_text_color(*dark_gray)
            pdf.set_font("Arial", size=10)
            clean_item = item.strip()
            if len(clean_item) > 65:
                clean_item = clean_item[:62] + "..."
            
            pdf.cell(0, 5, txt=to_latin1(f" {clean_item}"), ln=True)
            item_y += 7
        
        current_y += ingredients_height + 15
    
    # ==================== INSTRUCTIONS SECTION ====================
    if recipe["instructions"]:
        # Check if we need a new page
        if current_y > 200:
            pdf.add_page()
            current_y = 30
        
        # Section header
        pdf.set_fill_color(*primary_blue)
        pdf.rect(20, current_y, 170, 12, 'F')
        
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(*white)
        pdf.set_xy(25, current_y + 3)
        pdf.cell(0, 6, txt=to_latin1("INSTRUCTIONS"), ln=True)
        
        current_y += 18
        
        # Instructions with step-by-step design
        pdf.set_font("Arial", size=10)
        pdf.set_text_color(*dark_gray)
        
        # Calculate total height needed for instructions
        total_height = len(recipe["instructions"]) * 15 + 20  # Estimate
        
        # Create instructions container
        pdf.set_fill_color(*light_gray)
        pdf.rect(20, current_y, 170, total_height, 'F')
        
        # Container border
        pdf.set_draw_color(*medium_gray)
        pdf.set_line_width(0.5)
        pdf.rect(20, current_y, 170, total_height)
        
        step_y = current_y + 10
        
        for i, step in enumerate(recipe["instructions"], 1):
            if step_y > 250:
                pdf.add_page()
                step_y = 30
            
            # Step number box
            pdf.set_fill_color(*primary_blue)
            pdf.rect(25, step_y, 6, 6, 'F')
            
            pdf.set_font("Arial", 'B', 8)
            pdf.set_text_color(*white)
            pdf.set_xy(26, step_y + 1)
            pdf.cell(4, 4, txt=str(i), ln=0, align='C')
            
            # Step text with proper wrapping within container
            pdf.set_text_color(*dark_gray)
            pdf.set_font("Arial", size=10)
            
            clean_step = re.sub(r'^\d+\.\s*', '', step)
            
            # Text wrapping with width constraint
            words = clean_step.split()
            lines = []
            current_line = ""
            max_width = 55  # Characters that fit in the container width
            
            for word in words:
                test_line = current_line + word + " "
                if len(test_line) > max_width:
                    if current_line:
                        lines.append(current_line.strip())
                        current_line = word + " "
                    else:
                        # Handle very long words
                        if len(word) > max_width:
                            lines.append(word[:max_width-3] + "...")
                            current_line = ""
                        else:
                            lines.append(word)
                            current_line = ""
                else:
                    current_line = test_line
            
            if current_line.strip():
                lines.append(current_line.strip())
            
            # Write the lines within the container bounds
            text_start_x = 35  # Start after the step number
            text_max_x = 185   # End before container border
            
            for line_idx, line in enumerate(lines):
                if step_y + (line_idx * 5) > current_y + total_height - 5:
                    break  # Don't overflow the container
                
                pdf.set_xy(text_start_x, step_y + (line_idx * 5))
                # Ensure text doesn't exceed container width
                if len(line) * 2.5 > (text_max_x - text_start_x):  # Rough character width estimate
                    line = line[:int((text_max_x - text_start_x) / 2.5)] + "..."
                pdf.cell(text_max_x - text_start_x, 5, txt=to_latin1(line), ln=0)
            
            step_y += max(15, len(lines) * 5 + 5)  # Space for next step
        
        current_y += total_height + 15
    
    # ==================== CHEF TIP SECTION ====================
    if current_y < 240:
        # Tip box with nice styling
        tip_height = 25
        pdf.set_fill_color(255, 248, 220)  # Light yellow
        pdf.rect(20, current_y, 170, tip_height, 'F')
        
        # Left accent border
        pdf.set_fill_color(255, 193, 7)  # Golden
        pdf.rect(20, current_y, 4, tip_height, 'F')
        
        # Tip content
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(*dark_gray)
        pdf.set_xy(30, current_y + 5)
        pdf.cell(0, 6, txt=to_latin1("Chef Tip"), ln=True)
        
        pdf.set_font("Arial", 'I', 9)
        pdf.set_text_color(*medium_gray)
        chef_tip = get_random_chef_tip()
        
        # Wrap tip text
        words = chef_tip.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if len(test_line) > 75:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    lines.append(word)
                    current_line = ""
            else:
                current_line = test_line
        
        if current_line.strip():
            lines.append(current_line.strip())
        
        tip_y = current_y + 12
        for line in lines[:2]:  # Max 2 lines for tip
            pdf.set_xy(30, tip_y)
            pdf.cell(0, 4, txt=to_latin1(line), ln=True)
            tip_y += 4
    
    # ==================== FOOTER ====================
    pdf.set_y(285)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(*medium_gray)
    pdf.cell(0, 5, txt=to_latin1("Generated with Recipe Generator - Enjoy your cooking!"), ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin1')

def generate_recipe(ingredients, diet, tokenizer, generator):
    """Genera una receta usando el modelo T5 fine-tuned para recetas"""
    prompt = f"{ingredients}"
    input_text = f"items: {prompt}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=256)
    output = generator.generate(
        **inputs,
        max_length=512,
        min_length=64,
        no_repeat_ngram_size=3,
        do_sample=True,
        top_k=60,
        top_p=0.95
    )
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return parse_generated_recipe(generated_text), generated_text

def to_latin1(text):
    """Convierte texto a latin1 manejando caracteres especiales"""
    # Reemplazar caracteres problemáticos por equivalentes ASCII
    replacements = {
        '•': '*',
        '—': '-',
        '–': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '…': '...',
        '💡': '',
        '🍳': '',
        '🥕': '',
        '📝': '',
        '📊': '',
        '❤️': '',
        '⚠️': '',
        '✨': '',
        '📥': '',
        '👨‍🍳': '',
    }
    
    # Aplicar reemplazos
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Intentar codificar a latin1, reemplazando caracteres problemáticos
    try:
        return text.encode('latin1', errors='replace').decode('latin1')
    except:
        # Si aún hay problemas, usar solo caracteres ASCII básicos
        return ''.join(char if ord(char) < 128 else '?' for char in text)

# Interfaz principal
def main():
    # Custom CSS for new color palette and modern look
    st.markdown('''
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .main, .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }
        
        .recipe-card {
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            padding: 2rem;
            margin: 1.5rem 0;
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        
        .recipe-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            transform: translateY(-2px);
        }
        
        .gradient-header {
            background: linear-gradient(135deg, #4a90e2 0%, #22c55e 100%);
            color: white;
            border-radius: 16px;
            padding: 3rem 2rem 2rem 2rem;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 8px 25px -5px rgba(74, 144, 226, 0.3);
        }
        
        .gradient-header h1 {
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .gradient-header p {
            font-weight: 400;
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        h1.gradient-header {
            background: linear-gradient(135deg, #4a90e2 0%, #22c55e 100%);
            color: white;
            border-radius: 16px;
            padding: 2rem;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 8px 25px -5px rgba(74, 144, 226, 0.3);
            font-weight: 700;
            font-size: 2rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section-header {
            color: #4a90e2;
            font-weight: 600;
            font-size: 1.4rem;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .ingredient-dot {
            color: #22c55e;
            font-size: 1.2em;
            margin-right: 0.75rem;
            font-weight: 600;
        }
        
        .step-item {
            display: flex;
            align-items: flex-start;
            padding: 0.75rem 0;
            color: #374151;
            line-height: 1.6;
        }
        
        .step-number {
            background: #4a90e2;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
            font-weight: 600;
            margin-right: 1rem;
            flex-shrink: 0;
        }
        
        .chef-tip {
            background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%);
            border-left: 4px solid #f59e0b;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 2rem 0;
            color: #92400e;
            font-style: italic;
        }
        
        .stTextArea textarea {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            background: white;
            font-size: 1rem;
            transition: border-color 0.2s ease;
        }
        
        .stTextArea textarea:focus {
            border-color: #4a90e2;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }
        
        .stSelectbox > div > div {
            background: white;
            border-radius: 12px;
            border: 2px solid #e2e8f0;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #4a90e2 0%, #22c55e 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1.1rem;
            padding: 0.75rem 2rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(74, 144, 226, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(74, 144, 226, 0.4);
        }
        
        .stDownloadButton > button {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.75rem 2rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.3);
        }
        
        .stDownloadButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(34, 197, 94, 0.4);
        }
        
        .conflict-warning {
            background: linear-gradient(135deg, #fef3cd 0%, #fde68a 100%);
            color: #92400e;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-left: 4px solid #f59e0b;
            box-shadow: 0 2px 4px rgba(245, 158, 11, 0.1);
        }
        
        .conflict-warning h3 {
            margin-bottom: 0.75rem;
            font-weight: 600;
        }
        
        .modern-input-label {
            color: #374151;
            font-weight: 500;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        
        /* Animaciones suaves */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .recipe-content {
            animation: fadeIn 0.5s ease-out;
        }
        
        /* Scroll suave */
        html {
            scroll-behavior: smooth;
        }
        </style>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="gradient-header"><h1>🍳 Recipe Generator</h1><p>Create delicious recipes based on your ingredients and dietary preferences</p></div>', unsafe_allow_html=True)

    # Barra lateral con información de FatSecret
    with st.sidebar:
        st.markdown("### 🔧 Configuración API")
        
        if st.button("📍 Ver configuración de IP para FatSecret"):
            st.markdown("---")
            show_ip_setup_instructions()
        
        st.markdown("---")
        st.markdown("### ℹ️ Información")
        st.markdown("""
        **Fuentes de datos nutricionales:**
        - 🥇 **FatSecret API** (preferido)
        - 📊 **Estimación básica** (respaldo)
        
        Para obtener datos nutricionales precisos,
        configura tu IP en FatSecret Platform.
        """)

    st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">What would you like to cook today?</h2>', unsafe_allow_html=True)

    ingredients = st.text_area(
        "🥕 Ingredients (separated by commas):",
        placeholder="e.g. chicken, rice, tomatoes, onion",
        height=100
    )

    diet_options = [
        "Normal", "Vegan", "Gluten Free", "Low Carb", "Vegetarian", "Dairy Free"
    ]
    diet = st.selectbox("❤️ Dietary preference:", diet_options)

    generate = st.button("✨ Generate Recipe", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if generate:
        if not ingredients:
            st.warning("Please enter at least one ingredient")
        else:
            with st.spinner("Creating your personalized recipe..."):
                diet_check = classifier(diet)[0][0]
                if diet_check['score'] < 0.7:
                    st.warning(f"The restriction '{diet}' may not be well defined")
                recipe, recipe_raw_text = None, None
                try:
                    recipe, recipe_raw_text = generate_recipe(ingredients, diet, tokenizer, generator)
                except Exception as e:
                    st.error(f"Error generating recipe: {e}")
                if recipe:
                    # Validación de ingredientes
                    conflicts = validate_ingredients(ingredients, diet)
                    if conflicts:
                        st.markdown('<div class="conflict-warning">', unsafe_allow_html=True)
                        st.markdown("<h3>⚠️ Ingredient Conflicts Detected</h3>", unsafe_allow_html=True)
                        for conflict in conflicts:
                            st.markdown(f"<p>{conflict}</p>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Obtener tip aleatorio del chef
                    chef_tip = get_random_chef_tip()
                    
                    st.markdown('<div class="recipe-card recipe-content">', unsafe_allow_html=True)
                    st.markdown(f'<h1 class="gradient-header">{recipe["title"] if recipe["title"] else "Generated Recipe"}</h1>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1,1])
                    
                    with col1:
                        st.markdown('<h3 class="section-header">🥕 Ingredients</h3>', unsafe_allow_html=True)
                        for item in recipe["ingredients"]:
                            st.markdown(f'<span class="ingredient-dot">•</span> {item}', unsafe_allow_html=True)
                        
                        st.markdown('<h3 class="section-header">📊 Nutrition Information</h3>', unsafe_allow_html=True)
                        
                        # Obtener datos nutricionales reales usando FatSecret API
                        try:
                            with st.spinner("🔍 Calculando información nutricional..."):
                                # Convertir ingredientes de texto a lista
                                ingredients_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
                                
                                # Obtener datos nutricionales reales
                                nutrition_info = get_real_nutrition(ingredients_list)
                                
                                # Crear DataFrame para mostrar
                                nutrition_data = {
                                    "Nutriente": ["Calorías", "Proteínas", "Carbohidratos", "Grasas"],
                                    "Cantidad": [
                                        nutrition_info.get("Calorías", "N/A"),
                                        nutrition_info.get("Proteínas", "N/A"),
                                        nutrition_info.get("Carbohidratos", "N/A"),
                                        nutrition_info.get("Grasas", "N/A")
                                    ]
                                }
                                
                                # Mostrar tabla con diseño mejorado
                                df_nutrition = pd.DataFrame(nutrition_data)
                                st.table(df_nutrition)
                                
                                # Mostrar información sobre la fuente de datos
                                if "FatSecret" in str(nutrition_info):
                                    st.success("✅ Datos nutricionales de FatSecret API")
                                else:
                                    st.info("ℹ️ Estimación nutricional (FatSecret no disponible)")
                                    
                        except Exception as e:
                            st.warning("⚠️ No se pudo calcular la información nutricional")
                            # Fallback a datos por defecto
                            nutrition_data = {
                                "Nutriente": ["Calorías", "Proteínas", "Carbohidratos", "Grasas"],
                                "Cantidad": ["~350 kcal", "~25g", "~45g", "~12g"]
                            }
                            st.table(pd.DataFrame(nutrition_data))
                            st.caption("*Valores aproximados")
                    
                    with col2:
                        st.markdown('<h3 class="section-header">📝 Instructions</h3>', unsafe_allow_html=True)
                        for i, step in enumerate(recipe["instructions"], 1):
                            clean_step = re.sub(r'^\d+\.\s*', '', step)
                            st.markdown(f'<div class="step-item"><span class="step-number">{i}</span> {clean_step}</div>', unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="chef-tip"><strong>Chef Tip:</strong> {chef_tip}</div>', unsafe_allow_html=True)
                    
                    # Botón para guardar como PDF
                    pdf_bytes = create_pdf(recipe)
                    if pdf_bytes:  # Solo mostrar si el PDF tiene contenido
                        st.download_button(
                            label="📥 Save as PDF",
                            data=pdf_bytes,
                            file_name=f"{recipe['title'].replace(' ', '_')}.pdf" if recipe['title'] else "recipe.pdf",
                            mime="application/pdf"
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)

# Cargar modelos al iniciar
classifier, tokenizer, generator = load_models()

if __name__ == "__main__":
    main()