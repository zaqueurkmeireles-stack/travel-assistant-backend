import base64
import os

files_to_copy = [
    'app/agents/orchestrator.py',
    'app/agents/tools.py',
    'app/services/user_service.py',
    'app/api/routes.py',
    'app/services/document_ingestor.py'
]

patch_code = """import os
import sys
import base64

def write_file(path, content_b64):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(base64.b64decode(content_b64))

base_dir = "/app"

"""

for f in files_to_copy:
    with open(f, 'rb') as file:
        content_b64 = base64.b64encode(file.read()).decode('utf-8')
    
    patch_code += f"""
try:
    write_file(os.path.join(base_dir, '{f}'), "{content_b64}")
    print("Sucesso: {f}")
except Exception as e:
    print(f"Erro em {f}: {{e}}")
"""

patch_code += """
print("\\nAtualizacao concluida! Por favor, reinicie a aplicacao no Easypanel.")
"""

with open('deploy_patch_sharing.py', 'w', encoding='utf-8') as f:
    f.write(patch_code)

import urllib.request
b64_script = base64.b64encode(patch_code.encode('utf-8')).decode('utf-8')
print(f"\\n\\n=== COMANDO PARA O EASIPANEL CONSOLE ===\\n\\necho {b64_script} | base64 -d > deploy.py && python deploy.py\\n\\n")
with open('deploy_patch_sharing.b64', 'w', encoding='utf-8') as f:
    f.write(b64_script)
