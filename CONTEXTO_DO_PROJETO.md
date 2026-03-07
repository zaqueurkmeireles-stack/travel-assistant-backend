# CONTEXTO DO PROJETO: Travel Companion AI (Versão 1.0 & Visão de Futuro)

## 1. Visão Geral e Objetivo
O **Travel Companion AI** é um Concierge de Viagens inteligente, proativo e autônomo, operando 100% via WhatsApp. O objetivo é ser o melhor guia de viagens do mundo para indivíduos ou grupos familiares. 

O sistema não apenas responde perguntas, mas **antecipa necessidades**. Ele atua como um consultor ativo: recebe toda a documentação da viagem via WhatsApp, organiza em pastas seguras interligadas ao RAG, processa as informações e orquestra ações proativas através da arquitetura **LangGraph**. O robô guia o usuário passo a passo, focado em economizar tempo, dados de internet e evitar estresse.

## 2. Arquitetura Core e Estratégia de IA
- **Interface:** WhatsApp (via n8n + Evolution API).
- **Orquestração:** LangGraph (para fluxos de agentes complexos e cíclicos) e LangChain.
- **Estratégia de Modelos (V1.0):** Inicialmente, o sistema rodará **100% focado na API da OpenAI (GPT-4o)**, garantindo estabilidade e rapidez.
- **Design Agnóstico (Preparado para o Futuro):** Código modular para plugar facilmente Google Gemini, Anthropic Claude e outros modelos futuramente.
- **Consenso de IAs (Visão de Futuro):** Arquitetura prevendo múltiplas IAs debatendo entre si para chegar a um consenso perfeito antes de responder ao usuário.
- **Memória e Contexto (RAG):** PostgreSQL com `pgvector`. Separação estrita e segura por usuário/família e por viagem específica.
- **Geolocalização:** Leitura de localização em tempo real para disparar gatilhos contextuais.

## 3. Os Agentes Especialistas (LangGraph)

### 3.1. Agente de Ingestão, Organização e Análise de Lacunas (O Arquivista Consultor)
- **Função Principal:** Receber PDFs, imagens e textos via WhatsApp e salvar em pastas estruturadas e individualizadas (Usuário -> Viagem Específica).
- **Integração RAG:** Alimentar o banco de dados vetorial instantaneamente para que a IA tenha o contexto exato e isolado daquela viagem.
- **Ação Proativa (Gap Analysis):** Analisar a documentação recebida, cruzar com um checklist ideal de viagem e cobrar o usuário do que falta de forma natural.
- **Exemplo de Interação:** *"Sua viagem para Frankfurt está ficando ótima! Já guardei aqui suas passagens e a reserva do hotel. Mas notei que você ainda não me enviou o Seguro Viagem. Não esqueça de fazer um e me mandar a apólice para eu te ajudar rapidamente em caso de emergência médica. Ah, você vai alugar carro? Se sim, me mande o número da reserva também!"*

### 3.2. Agente de Checkpoints (O Guia Proativo)
- **D-7 (Uma semana antes):** Avisos de documentação, vistos e checklist de mala baseado no clima.
- **D-1 (Véspera):** Lembrete de check-in, localizadores consolidados e dicas de fuso horário.
- **D-0 (Dia do Voo - Origem):** Orientações de guichê e portão no aeroporto de origem.
- **D-0 (Chegada no Destino):** Opções de mapas offline (para poupar dados) e rota exata até a locadora de veículos ou hotel.

### 3.3. Agente de Monitoramento em Tempo Real (O Anjo da Guarda)
- **Função:** Monitorar APIs de voos e clima constantemente.
- **Ação:** Avisar sobre mudanças de portão, atrasos de voo ou mudanças bruscas de clima (Ex: *"Prepare-se para o frio em Frankfurt!"*).

### 3.4. Agente de Choque Cultural e Segurança (O Local)
- **Função:** Evitar gafes culturais e problemas legais baseado na geolocalização.
- **Exemplo:** *"Lembrete cultural: aqui não se pode beber na rua e é proibido fazer barulho após as 22h."*

### 3.6. Funcionalidades de Elite (V1.1 - Implementadas)
- **Match Inteligente:** O sistema detecta automaticamente sobreposição de viagens entre usuários (mesmo destino e data) e sugere a unificação do RAG para um planejamento compartilhado.
- **Autorização Passiva:** Novos usuários entram em uma lista de espera (`unauthorized`) e o administrador pode liberá-los com um simples comando ("sim [n]").
- **Micro-Navegação Proativa:** Ao detectar o pouso (Voo), o robô informa silenciosamente a esteira de bagagem e fornece mapas visuais e links para o balcão de aluguel de carro ou shuttle, sem que o usuário precise perguntar.
- **Dossiê Unificado:** Suporte a múltiplos passageiros no mesmo ID de viagem, permitindo que todos vejam os documentos uns dos outros de forma segura.
- **Gestão de Conflitos Humana:** O robô nunca descarta documentos sem perguntar. Se houver duplicidade ou irrelevância, ele solicita confirmação do usuário ("sim substituir" ou "sim incluir").

## 4. APIs e Integrações Necessárias (V1.0)
- **Voos:** FlightAware API ou AviationStack.
- **Clima:** OpenWeatherMap API ou WeatherAPI.
- **Mapas e Rotas:** Google Maps API e Mapbox (mapas offline).

