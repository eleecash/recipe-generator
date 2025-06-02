# 🍳 Recipe Generator

A modern, AI-powered web application that generates personalized recipes based on your available ingredients and dietary preferences. Built with Streamlit and powered by Hugging Face Transformers for intelligent recipe creation.

## ✨ Features

- **🥕 Smart Recipe Generation**: Enter your available ingredients and get complete, creative recipes
- **🍃 Dietary Restrictions**: Support for Vegan, Gluten Free, Low Carb, Vegetarian, Dairy Free, and Normal diets
- **⚠️ Ingredient Validation**: Automatic conflict detection between ingredients and dietary preferences
- **🎨 Modern UI**: Beautiful, responsive interface with custom color palette
- **📊 Nutrition Information**: Displays estimated nutritional values for each generated recipe
- **👨‍🍳 Chef Tips**: Random cooking tips and suggestions for better flavor
- **📥 PDF Export**: Download recipes as beautifully formatted PDFs with vintage styling
- **🤖 AI-Powered**: Uses T5 transformer model fine-tuned specifically for recipe generation

## 🚀 Demo

Simply enter ingredients like "chicken, rice, tomatoes, onion", select your dietary preference, and watch as the AI creates a complete recipe with:
- Detailed ingredient list
- Step-by-step cooking instructions
- Nutritional information
- Professional chef tips

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/recipe-generator.git
   cd recipe-generator
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and navigate to `http://localhost:8501`

## 📦 Dependencies

```
streamlit==1.33.0
transformers==4.41.2
torch==2.3.0
pandas==2.2.2
requests==2.32.3
sentencepiece
fpdf
```

## 🎯 Usage

1. **Enter Ingredients**: Type your available ingredients separated by commas
2. **Select Diet**: Choose your dietary preference from the dropdown
3. **Generate Recipe**: Click the "Generate Recipe" button
4. **Review Results**: See your personalized recipe with ingredients, instructions, and nutrition info
5. **Download PDF**: Save your recipe as a professional PDF document

## 🏗️ Project Structure

```
recipe-generator/
├── app.py                 # Main Streamlit application
├── nutrition_estimator.py # Nutrition calculation utilities
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## 🧠 AI Model

This application uses the **flax-community/t5-recipe-generation** model from Hugging Face, which is specifically fine-tuned for recipe generation tasks. The model can create realistic and diverse recipes based on ingredient inputs.

## 🎨 Customization

### Color Palette
The app uses a carefully chosen color scheme:
- **Tea Green**: #c6d69b
- **Vanilla**: #f6e6b5  
- **Celtic Blue**: #3771b1
- **Ivory**: #faf8ee
- **Drab Dark Brown**: #343b1b

### Adding New Features
- **Chef Tips**: Edit `get_random_chef_tip()` function to add more cooking suggestions
- **Dietary Options**: Extend `diet_options` list and `validate_ingredients()` function
- **PDF Styling**: Modify `create_pdf()` function for different layouts

## 🔧 Configuration

### Nutrition API (Optional)
To get real nutritional data, configure the Edamam API:

1. Sign up at [Edamam Nutrition API](https://developer.edamam.com/)
2. Get your APP_ID and APP_KEY
3. Update `nutrition_estimator.py`:
   ```python
   app_id = "YOUR_APP_ID"
   app_key = "YOUR_APP_KEY"
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Hugging Face** for the T5 recipe generation model
- **Streamlit** for the amazing web app framework
- **FPDF** for PDF generation capabilities

## 🐛 Known Issues

- PDF generation requires latin1 compatible characters (emojis are converted to text)
- First run may be slow due to model downloading

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/recipe-generator/issues) on GitHub.

---

**Made with ❤️ for food lovers and developers @eleecash!**