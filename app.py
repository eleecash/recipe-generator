import streamlit as st
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import re
from fpdf import FPDF
import base64
import random

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
                conflicts.append(f"⚠️ {item.capitalize()} no es vegano")
    
    if "Gluten Free" in diet:
        for item in gluten:
            if item in ingredients.lower():
                conflicts.append(f"⚠️ {item.capitalize()} contiene gluten")
    
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
    """Crea un PDF con el estilo clásico de receta"""
    pdf = FPDF()
    pdf.add_page()
    
    # Configuración de colores corporativos
    primary_color = (55, 113, 177)   # #3771b1
    secondary_color = (198, 214, 155) # #c6d69b
    accent_color = (246, 230, 181)   # #f6e6b5
    dark_color = (52, 59, 27)        # #343b1b
    
    # Encabezado con estilo vintage
    pdf.set_font("Times", 'B', 24)
    pdf.set_text_color(*dark_color)
    pdf.cell(200, 15, txt=to_latin1(recipe["title"] if recipe["title"] else "Generated Recipe"), ln=True, align='C')
    pdf.ln(10)
    
    # Línea decorativa
    pdf.set_draw_color(*primary_color)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(12)
    
    # Sección de ingredientes
    pdf.set_font("Times", 'B', 18)
    pdf.set_text_color(*dark_color)
    pdf.cell(200, 10, txt="Ingredients", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Times", size=12)
    pdf.set_text_color(0, 0, 0)  # Negro
    
    # Lista de ingredientes con viñetas vintage
    for item in recipe["ingredients"]:
        pdf.set_font("Times", 'B', 14)
        pdf.set_text_color(*primary_color)
        pdf.cell(5, 8, txt="-", ln=0)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Times", size=12)
        pdf.multi_cell(0, 8, txt=to_latin1(f" {item}"))
        pdf.ln(2)
    pdf.ln(8)
    
    # Línea decorativa
    pdf.set_draw_color(*primary_color)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(12)
    
    # Sección de preparación
    pdf.set_font("Times", 'B', 18)
    pdf.set_text_color(*dark_color)
    pdf.cell(200, 10, txt="Preparation", ln=True)
    pdf.ln(5)
    
    # Instrucciones con estilo clásico
    pdf.set_font("Times", size=12)
    pdf.set_text_color(0, 0, 0)
    
    for step in recipe["instructions"]:
        # Eliminar numeración si está presente
        clean_step = re.sub(r'^\d+\.\s*', '', step)
        pdf.multi_cell(0, 8, txt=to_latin1(clean_step))
        pdf.ln(5)
    
    # Notas del chef con estilo vintage
    chef_tip = get_random_chef_tip()
    pdf.ln(10)
    pdf.set_draw_color(*primary_color)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_font("Times", 'B', 14)
    pdf.set_text_color(*dark_color)
    pdf.cell(200, 8, txt="Chef's Tip", ln=True)
    pdf.ln(3)
    
    pdf.set_font("Times", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, txt=to_latin1(chef_tip))
    
    # Pie de página vintage
    pdf.set_y(-15)
    pdf.set_font("Times", 'I', 10)
    pdf.set_text_color(*primary_color)
    pdf.cell(0, 10, txt="Generated by Recipe Generator App", align='C')
    
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
    # Reemplaza caracteres no latin1 por aproximaciones o los elimina
    return text.encode('latin1', errors='replace').decode('latin1')

# Interfaz principal
def main():
    # Custom CSS for new color palette and modern look
    st.markdown('''
        <style>
        body {
            background: linear-gradient(135deg, #c6d69b 0%, #faf8ee 100%) !important;
        }
        .main, .stApp {
            background: transparent !important;
        }
        .recipe-card {
            background: #faf8ee;
            border-radius: 1.2rem;
            box-shadow: 0 10px 30px -10px rgba(52,59,27,0.10);
            padding: 2.5rem 2rem 2rem 2rem;
            margin-bottom: 2rem;
            border: 2px solid #c6d69b;
        }
        .gradient-header {
            background: linear-gradient(90deg, #f6e6b5 0%, #c6d69b 100%);
            color: #343b1b;
            border-radius: 1.2rem 1.2rem 0 0;
            padding: 2rem 2rem 1rem 2rem;
            margin-bottom: 0;
            border-bottom: 2px solid #c6d69b;
        }
        .ingredient-dot {
            color: #3771b1;
            font-size: 1.2em;
            margin-right: 0.5em;
        }
        .step-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #3771b1;
            border-radius: 50%;
            margin-right: 0.7em;
        }
        .chef-tip {
            background: #f6e6b5;
            border-left: 5px solid #c6d69b;
            border-radius: 0.7rem;
            padding: 1rem 1.5rem;
            margin-top: 2rem;
            color: #343b1b;
        }
        .action-btn {
            background: #3771b1;
            color: #fff;
            border: none;
            border-radius: 0.7rem;
            padding: 0.7rem 1.5rem;
            margin-right: 0.7rem;
            font-weight: 600;
            transition: background 0.2s;
        }
        .action-btn:hover {
            background: #343b1b;
        }
        .stTextArea textarea, .stSelectbox, .stButton button {
            font-size: 1.1em;
        }
        .stTextArea textarea {
            border-radius: 0.7rem;
            border: 1.5px solid #c6d69b;
            background: #faf8ee;
        }
        .stButton button {
            background: linear-gradient(90deg, #3771b1 0%, #c6d69b 100%);
            color: #fff;
            border: none;
            border-radius: 0.7rem;
            font-weight: 700;
            padding: 0.8em 2em;
            margin-top: 1em;
        }
        .stButton button:hover {
            background: linear-gradient(90deg, #343b1b 0%, #3771b1 100%);
        }
        .stTable {
            background: #f6e6b5;
            border-radius: 0.7rem;
        }
        .conflict-warning {
            background-color: #fff3cd;
            color: #856404;
            border-radius: 0.7rem;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 5px solid #ffc107;
        }
        div.stDownloadButton > button {
            background: linear-gradient(90deg, #3771b1 0%, #c6d69b 100%);
            color: #fff;
            border: none;
            border-radius: 0.7rem;
            padding: 0.7rem 1.5rem;
            font-weight: 600;
            transition: background 0.2s;
            margin-top: 1em;
        }
        div.stDownloadButton > button:hover {
            background: linear-gradient(90deg, #343b1b 0%, #3771b1 100%);
            color: #fff;
        }
        </style>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="gradient-header"><h1 style="font-size:2.7em; margin-bottom:0.2em;">🍳 Recipe Generator</h1><p style="font-size:1.2em; color:#343b1b; margin-bottom:0;">Create delicious recipes based on your ingredients and dietary preferences</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
    st.markdown('<h2 style="font-size:1.5em; margin-bottom:1em; color:#3771b1;">What would you like to cook today?</h2>', unsafe_allow_html=True)

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
                        st.markdown("<h3 style='color:#856404; margin-bottom:0.5em;'>⚠️ Ingredient Conflicts Detected</h3>", unsafe_allow_html=True)
                        for conflict in conflicts:
                            st.markdown(f"<p style='margin:0;'>{conflict}</p>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Obtener tip aleatorio del chef
                    chef_tip = get_random_chef_tip()
                    
                    st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="gradient-header"><h2 style="font-size:2em; margin-bottom:0.2em;">{recipe["title"] if recipe["title"] else "Generated Recipe"}</h2></div>', unsafe_allow_html=True)
                    col1, col2 = st.columns([1,1])
                    with col1:
                        st.markdown('<h3 style="color:#3771b1; margin-top:1em;">🥕 Ingredients</h3>', unsafe_allow_html=True)
                        for item in recipe["ingredients"]:
                            st.markdown(f'<span class="ingredient-dot">•</span> {item}', unsafe_allow_html=True)
                        st.markdown('<h3 style="color:#3771b1; margin-top:2em;">📊 Nutrition Information</h3>', unsafe_allow_html=True)
                        nutrition_data = {
                            "Nutrient": ["Calories", "Protein", "Carbohydrates", "Fat"],
                            "Amount": ["350 kcal", "25g", "45g", "12g"]
                        }
                        st.table(pd.DataFrame(nutrition_data))
                    with col2:
                        st.markdown('<h3 style="color:#3771b1; margin-top:1em;">📝 Instructions</h3>', unsafe_allow_html=True)
                        for step in recipe["instructions"]:
                            st.markdown(f'<span class="step-dot"></span> {step}', unsafe_allow_html=True)
                        st.markdown(f'<div class="chef-tip"><b>👨‍🍳 Chef tip:</b> {chef_tip}</div>', unsafe_allow_html=True)
                    
                    # Botón para guardar como PDF
                    pdf_bytes = create_pdf(recipe)
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