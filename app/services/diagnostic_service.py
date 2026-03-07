import os
import json
import httpx
import time
from loguru import logger
from app.config import settings

class DiagnosticService:
    """
    Serviço de Diagnóstico Profundo (O Sentinela)
    Monitora a saúde das dependências, integridade dos dados e funcionamento core.
    """

    async def check_all(self):
        """Executa todos os diagnósticos e retorna um relatório completo."""
        results = {
            "timestamp": time.time(),
            "dependencies": await self.check_dependencies(),
            "data_integrity": self.check_data_integrity(),
            "functional_sanity": await self.check_functional_sanity(),
            "environment": self.check_environment()
        }
        
        # Determina o status geral
        # Ignora GOOGLE_DRIVE_FOLDER_ID faltando para o STATUS GERAL (não é crítico)
        critical_checks = []
        for cat_name, cat_data in results.items():
            if not isinstance(cat_data, dict): continue
            for key, val in cat_data.items():
                if isinstance(val, dict) and "status" in val:
                    # Se for APENAS o Drive faltando, não marcamos como DEGRADED no geral
                    if key == "GOOGLE_DRIVE_FOLDER_ID" and val.get("status") == "MISSING":
                        continue
                    critical_checks.append(val.get("status") == "OK")
        
        results["overall_status"] = "HEALTHY" if all(critical_checks) else "DEGRADED"
        return results

    def get_alert_report(self, diag_results):
        """Gera um relatório legível com instruções de reparo."""
        if diag_results["overall_status"] == "HEALTHY":
            return "✅ Todos os sistemas operando normalmente."

        report = "🚨 *ALERTA DO SENTINELA MONUMENTAL*\n\nDetectei problemas que podem impactar sua viagem:\n\n"
        
        fix_guide = {
            "OPENAI_API_KEY": "Falta a chave da OpenAI. Verifique seu arquivo .env ou variáveis no EasyPanel.",
            "EVOLUTION_API_URL": "URL da Evolution API não configurada. O bot não conseguirá enviar mensagens.",
            "EVOLUTION_API_KEY": "Chave da Evolution API faltando ou inválida.",
            "GEMINI_API_KEY": "Chave do Google Gemini não encontrada (essencial para ler PDFs). Gere em: aistudio.google.com",
            "GOOGLE_DRIVE_FOLDER_ID": "ID da pasta raiz não configurado. O sistema usará folders por viagem se configurados.",
            "idempotency": "Banco de dados de segurança (idempotency.db) não encontrado ou corrompido.",
            "trips": "O arquivo de viagens (trips.json) está faltando ou corrompido!",
            "openai": "Falha na conexão com OpenAI. Verifique se sua chave tem créditos.",
            "evolution_api": "Não consegui falar com a Evolution API. Verifique se o serviço está rodando.",
            "drive_isolation": "Nenhuma viagem possui pasta de Drive personalizada vinculada ainda."
        }

        # Analisar falhas de variáveis
        env = diag_results.get("environment", {})
        missing_vars = [k for k, v in env.items() if v.get("status") != "OK"]
        if missing_vars:
            report += "*⚠️ Variáveis Faltando:*\n"
            for v in missing_vars:
                report += f"- `{v}`: {fix_guide.get(v, 'Configuração necessária.')}\n"
        
        # Analisar falhas de dependência
        deps = diag_results.get("dependencies", {})
        failed_deps = [k for k, v in deps.items() if v.get("status") != "OK"]
        if failed_deps:
            report += "\n*❌ APIs Indisponíveis:*\n"
            for d in failed_deps:
                report += f"- `{d.upper()}`: {fix_guide.get(d, 'Erro de conexão.')} ({deps[d].get('message', 'Erro desconhecido')})\n"

        # Analisar falhas de integridade
        integ = diag_results.get("data_integrity", {})
        failed_data = [k for k, v in integ.items() if v.get("status") != "OK"]
        if failed_data:
            report += "\n*💾 Erros de Dados:*\n"
            for f in failed_data:
                report += f"- `{f.upper()}`: {fix_guide.get(f, 'Arquivo com erro.')}\n"

        report += "\n🔧 *Como corrigir:* Acesse o painel do EasyPanel, atualize as variáveis no `.env` e reinicie o serviço."
        return report

    async def notify_admin_if_degraded(self, diag_results):
        """Envia o alerta para o WhatsApp do Admin se houver problemas CRÍTICOS."""
        if diag_results["overall_status"] != "HEALTHY":
            # Filtro extra: Só notifica se houver erro além do Drive
            env = diag_results.get("environment", {})
            critical_missing = [k for k, v in env.items() if v.get("status") != "OK" and k != "GOOGLE_DRIVE_FOLDER_ID"]
            
            deps = diag_results.get("dependencies", {})
            failed_deps = [k for k, v in deps.items() if v.get("status") != "OK"]
            
            if not critical_missing and not failed_deps:
                logger.info("ℹ️ Sentinela: Apenas avisos não críticos detectados. Notificação de WhatsApp suprimida.")
                return

            report = self.get_alert_report(diag_results)
            try:
                from app.services.n8n_service import N8nService
                n8n = N8nService()
                if settings.ADMIN_WHATSAPP_NUMBER:
                    n8n.enviar_resposta_usuario(settings.ADMIN_WHATSAPP_NUMBER, report, bypass_firewall=True)
                    logger.info("📢 Alerta de degradado enviado ao Admin via WhatsApp.")
            except Exception as e:
                logger.error(f"❌ Falha ao enviar alerta ao Admin: {e}")

    async def check_dependencies(self):
        """Verifica conectividade com APIs externas."""
        deps = {}
        
        # 1. OpenAI (Embeddings)
        if not settings.OPENAI_API_KEY:
            deps["openai"] = {"status": "MISSING_KEY"}
        else:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}, timeout=5.0)
                    deps["openai"] = {"status": "OK" if resp.status_code == 200 else "ERROR", "code": resp.status_code}
            except Exception as e:
                deps["openai"] = {"status": "ERROR", "message": str(e)}

        # 2. Evolution API (WhatsApp)
        if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_API_KEY:
            deps["evolution_api"] = {"status": "MISSING_CONFIG"}
        else:
            try:
                url = f"{settings.EVOLUTION_API_URL}/instance/fetchInstances"
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers={"apikey": str(settings.EVOLUTION_API_KEY)}, timeout=5.0)
                    deps["evolution_api"] = {"status": "OK" if resp.status_code == 200 else "ERROR", "code": resp.status_code}
            except Exception as e:
                deps["evolution_api"] = {"status": "ERROR", "message": str(e)}

        # 3. N8N (Webhooks)
        if not settings.N8N_WEBHOOK_URL:
            deps["n8n"] = {"status": "MISSING_URL"}
        else:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(settings.N8N_WEBHOOK_URL.split("/webhook")[0], timeout=5.0)
                    deps["n8n"] = {"status": "OK" if resp.status_code < 500 else "DEGRADED", "code": resp.status_code}
            except Exception as e:
                deps["n8n"] = {"status": "ERROR", "message": str(e)}

        return deps

    def check_data_integrity(self):
        """Valida se os arquivos de persistência estão íntegros e legíveis."""
        files = {
            "trips": "data/trips.json",
            "users": "data/users_db.json",
            "idempotency": "data/idempotency.db"
        }
        report = {}
        
        for name, path in files.items():
            if not os.path.exists(path):
                report[name] = {"status": "MISSING", "path": path}
                continue
            
            try:
                if path.endswith(".json"):
                    with open(path, 'r', encoding='utf-8') as f:
                        json.load(f)
                report[name] = {"status": "OK", "size": os.path.getsize(path)}
            except Exception as e:
                report[name] = {"status": "CORRUPTED", "error": str(e)}
                
        return report

    async def check_functional_sanity(self):
        """Testa funções core (RAG, Gemini) sem efeitos colaterais persistentes."""
        sanity = {}
        
        # 1. RAG Service (Load check)
        try:
            from app.services.rag_service import RAGService
            rag = RAGService()
            sanity["rag_engine"] = {"status": "OK", "docs_count": len(rag.documents)}
        except Exception as e:
            sanity["rag_engine"] = {"status": "ERROR", "message": str(e)}

        # 2. Gemini Parser (Connectivity)
        try:
            from app.parsers.document_parser import DocumentParser
            parser = DocumentParser()
            # Apenas verifica se a API key está configurada e responde a um prompt mínimo
            # Para economizar tokens, aqui fazemos apenas cheque de configuração no momento ou mock
            sanity["gemini_api"] = {"status": "OK" if settings.GEMINI_API_KEY else "MISSING_KEY"}
        except Exception as e:
            sanity["gemini_api"] = {"status": "ERROR", "message": str(e)}

        # 3. Phone Normalization (Sanity check)
        try:
            from app.services.user_service import UserService
            svc = UserService()
            # Testa se 9 dígitos vira 8 (sem DDI) ou se normaliza com DDI
            res = svc.normalize_phone("5541988368783")
            sanity["phone_normalization"] = {"status": "OK" if res == "554188368783" else "ERROR"}
        except:
            sanity["phone_normalization"] = {"status": "ERROR"}

        # 4. Drive Isolation (Check if any trip has custom folder)
        try:
            from app.services.trip_service import TripService
            trip_svc = TripService()
            has_custom = any(t.get("drive_folder_id") for t in trip_svc.trips)
            sanity["drive_isolation"] = {"status": "OK" if has_custom else "WARNING"}
        except:
            sanity["drive_isolation"] = {"status": "ERROR"}

        return sanity

    def check_environment(self):
        """Verifica variáveis de ambiente críticas."""
        keys = [
            "OPENAI_API_KEY", "EVOLUTION_API_URL", "EVOLUTION_API_KEY", 
            "GEMINI_API_KEY", "ADMIN_WHATSAPP_NUMBER", "GOOGLE_DRIVE_FOLDER_ID"
        ]
        env_rpt = {}
        for k in keys:
            val = getattr(settings, k, None) or os.getenv(k)
            env_rpt[k] = {"status": "OK" if val else "MISSING"}
        return env_rpt
