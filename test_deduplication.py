
import requests
import json
import time
import threading

def send_request(message_id, user_id, message):
    url = "http://localhost:8000/api/chat"
    payload = {
        "user_id": user_id,
        "message": message,
        "message_id": message_id,
        "push_name": "Teste Deduplicacao"
    }
    print(f"[*] Enviando request: {message_id}")
    try:
        response = requests.post(url, json=payload)
        print(f"[RES] {message_id}: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"[ERR] {message_id}: {e}")

def test_deduplication():
    # Enviar o mesmo message_id duas vezes rapidamente
    mid = f"test-dedup-{int(time.time())}"
    uid = "5511999999999"
    msg = "Teste de deduplicação"
    
    t1 = threading.Thread(target=send_request, args=(mid, uid, msg))
    t2 = threading.Thread(target=send_request, args=(mid, uid, msg))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()

if __name__ == "__main__":
    # Certifique-se que o servidor está rodando
    test_deduplication()
