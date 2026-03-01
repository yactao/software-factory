# app/services/agents_dev.py
import subprocess
import os
import uuid
from typing import Tuple

from app.services.llm_provider import llm_chat_completion

def generate_and_test_code(question: str, language: str) -> Tuple[str, str, str]:
    """
    Simaulation of a LLM Foundry Software Factory:
    1. Sends the requirement to an LLM
    2. Writes the generated code in a local temporary sandbox
    3. Runs the code and returns the console output
    """
    system_prompt = (
        "Tu es l'Usine Logicielle d'Aïna (Aïna Coder Foundry).\n"
        f"L'utilisateur veut un script en {language}.\n"
        "Génère uniquement le code source complet et fonctionnel, sans balises Markdown (ex: ```python), "
        "sans explications, juste le code brut qui peut être écrit directement dans un fichier et exécuté."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    # 1. Inférence LLM
    try:
        generated_code = llm_chat_completion(
            "dev_coder",
            messages,
            temperature=0.1,
            max_tokens=2000,
        )
    except Exception as e:
        return "", f"Erreur LLM: {str(e)}"
        
    generated_code = generated_code.strip()
    
    # Very basic cleanup of markdown if LLM disobeyed
    if generated_code.startswith("```"):
        lines = generated_code.split("\n")
        if lines[0].startswith("```"):
            lines.pop(0)
        if lines[-1].startswith("```"):
            lines.pop(-1)
        generated_code = "\n".join(lines).strip()
        
    # 2. Execution in Sandbox
    sandbox_dir = os.path.join(os.getcwd(), "sandbox")
    os.makedirs(sandbox_dir, exist_ok=True)
    
    conv_id = str(uuid.uuid4())
    run_dir = os.path.join(sandbox_dir, conv_id)
    os.makedirs(run_dir, exist_ok=True)
    
    ext = "js" if language.lower() in ["node", "javascript", "js"] else "py"
    cmd_runner = "node" if ext == "js" else "python"
    
    file_path = os.path.join(run_dir, f"main.{ext}")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(generated_code)
        
    # 3. Run safely
    try:
        result = subprocess.run(
            [cmd_runner, file_path], 
            cwd=run_dir, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        output = stdout
        if stderr:
             output += "\nErreur: " + stderr
             
        # Mock SAS logic
        sas_url = f"https://aina-foundry.blob.core.windows.net/sandbox/{conv_id}/code.zip?sv=factory-token"
             
        return generated_code, output, sas_url
    except subprocess.TimeoutExpired:
        return generated_code, "Erreur: Timeout lors de l'exécution en sandbox.", ""
    except Exception as e:
        return generated_code, f"Erreur Sandbox système: {str(e)}", ""
