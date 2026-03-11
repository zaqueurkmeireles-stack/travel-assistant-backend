file_path = "main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Corrigindo o erro do caractere invisível e a falta de espaço
# Procura a parte quebrada e substitui pela correta
import re
# O padrão procura o caractere de alerta \x07 seguido de sync
pattern = r'@app\.on_event\("startup"\).*?sync def startup_event\(\):'
correct_block = '@app.on_event("startup")\nasync def startup_event():'

if "@app.on_event" in content:
    content = re.sub(pattern, correct_block, content)
    
    # Garantindo que não existam outros caracteres \x07 perdidos
    content = content.replace("\x07", "a") 

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Sintaxe corrigida! O 'a' de async foi restaurado e o caractere invisível removido.")
