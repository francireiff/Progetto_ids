@echo off
REM Script per testare il progetto Django DiabeticCare su Windows

echo ===========================================
echo Test automatico del progetto DiabeticCare
echo ===========================================

REM Verifica che l'ambiente virtuale sia attivo o attivalo
if "%VIRTUAL_ENV%"=="" (
    echo Ambiente virtuale non attivo, tentativo di attivazione...
    if exist venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
        echo Ambiente virtuale attivato
    ) else (
        echo Ambiente virtuale non trovato. Crealo con 'python -m venv venv'
        exit /b 1
    )
)

REM Verifica se Django è installato
echo Verifico le dipendenze...
python -c "import django" 2>nul
if errorlevel 1 (
    echo Django non è installato. Installa le dipendenze con 'pip install -r requirements.txt'
    exit /b 1
)

echo Le dipendenze sono installate

REM Esegui le migrazioni
echo Esecuzione delle migrazioni...
python manage.py makemigrations
if errorlevel 1 (
    echo Errore durante makemigrations
    exit /b 1
)

python manage.py migrate
if errorlevel 1 (
    echo Errore durante migrate
    exit /b 1
)

echo Migrazioni completate con successo

REM Esegui i test
echo Esecuzione dei test automatici...
pytest
if errorlevel 1 (
    echo Alcuni test non sono passati
    exit /b 1
)

echo Tutti i test sono passati!

REM Avvia il server di sviluppo
echo Avvio del server di sviluppo...
echo Server di sviluppo avviato su http://127.0.0.1:8000/
echo Premi CTRL+C per terminare il server
python manage.py runserver