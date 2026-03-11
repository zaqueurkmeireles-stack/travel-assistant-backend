import re

file_path = "main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Verifica se o import já existe, se não, adiciona
if "from app.services.scheduler_service import SchedulerService" not in content:
    content = "from app.services.scheduler_service import SchedulerService\n" + content

# Injeta a inicialização do Scheduler no evento de startup do FastAPI
startup_pattern = r'(@app\.on_event\("startup"\)\s+async def startup_event\(\):)'
if "@app.on_event(\"startup\")" in content:
    # Se já tem o evento, injetamos dentro dele
    content = re.sub(startup_pattern, r'\1\n    scheduler = SchedulerService()\n    scheduler.start()', content)
else:
    # Se não tem o evento, criamos um novo antes das rotas
    content = content.replace("app = FastAPI", "app = FastAPI()\n\n@app.on_event(\"startup\")\async def startup_event():\n    scheduler = SchedulerService()\n    scheduler.start()")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("🚀 Motor de Proatividade Antigravity devidamente acoplado ao main.py!")
