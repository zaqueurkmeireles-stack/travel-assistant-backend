import os
import re

print("\n" + "="*70)
print("🗺️  RAIO-X COMPLETO: MAPA DE CLASSES E FUNÇÕES DO TRAVELCOMPANION")
print("="*70)

for root, dirs, files in os.walk("app"):
    if "__pycache__" in root: continue
    for file in files:
        if file.endswith(".py") and file != "__init__.py":
            filepath = os.path.join(root, file).replace("\\", "/")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                elements = []
                for line in lines:
                    # Captura a assinatura da classe ou função
                    if re.match(r'^\s*(class|async def|def)\s+', line):
                        # Limpa quebras de linha longas para caber na tela
                        clean_line = line.strip().split(')')[0] + (')' if '(' in line else '')
                        elements.append(clean_line)
                        
                if elements:
                    print(f"\n📁 {filepath}")
                    for el in elements:
                        if el.startswith("class"):
                            print(f"  🟦 {el}")
                        else:
                            print(f"    ⚙️ {el}")
            except Exception:
                pass
print("\n" + "="*70)
