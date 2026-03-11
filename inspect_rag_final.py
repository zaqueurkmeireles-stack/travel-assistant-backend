
import json
import os

db_path = "data/chroma_db/vector_data.json"

if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)
        data = full_data.get("documents", [])
        
    print(f"Total documents: {len(data)}")
    
    # List counts per user
    counts = {}
    for doc in data:
        uid = doc["metadata"].get("thread_id", "none")
        counts[uid] = counts.get(uid, 0) + 1
    
    print("Documents per user:")
    for uid, count in counts.items():
        print(f"  {uid}: {count}")

    # Inspect documents
    print("\nAll documents in RAG:")
    for i, doc in enumerate(data):
        meta = doc["metadata"]
        print(f"{i+1}. File: {meta.get('filename')} | TripID: {meta.get('trip_id')} | User: {meta.get('thread_id') or meta.get('user_id')}")
else:
    print("File not found.")
