@echo off
REM ====================================================================
REM SÛRCHECK AI — Démarrage du backend FastAPI (développement local)
REM ====================================================================

echo.
echo  [SurCheck API] Demarrage du serveur FastAPI...
echo.

cd /d %~dp0

REM Activation du virtualenv
call .venv\Scripts\activate.bat

REM Chargement des variables d'environnement depuis la racine du projet
if exist "..\.env" (
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" "..\.env"`) do (
        set "%%A=%%B"
    )
)

REM Démarrage uvicorn avec rechargement automatique
.venv\Scripts\uvicorn.exe src.main:app --host 127.0.0.1 --port 8001 --reload --log-level info

pause
