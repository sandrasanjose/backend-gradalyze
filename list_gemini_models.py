import google.generativeai as genai

api_key = "AIzaSyD9z5-rAAGbLc_6nLvbNzjI6Fqbq-b4XB4"
genai.configure(api_key=api_key)

for m in genai.list_models():
    print(m.name, m.supported_generation_methods)
