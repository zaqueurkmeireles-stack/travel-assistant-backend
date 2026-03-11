import json

print("--- VECTOR DATA ---")
try:
    with open('data/chroma_db/vector_data.json', 'r') as f:
        data = json.load(f)
        docs = data.get('documents', [])
        for i, d in enumerate(docs):
            print(f"Doc {i}: {d.get('metadata')}")
except Exception as e:
    print(f"Error reading vector_data: {e}")

print("\n--- USERS DB ---")
try:
    with open('data/users_db.json', 'r') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading users_db: {e}")

print("\n--- TRIPS DB ---")
try:
    with open('data/trips/trips_db.json', 'r') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading trips_db: {e}")
