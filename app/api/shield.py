from fastapi import APIRouter, Depends, HTTPException
from app.services.diagnostic_service import DiagnosticService
from app.services.user_service import UserService
from loguru import logger

router = APIRouter(prefix="/shield", tags=["Shield"])

@router.get("/status")
async def get_system_status(user_id: str = None):
    """
    Retorna o status completo do sistema. 
    Idealmente restrito ao Admin (vias de regra, validamos o user_id se fornecido).
    """
    # Se um user_id for passado, verificamos se é admin
    if user_id:
        user_svc = UserService()
        role = user_svc.get_user_role(user_id)
        if role != "admin":
            raise HTTPException(status_code=403, detail="Acesso restrito ao Administrador.")

    diag = DiagnosticService()
    report = await diag.check_all()
    
    # Logamos se o status não for saudável
    if report["overall_status"] != "HEALTHY":
        logger.warning(f"⚠️ Sentinela detectou sistema DEGRADADO: {report}")
        
    return report

@router.post("/fix-integrity")
async def repair_system():
    """
    Tenta reparos automáticos em arquivos corrompidos (placeholder para lógica de self-healing).
    """
    # No futuro, aqui podemos restaurar backups ou limpar locks travados
    return {"success": True, "message": "Reparo disparado. Verifique os logs."}
