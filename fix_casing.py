
import json
import os

def fix_trip_casing():
    print("--- Corrigindo Case Mismatch nos Trip IDs ---")
    
    # 1. Corrigir users_db.json
    users_path = "data/users_db.json"
    if os.path.exists(users_path):
        with open(users_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        for uid, udata in users.items():
            if "active_trip_id" in udata and udata["active_trip_id"]:
                parts = udata["active_trip_id"].split("_")
                if len(parts) >= 3:
                    parts[1] = parts[1].upper()
                    udata["active_trip_id"] = "_".join(parts)
            
            if "authorized_trips" in udata:
                new_auth = []
                for tid in udata["authorized_trips"]:
                    parts = tid.split("_")
                    if len(parts) >= 3:
                        parts[1] = parts[1].upper()
                        new_auth.append("_".join(parts))
                    else:
                        new_auth.append(tid)
                udata["authorized_trips"] = new_auth
        
        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
        print("users_db.json atualizado.")

    # 2. Corrigir trips.json
    trips_path = "data/trips.json"
    if os.path.exists(trips_path):
        with open(trips_path, 'r', encoding='utf-8') as f:
            trips = json.load(f)
        
        for trip in trips:
            parts = trip["id"].split("_")
            if len(parts) >= 3:
                parts[1] = parts[1].upper()
                trip["id"] = "_".join(parts)
            trip["destination"] = trip["destination"].upper()
            
        with open(trips_path, 'w', encoding='utf-8') as f:
            json.dump(trips, f, indent=2)
        print("trips.json atualizado.")

    # 3. Corrigir vector_data.json
    vector_path = "data/chroma_db/vector_data.json"
    if os.path.exists(vector_path):
        with open(vector_path, 'r', encoding='utf-8') as f:
            vdata = json.load(f)
        
        count = 0
        for doc in vdata.get("documents", []):
            tid = doc["metadata"].get("trip_id")
            if tid:
                parts = tid.split("_")
                if len(parts) >= 3:
                    parts[1] = parts[1].upper()
                    new_tid = "_".join(parts)
                    if new_tid != tid:
                        doc["metadata"]["trip_id"] = new_tid
                        count += 1
        
        with open(vector_path, 'w', encoding='utf-8') as f:
            json.dump(vdata, f, indent=2)
        print(f"vector_data.json: {count} documentos atualizados.")

if __name__ == "__main__":
    fix_trip_casing()
