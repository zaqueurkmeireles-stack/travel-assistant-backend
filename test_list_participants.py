import sys
sys.path.insert(0, ".")

from app.services.user_service import UserService
from langchain_core.runnables import RunnableConfig

# Simular config do LangChain
config = {
    "configurable": {
        "thread_id": "5511999999999"  # Substitua por um user_id real
    }
}

# Instanciar serviço
user_svc = UserService()

# Testar get_active_trip
active_trip = user_svc.get_active_trip(config["configurable"]["thread_id"])
print(f"✅ Active Trip: {active_trip}")

# Testar list_trip_participants (simulado)
user_id = config.get("configurable", {}).get("thread_id", "default")
active_trip_id = user_svc.get_active_trip(user_id)

if not active_trip_id:
    print("❌ Nenhuma viagem ativa encontrada")
else:
    participants = []
    seen = set()
    
    for uid, data in user_svc.users.items():
        if not isinstance(data, dict):
            continue
        authorized = data.get("authorized_trips", []) or []
        if data.get("active_trip_id") == active_trip_id or active_trip_id in authorized:
            if uid in seen:
                continue
            seen.add(uid)
            name = data.get("name", uid)
            role = data.get("role", "guest")
            tag = "ativo" if data.get("active_trip_id") == active_trip_id else "autorizado"
            participants.append(f"- {name} ({role} | {tag})")
    
    if not participants:
        print("❌ Nenhum participante encontrado")
    else:
        dest = active_trip_id.split("_", 1)[1] if "_" in active_trip_id else active_trip_id
        result = f"Participantes com acesso a viagem para {dest}:\n" + "\n".join(participants)
        print("✅ Resultado:")
        print(result)
