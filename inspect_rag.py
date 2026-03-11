import json

with open('data/chroma_db/vector_data.json', encoding='utf-8') as f:
    d = json.load(f)

docs = d.get('documents', [])
print(f"Total docs: {len(docs)}")
for i, doc in enumerate(docs):
    m = doc.get('metadata', {})
    text = doc.get('text', '')
    print(f"\n--- Doc {i} ---")
    print(f"thread_id: {m.get('thread_id')}")
    print(f"filename: {m.get('filename')}")
    print(f"trip_id: {m.get('trip_id')}")
    print(f"text_len: {len(text)}")
    print(f"preview: {text[:200] if text else '(EMPTY)'}")
