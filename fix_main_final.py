import os

file_path = "main.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. Preparamos os imports essenciais
essential_imports = [
    "from app.services.scheduler_service import SchedulerService\n",
    "from loguru import logger\n",
    "import os\n"
]

# 2. Removemos imports duplicados ou mal posicionados para evitar o NameError
new_lines = []
seen_scheduler = False

for line in lines:
    if "from app.services.scheduler_service" in line:
        continue # Vamos reinserir no topo
    new_lines.append(line)

# Colocamos os novos imports logo no início
final_content = "".join(essential_imports) + "".join(new_lines)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(final_content)

print("✅ main.py atualizado! SchedulerService e Logger agora estão no radar.")