## 5. Visão de Futuro (Preparando o Terreno para V2.0+)
1. **Consenso Multi-Agentes:** Integração definitiva do Gemini e Claude para validação cruzada.
2. **Agente de Milhas e Cartões:** Integração com APIs de programas de fidelidade para maximizar acúmulo de milhas e sugerir o melhor cartão.
3. **Agente Caçador de Passagens:** Monitoramento de preços via Skyscanner/Kiwi APIs.
4. **Integração com Wearables:** Sugerir pausas no roteiro baseado no cansaço físico do usuário.

## 6. Diretrizes de Desenvolvimento para o Agente Antigravity
- **Foco Inicial:** Construir a base sólida com OpenAI.
- **Modularidade:** Crie os nós do LangGraph de forma isolada.
- **Economia de Dados:** Sempre ofereça opções "low-data" (texto simples) antes de enviar mapas online.
- **Tratamento de Erros:** Se uma API externa falhar, o robô deve assumir graciosamente e avisar o usuário.
## 7. Contrato de Arquitetura e Padrões de Código (Para Agentes de IA)
Esta seção define as regras estritas de engenharia do repositório. Qualquer IA atuando neste projeto (Jules, Antigravity, etc.) **DEVE** seguir estas diretrizes ao implementar novas funcionalidades.

### 7.1. Estrutura de Diretórios e Responsabilidades
A organização do código obedece a uma separação estrita de conceitos. Novas implementações devem respeitar os seguintes domínios:

- `app/api/`: Contém apenas os roteadores (`routes.py`) e o Error Boundary global (`shield.py`). Função: receber requisições, retornar HTTP 200 rápido e despachar para background. Nenhuma regra de negócio deve ficar aqui.
- `app/services/`: O coração do sistema. Onde a lógica de negócio, regras de RAG, controle de banco de dados e integrações externas (APIs) vivem.
- `app/agents/`: Lógica do LangGraph.
  - `tools.py`: Toda capacidade interativa do robô (ações) deve ser mapeada aqui como uma `@tool`.
  - `orchestrator.py`: O cérebro do LangGraph que roteia qual agente/tool chamar.
- `app/models/`: Schemas de dados (Pydantic) e modelos de banco de dados. Qualquer tipagem estrita ou validação de payload deve nascer aqui.
- `app/parsers/`: Scripts exclusivos para extrair e normalizar dados de PDFs, imagens e comprovantes estruturados.
- `app/prompts/`: Todos os templates de texto, system prompts e personas das IAs devem ser isolados aqui (não hardcoded nos serviços).
- `app/utils/`: Funções utilitárias genéricas (formatação de data, limpeza de strings, etc.) que são usadas por múltiplos serviços.
- `data/`: Armazenamento de estado local (como `trips.json`, `vector_data.json` e o banco do `idempotency.db`). O código deve assumir que esta pasta exige travas de concorrência (Locks) para escrita.
- `tests/`: Onde moram todos os scripts de validação (`test_*.py`). Toda nova feature crítica deve ser acompanhada de um teste aqui usando pytest.
- `Raiz (Root)`: Arquivos de configuração (`main.py`, `.env`, `docker-compose.yml`) e scripts de deploy/blindagem.

### 7.2. Regras Imutáveis de Engenharia (NÃO QUEBRE)
1. **Idempotência (Obrigatório):** Todo evento de entrada da Evolution API passa pelo `IdempotencyService` (SQLite). Nunca modifique isso. O sistema não pode processar o mesmo webhook duas vezes.
2. **Tratamento de Erros (Shield):** É estritamente proibido usar `except Exception as e:` que devolva erros genéricos ao usuário ("Erro interno"). Use o Error Boundary Global (`shield.py`) e garanta fallbacks graciosos. Suprima erros de cota (429/400) das IAs nos logs.
3. **ACL e Identidade:** Todo telefone DEVE ser normalizado para o padrão E.164 pelo `UserService` antes de qualquer verificação de permissão de `trip_id`.
4. **Deduplicação Estrita:** Documentos nunca são substituídos baseados apenas em similaridade semântica. A deduplicação exige chaves exatas baseadas em `doc_type` (ex: PNR igual para voos).
5. **Isolamento de Dados:** Cada viagem possui seu próprio `trip_id` e seu próprio `drive_folder_id`. Os dados não se misturam.

## 8. Protocolo de Implementação de Novas Features (Instrução LLM)
Quando o desenvolvedor pedir para você (IA) implementar uma nova feature descrita nas seções acima (ex: "Integração com Uber"), você DEVE executar o seguinte fluxo de trabalho em lote:
1. **Service:** Crie o arquivo `[nome]_service.py` isolado em `app/services/`.
2. **Tool:** Registre a nova capacidade em `app/agents/tools.py` encapsulando a chamada do service.
3. **Orchestrator:** Atualize o prompt do sistema ou os nós do LangGraph em `app/agents/orchestrator.py` para que a IA saiba quando usar a nova tool.
4. **Env:** Adicione as novas variáveis de ambiente necessárias no `.env.example`.
5. **Documentação Viva (Auto-Atualização):** Se a implementação da nova feature exigir a criação de uma nova pasta estrutural na raiz do projeto (fora do escopo já documentado), você (IA) DEVE obrigatoriamente abrir este arquivo `CONTEXTO_DO_PROJETO.md`, ir até a Seção 7.1 e adicionar a explicação e a responsabilidade dessa nova pasta para manter o mapa arquitetônico sempre atualizado.