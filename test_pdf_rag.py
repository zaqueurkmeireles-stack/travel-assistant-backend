"""
Teste direto: envia um PDF de boarding pass real ao endpoint do backend
para ver se o OCR/parse funciona e o conteúdo é indexado no RAG.
"""
import requests
import base64
import json
import os

# URL do backend (produção no Easypanel)
BACKEND_URL = "https://wsdfsdf-travel-assistant-backend.nkfiyw.easypanel.host"
USER_ID = "554188368783"

# 1. Verificar o estado atual do RAG
print("=== Estado atual do RAG (local) ===")
try:
    with open('data/chroma_db/vector_data.json', encoding='utf-8') as f:
        d = json.load(f)
    docs = d.get('documents', [])
    print(f"Docs no servidor local: {len(docs)}")
    for doc in docs:
        m = doc.get('metadata', {})
        if m.get('thread_id') == USER_ID:
            print(f"  >> Encontrado para {USER_ID}: {m.get('filename')} ({len(doc.get('text',''))} chars)")
except Exception as e:
    print(f"  Erro ao ler RAG local: {e}")

print("\n=== Testando endpoint de mídia com PDF de teste ===")

# 2. Criar um PDF de teste simples com conteúdo de boarding pass
teste_conteudo = """
BOARDING PASS - GOL LINHAS AÉREAS
Passageiro: BERNARDO NUNES MEIRELES
Voo: G3 1234
Data: 14 de Abril de 2026 - Terça-feira
Partida: SAO PAULO (GRU) - Terminal 2 - Gate B22
Horário de Embarque: 09:45
Horário de Decolagem: 10:30
Chegada: LISBOA (LIS) - Terminal 1
Horário de Chegada: 01:25 (15/04/2026)
Assento: 24F - Janela
Classe: Econômica
Número do Bilhete: 127-2876543210
Código de Barras: GOL-G31234-14APR-GRU-LIS
"""

# Criar um PDF simples em memória usando a lib reportlab se disponível, ou texto puro
pdf_bytes = None
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    import io
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in teste_conteudo.strip().split('\n'):
        c.drawString(72, y, line.strip())
        y -= 20
    c.save()
    pdf_bytes = buffer.getvalue()
    print("PDF gerado com reportlab")
except ImportError:
    # Fallback: usar o texto como bytes simulando um PDF simples
    # Criar um PDF válido mínimo com texto
    pdf_text = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(teste_conteudo) + 100} >>
stream
BT /F1 12 Tf 72 720 Td
{chr(10).join([f'({line.strip()}) Tj 0 -20 Td' for line in teste_conteudo.strip().split(chr(10)) if line.strip()])}
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000600 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
680
%%EOF"""
    pdf_bytes = pdf_text.encode('latin-1', errors='replace')
    print("PDF gerado manualmente (sem reportlab)")

# 3. Codificar em base64
pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
print(f"Base64 gerado: {len(pdf_b64)} chars")

# 4. Enviar ao endpoint
payload = {
    "user_id": USER_ID,
    "base64": pdf_b64,
    "filename": "boarding_pass_bernardo_teste.pdf",
    "mimetype": "application/pdf"
}

print(f"\nEnviando para {BACKEND_URL}/api/webhook/media ...")
try:
    resp = requests.post(
        f"{BACKEND_URL}/api/webhook/media",
        json=payload,
        timeout=60
    )
    print(f"Status: {resp.status_code}")
    print(f"Resposta: {resp.text[:500]}")
except Exception as e:
    print(f"Erro na requisição: {e}")

# 5. Testar o chat endpoint para ver se agora consegue responder
print("\n=== Testando chat após indexação ===")
import time
time.sleep(3)  # Aguardar indexação assíncrona

chat_payload = {
    "user_id": USER_ID,
    "message": "Que horas o Bernardo embarca? Qual é o horário do voo?"
}
try:
    resp = requests.post(
        f"{BACKEND_URL}/api/chat",
        json=chat_payload,
        timeout=60
    )
    print(f"Status do chat: {resp.status_code}")
    data = resp.json()
    print(f"Resposta da IA: {data.get('response', data)[:500]}")
except Exception as e:
    print(f"Erro no chat: {e}")
