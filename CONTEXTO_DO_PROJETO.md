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