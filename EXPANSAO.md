# Guia de Expansão - Como Adicionar Novas APIs

## Processo Simples em 3 Passos:

### PASSO 1: Adicionar no .env
Abra o arquivo .env e adicione sua nova API:
`NOVA_API_KEY=sua_chave_aqui`

### PASSO 2: Adicionar no app/config.py
Adicione o campo na classe Settings:
`NOVA_API_KEY: Optional[str] = None`

### PASSO 3: Usar nos seus serviços
Importe as configurações e use a chave em qualquer lugar do projeto:

    from app.config import settings
    print(settings.NOVA_API_KEY)
