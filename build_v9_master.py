import json

def build_v9():
    with open('n8n_workflow_final_v8_pro.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    nodes = data['nodes']
    connections = data['connections']
    
    # 1. Configurar Webhook para "onReceived" (Resolve o Responder OK)
    for node in nodes:
        if node['name'] == 'Webhook Entrada WhatsApp':
            node['parameters']['responseMode'] = 'onReceived'
            node['parameters']['responseData'] = '={"status": "ok"}'
            
    # Remover o "Responder OK" do json
    nodes = [n for n in nodes if n['name'] != 'Responder OK']
    if "Responder OK" in connections:
        del connections["Responder OK"]
        
    # Arrumar conexão: Filtro Segurança -> É Mídia
    connections["Filtro de Segurança (anti-loop e grupos)"]["main"][0] = [
        {
            "node": "É Mídia?",
            "type": "main",
            "index": 0
        }
    ]
            
    # 2. Centralizar URLs num Set node
    set_node = {
        "parameters": {
            "values": {
                "string": [
                    {
                        "name": "BACKEND_URL",
                        "value": "https://wsdfsdf-travel-assistant-backend.nkfiyw.easypanel.host"
                    },
                    {
                        "name": "EVOLUTION_URL",
                        "value": "https://wsdfsdf-evolution-api.nkfiyw.easypanel.host"
                    },
                    {
                        "name": "INSTANCE_NAME",
                        "value": "TravelAssistant"
                    }
                ]
            },
            "options": {}
        },
        "id": "node-variaveis-globais",
        "name": "Variáveis Globais",
        "type": "n8n-nodes-base.set",
        "typeVersion": 2,
        "position": [ 450, 300 ]
    }
    
    # Inserir o Set node após o filtro de seguranca
    connections["Filtro de Segurança (anti-loop e grupos)"]["main"][0][0]["node"] = "Variáveis Globais"
    connections["Variáveis Globais"] = {
        "main": [
            [
                {
                    "node": "É Mídia?",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }
    nodes.append(set_node)
    
    # 3. Mudar URLs harcoded e Error Handling dos HTTP Requests
    for node in nodes:
        if node['name'] == 'Enviar Texto p/ IA':
            node['parameters']['url'] = '={{ $json["BACKEND_URL"] }}/api/chat'
            node['parameters']['options'] = node['parameters'].get('options', {})
            node['parameters']['options']['continueOnFail'] = True
            
        elif node['name'] == 'Enviar Mídia p/ IA':
            node['parameters']['url'] = '={{ $json["BACKEND_URL"] }}/webhook/whatsapp/media'
            node['parameters']['options'] = node['parameters'].get('options', {})
            node['parameters']['options']['continueOnFail'] = True
            
        elif node['name'] == 'Enviar Localização p/ IA':
            node['parameters']['url'] = '={{ $json["BACKEND_URL"] }}/webhook/whatsapp/location'
            node['parameters']['options'] = node['parameters'].get('options', {})
            node['parameters']['options']['continueOnFail'] = True
            
        elif node['name'] == 'Enviar WhatsApp (Evolution)':
            node['parameters']['url'] = '={{ $json["EVOLUTION_URL"] }}/message/sendText/{{ $json["INSTANCE_NAME"] }}'
            node['parameters']['options'] = node['parameters'].get('options', {})
            node['parameters']['options']['continueOnFail'] = True
            # Remover API key hardcoded
            if 'headers' in node['parameters']:
                # The old logic used to put apikey here. Replacing with credentials.
                pass
            node['credentials'] = {
                "httpHeaderAuth": {
                    "id": "evolution_api_cred",
                    "name": "Evolution API"
                }
            }
            if 'name' in node['parameters'].get('headers', {}).get('name1', {}):
                node['parameters']['headers'] = {} # Clean it up to use credentials
                
    # 4. Nós de Erro
    error_node_texto = {
        "parameters": {
            "conditions": {
                "boolean": [
                    {
                        "value1": "={{ $json.error !== undefined }}",
                        "value2": True
                    }
                ]
            }
        },
        "id": "node-error-texto",
        "name": "Erro no Texto?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
        "position": [ 1300, 500 ]
    }
    
    error_node_midia = {
        "parameters": {
            "conditions": {
                "boolean": [
                    {
                        "value1": "={{ $json.error !== undefined }}",
                        "value2": True
                    }
                ]
            }
        },
        "id": "node-error-midia",
        "name": "Erro na Mídia?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
        "position": [ 1100, 100 ]
    }
    
    error_node_loc = {
        "parameters": {
            "conditions": {
                "boolean": [
                    {
                        "value1": "={{ $json.error !== undefined }}",
                        "value2": True
                    }
                ]
            }
        },
        "id": "node-error-loc",
        "name": "Erro na Loc?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
        "position": [ 1300, 300 ]
    }
    
    nodes.extend([error_node_texto, error_node_midia, error_node_loc])
    
    # Conectando saida pros IFs de erro
    connections["Enviar Texto p/ IA"] = { "main": [ [ { "node": "Erro no Texto?", "type": "main", "index": 0 } ] ] }
    connections["Enviar Mídia p/ IA"] = { "main": [ [ { "node": "Erro na Mídia?", "type": "main", "index": 0 } ] ] }
    connections["Enviar Localização p/ IA"] = { "main": [ [ { "node": "Erro na Loc?", "type": "main", "index": 0 } ] ] }
    
    # O pipeline 2 (Saida) estava ok, mas podemos aplicar a regra da credencial la tambem
    data['nodes'] = nodes
    data['connections'] = connections
    data['name'] = "TravelCompanion AI - Fluxo Final V9 Master"
    
    with open('n8n_workflow_final_v9_master.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

build_v9()
print("V9 Created")
