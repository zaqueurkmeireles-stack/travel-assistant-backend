import asyncio
from app.services.user_service import UserService

async def test_authorization():
    # Suponha que temos admin e guest no DB
    admin = "554199999999"  # Substitua por admin real se necessário
    guest = "551199999999"

    service = UserService()
    # Mockando uma solicitação pendente
    service.users.setdefault(admin, {})
    service.users[admin]["role"] = "admin"
    service.users[admin]["pending_requests"] = {
        guest: "2026-02-27T10:00:00.000000"
    }
    service.set_active_trip(admin, "Test_Trip_123")
    service._save_users()
    
    # Agora vamos testar a lógica do endpoint simular
    
    active_trip = service.get_active_trip(admin)
    
    admin_user = service.get_user(admin)
    pending_requests = admin_user.get("pending_requests", {}) if admin_user else {}
    
    print("Pending requests:", pending_requests)
    
    if pending_requests:
        guest_id = sorted(pending_requests.items(), key=lambda x: x[1], reverse=True)[0][0]
        print(f"Guest mais recente: {guest_id}")
        
        if active_trip:
            success = service.authorize_guest(admin, guest_id, active_trip)
            print(f"Success authorization: {success}")
        else:
            print("No active trip")
    else:
        print("No pending requests")

if __name__ == "__main__":
    asyncio.run(test_authorization())
