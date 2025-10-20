@echo off
setlocal ENABLEDELAYEDEXPANSION

REM === Racine du module ===
set "ROOT=app"

REM --- Dossiers ---
mkdir "%ROOT%" 2>nul
mkdir "%ROOT%\api" 2>nul
mkdir "%ROOT%\core" 2>nul
mkdir "%ROOT%\llm" 2>nul
mkdir "%ROOT%\agents" 2>nul
mkdir "%ROOT%\retrieval" 2>nul
mkdir "%ROOT%\storage" 2>nul
mkdir "%ROOT%\security" 2>nul
mkdir "%ROOT%\config" 2>nul
mkdir "%ROOT%\config\indexes" 2>nul
mkdir "%ROOT%\docs" 2>nul
mkdir "%ROOT%\utils" 2>nul

REM --- Fichiers racine ---
call :touch "%ROOT%\main.py"
call :touch "%ROOT%\settings.py"
call :touch "%ROOT%\container.py"
call :touch "%ROOT%\__init__.py"

REM --- api ---
call :touch "%ROOT%\api\__init__.py"
call :touch "%ROOT%\api\routes_health.py"
call :touch "%ROOT%\api\routes_auth.py"
call :touch "%ROOT%\api\routes_chat.py"
call :touch "%ROOT%\api\routes_docs.py"

REM --- core ---
call :touch "%ROOT%\core\__init__.py"
call :touch "%ROOT%\core\orchestrator.py"
call :touch "%ROOT%\core\pipeline.py"
call :touch "%ROOT%\core\typing.py"

REM --- llm ---
call :touch "%ROOT%\llm\__init__.py"
call :touch "%ROOT%\llm\base.py"
call :touch "%ROOT%\llm\gemini_client.py"
call :touch "%ROOT%\llm\openai_client.py"
call :touch "%ROOT%\llm\deepseek_client.py"
call :touch "%ROOT%\llm\factory.py"

REM --- agents ---
call :touch "%ROOT%\agents\__init__.py"
call :touch "%ROOT%\agents\base.py"
call :touch "%ROOT%\agents\agent_doc.py"
call :touch "%ROOT%\agents\agent_table.py"
call :touch "%ROOT%\agents\agent_vision.py"
call :touch "%ROOT%\agents\agent_trading.py"
call :touch "%ROOT%\agents\agent_hr.py"

REM --- retrieval ---
call :touch "%ROOT%\retrieval\__init__.py"
call :touch "%ROOT%\retrieval\search_client.py"
call :touch "%ROOT%\retrieval\filters.py"
call :touch "%ROOT%\retrieval\rank.py"

REM --- storage ---
call :touch "%ROOT%\storage\__init__.py"
call :touch "%ROOT%\storage\blob.py"
call :touch "%ROOT%\storage\tables.py"

REM --- security ---
call :touch "%ROOT%\security\__init__.py"
call :touch "%ROOT%\security\auth.py"

REM --- config ---
call :touch "%ROOT%\config\llm.yaml"
call :touch "%ROOT%\config\cors.yaml"
call :touch "%ROOT%\config\indexes\chunks.yaml"
call :touch "%ROOT%\config\indexes\finance.csv.yaml"
call :touch "%ROOT%\config\indexes\trading.yaml"
call :touch "%ROOT%\config\indexes\hr.yaml"

REM --- docs ---
call :touch "%ROOT%\docs\ARCHITECTURE.md"
call :touch "%ROOT%\docs\PIPELINE_CICD.md"
call :touch "%ROOT%\docs\API.md"

REM --- utils ---
call :touch "%ROOT%\utils\__init__.py"
call :touch "%ROOT%\utils\text.py"
call :touch "%ROOT%\utils\ids.py"
call :touch "%ROOT%\utils\logging.py"

echo ✅ Structure creee sous "%ROOT%".
goto :eof

:touch
REM crée un fichier vide seulement s'il n'existe pas
if not exist "%~1" (
  type nul > "%~1"
)
exit /b
