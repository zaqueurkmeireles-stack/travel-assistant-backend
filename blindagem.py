import asyncio
import sys
import os
import json
from loguru import logger

# Adiciona o diretório atual ao path para importar os módulos do app
sys.path.append(os.getcwd())

async def run_blindagem():
    """
    Script de Auditoria Monumental (Blindagem CLI)
    Executa um check-up completo do sistema e reporta no terminal.
    """
    print("\n" + "="*60)
    print("SISTEMA DE BLINDAGEM - SEVEN ASSISTANT TRAVEL")
    print("="*60)
    
    try:
        from app.services.diagnostic_service import DiagnosticService
        diag = DiagnosticService()
        
        print("\nIniciando diagnostico profundo...")
        results = await diag.check_all()
        
        # 1. Dependencias
        print("\nCONECTIVIDADE E APIs:")
        for dep, status in results["dependencies"].items():
            icon = "[OK]" if status.get("status") == "OK" else "[ERRO]"
            print(f"  {icon} {dep.upper()}: {status.get('status')} {status.get('message', '')}")
            
        # 2. Integridade de Dados
        print("\nINTEGRIDADE DE DADOS (JSON/DB):")
        for file, status in results["data_integrity"].items():
            icon = "[OK]" if status.get("status") == "OK" else "[ERRO]"
            print(f"  {icon} {file.upper()}: {status.get('status')} {status.get('error', '')}")
            
        # 3. Funcoes Core
        print("\nSANIDADE FUNCIONAL (RAG/AI):")
        for func, status in results["functional_sanity"].items():
            icon = "[OK]" if status.get("status") == "OK" else "[ERRO]"
            print(f"  {icon} {func.upper()}: {status.get('status')} {status.get('message', '')}")
            
        # 4. Ambiente
        print("\nVARIAVEIS DE AMBIENTE:")
        missing_env = [k for k, v in results["environment"].items() if v.get("status") != "OK"]
        if not missing_env:
            print("  [OK] Todas as variaveis criticas configuradas.")
        else:
            print(f"  [ERRO] VARIAVEIS FALTANDO: {', '.join(missing_env)}")

        print("\n" + "="*60)
        if results["overall_status"] == "HEALTHY":
            print("STATUS GERAL: TOTALMENTE PROTEGIDO / PRONTO PARA VIAGEM")
        else:
            print("STATUS GERAL: DEGRADADO - VERIFIQUE OS ITENS ACIMA")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO AO EXECUTAR BLINDAGEM: {e}")
        logger.exception("Falha no script de blindagem")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_blindagem())
