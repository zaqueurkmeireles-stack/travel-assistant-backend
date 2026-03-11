import asyncio
import sys
import os

sys.path.append(os.getcwd())

async def test_proactive_alert():
    from app.services.diagnostic_service import DiagnosticService
    diag = DiagnosticService()
    
    print("Iniciando diagnostico para teste de alerta...")
    results = await diag.check_all()
    
    report = diag.get_alert_report(results)
    print("\n--- RELATORIO GERADO ---")
    print(report.encode('ascii', 'ignore').decode('ascii'))
    print("------------------------\n")
    
    if results["overall_status"] != "HEALTHY":
        print("Tentando enviar alerta para o WhatsApp do Admin...")
        await diag.notify_admin_if_degraded(results)
        print("Processo de envio concluido (Verifique os logs do N8N/Evolution).")
    else:
        print("Sistema esta saudável, nenhum alerta necessario.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_proactive_alert())
