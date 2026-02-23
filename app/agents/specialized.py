"""
Agentes Especializados - Arquivista e Guia Proativo (Integração WhatsApp)
"""

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings
from loguru import logger

def get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=settings.OPENAI_API_KEY
    )

def agente_arquivista_consultor(documento_texto: str) -> str:
    """
    Agente responsável por ler documentos (passagens, reservas) e identificar lacunas.
    """
    logger.info("📄 Executando Agente Arquivista Consultor...")
    prompt = PromptTemplate.from_template(
        """Você é um Concierge de Viagens de Luxo extremamente proativo e organizado.
        Sua tarefa é analisar o documento de viagem abaixo e extrair as informações principais (datas, locais, localizadores).
        
        Além disso, você deve fazer uma 'Análise de Lacunas' (Gap Analysis). 
        Verifique se falta algo essencial para uma viagem internacional (ex: Seguro Viagem, Reserva de Carro, Hotel).
        Se faltar algo, crie uma mensagem educada e prestativa cobrando o usuário de forma natural.

        Documento recebido:
        {documento}
        
        Responda no seguinte formato JSON:
        {{
            "dados_extraidos": {{ "resumo": "..." }},
            "lacunas_identificadas": ["seguro viagem", "carro"],
            "mensagem_proativa_usuario": "Sua viagem está ficando ótima! Notei que..."
        }}
        """
    )
    
    chain = prompt | get_llm()
    resposta = chain.invoke({"documento": documento_texto})
    return resposta.content

def agente_guia_proativo(contexto_viagem: str, dias_para_viagem: int) -> str:
    """
    Agente que envia dicas e lembretes baseados na linha do tempo da viagem (D-7, D-1, D-0).
    """
    logger.info(f"📅 Executando Agente Guia Proativo (D-{dias_para_viagem})...")
    prompt = PromptTemplate.from_template(
        """Você é um Guia de Viagens Proativo. Faltam {dias} dias para a viagem do usuário.
        Baseado no contexto da viagem abaixo, gere um lembrete útil, amigável e conciso (ideal para WhatsApp).
        
        Contexto da Viagem: {contexto}
        
        Regras:
        - Se faltam 7 dias (D-7): Lembre de documentos, vistos e sugira checklist de mala.
        - Se falta 1 dia (D-1): Lembre do check-in e mudança de clima.
        - Se é o dia do voo (D-0): Dê orientações de aeroporto.
        
        Mensagem para o WhatsApp:"""
    )
    
    chain = prompt | get_llm()
    resposta = chain.invoke({"contexto": contexto_viagem, "dias": dias_para_viagem})
    return resposta.content
