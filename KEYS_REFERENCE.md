# 🔑 KEYS & INFRASTRUCTURE REFERENCE — TravelCompanion AI

> Arquivo de referência seguro para uso interno. NÃO versionar no git.

---

## 🌐 URLs Easypanel (Projeto: `wsdfsdf`)

| Serviço              | URL Pública (externa)                                              | URL Interna Docker              | Porta |
|----------------------|--------------------------------------------------------------------|---------------------------------|-------|
| **Backend AI**       | https://wsdfsdf-travel-assistant-backend.nkfiyw.easypanel.host     | http://travel-assistant-backend | 8000  |
| **Evolution API**    | https://wsdfsdf-evolution-api.nkfiyw.easypanel.host                | http://evolution-api            | 8080  |
| **n8n (Automação)**  | https://wsdfsdf-automacao.nkfiyw.easypanel.host                    | http://automacao                | 5678  |
| **Chatwoot**         | https://wsdfsdf-chatwoot.nkfiyw.easypanel.host                     | http://chatwoot                 | 3000  |
| **Easypanel Admin**  | http://76.13.161.84:3000/projects/wsdfsdf                          | —                               | 3000  |

---

## 📱 Evolution API

| Campo                | Valor                                                     |
|----------------------|-----------------------------------------------------------|
| **Global API Key**   | `429683C4C977415CAAFCCE10F7D57E11`                        |
| **Instância Bot**    | `Seven_Assistant`                                         |
| **Número do bot**    | 5541988624861 (Seven Assistent Travel)                    |
| **Token da instância** | `seven_token_123`                                       |
| **Webhook URL n8n**  | https://wsdfsdf-automacao.nkfiyw.easypanel.host/webhook/whatsapp-input |
| **webhookBase64**    | ✅ Ativo (envia PDFs/mídias como base64)                  |
| **Instância pessoal** | `viagem` (Rodrigo — 554188368783)                        |

---

## 🤖 IA e APIs de Serviços

| Serviço              | Tipo         | Chave/Token                                                                      | Status       |
|----------------------|--------------|----------------------------------------------------------------------------------|--------------|
| **OpenAI GPT-4o-mini** | AI principal | `sk-proj-OwQEbbYRKNx...` (ver .env)                                             | ✅ Ativo     |
| **Google Gemini**    | AI secundária | `AIzaSyA3it9_z1pLrOGiRqhdo5ix0_xJIXmCtY4`                                      | ✅ Ativo     |
| **Google Maps**      | Geolocalização | `AIzaSyAl-uUlCM-JDd398Qsa_tyhX-dVoOwB75o`                                     | ✅ Ativo     |
| **OpenWeather**      | Clima        | `6d2f79674c36b116946da1f15b85fc42`                                               | ✅ Ativo     |
| **SERP API**         | Busca Web    | `d2f12a493bbde4b34f1e4bff3de275206524c012c02ed7b03618ca5cf256bcb0`              | ✅ Ativo     |
| **ElevenLabs**       | Voz          | `sk_56d0072b7eaf744e3e912966a1a13b76afea02d59c074572`                            | ✅ Ativo     |
| **Foursquare**       | POI          | `fsqhDT4oMj2BxiTg7wM04qEJUDSV3P90blU5lzN7bVN9JM=`                             | ✅ Ativo     |
| **Duffel**           | Voos         | `duffel_test_wcTTFmQHQLkNSkBeq1dYwcbF33AJuKz9XFi8fKS8nDO`                      | ⚠️ TEST MODE |
| **Anthropic Claude** | AI terciária | `sk-ant-api03-bQHscUhPb...` (ver .env)                                           | ✅ Ativo     |

---

## 🔗 Endpoints Principais do Backend

| Endpoint                        | Método | Descrição                            |
|---------------------------------|--------|--------------------------------------|
| `/api/chat`                     | POST   | Chat principal com IA                |
| `/api/webhook/media`            | POST   | Recebe PDF/imagem via n8n            |
| `/webhook/whatsapp/media`       | POST   | Recebe mídia raw da Evolution API    |
| `/webhook/whatsapp/location`    | POST   | Recebe geolocalização                |
| `/api/health`                   | GET    | Health check                         |

---

## 📋 Números de WhatsApp

| Pessoa      | Número         | Papel           |
|-------------|----------------|-----------------|
| **Rodrigo** | 5541988368783  | Admin / Dono    |
| **Bot**     | 5541988624861  | Seven Assistant |

---

## 🔄 Fluxo n8n — Arquivo Atual

**Arquivo:** `n8n_workflow_final_v23.json`

- Webhook entrada: `whatsapp-input`
- Webhook saída IA: `ia-response`
- Todos os nós em `typeVersion: 1` (compatibilidade máxima)
- URLs internas Docker (sem HTTPS, sem domínio público)
- Chave Evolution: `429683C4C977415CAAFCCE10F7D57E11`

---

## ⚠️ Avisos

- O Duffel está em modo **TEST** — voos fictícios. Substituir por chave de produção quando lançar.
- O banco de dados PostgreSQL ainda usa placeholder (`postgresql://usuario:senha@host:5432/banco_de_dados`).
- A chave Anthropic e OpenAI ficam no `.env` (não comitar).
