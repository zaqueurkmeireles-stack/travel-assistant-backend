import ast
import sys

file_path = 'c:/Users/ughdu/Documents/travel-assistant-backend/app/api/routes.py'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print("✅ Sintaxe OK!")
except SyntaxError as e:
    print(f"❌ Erro de Sintaxe: {e.msg}")
    print(f"Linha: {e.lineno}, Coluna: {e.offset}")
    print(f"Código: {e.text}")
except Exception as e:
    print(f"❌ Erro: {e}")
