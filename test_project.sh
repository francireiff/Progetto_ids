#!/bin/bash

# Script per testare il progetto Django DiabeticCare

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Inizia il test automatico del progetto DiabeticCare${NC}"

# Verifica che l'ambiente virtuale sia attivo o attivalo
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Ambiente virtuale non attivo, tentativo di attivazione...${NC}"
    if [[ -d "venv" ]]; then
        source venv/bin/activate
        echo -e "${GREEN}Ambiente virtuale attivato${NC}"
    else
        echo -e "${RED}Ambiente virtuale non trovato. Crealo con 'python -m venv venv'${NC}"
        exit 1
    fi
fi

# Verifica se Django è installato
echo -e "${YELLOW}Verifico le dipendenze...${NC}"
python -c "import django" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo -e "${RED}Django non è installato. Installa le dipendenze con 'pip install -r requirements.txt'${NC}"
    exit 1
fi

echo -e "${GREEN}Le dipendenze sono installate${NC}"

# Esegui le migrazioni
echo -e "${YELLOW}Esecuzione delle migrazioni...${NC}"
python manage.py makemigrations
if [[ $? -ne 0 ]]; then
    echo -e "${RED}Errore durante makemigrations${NC}"
    exit 1
fi

python manage.py migrate
if [[ $? -ne 0 ]]; then
    echo -e "${RED}Errore durante migrate${NC}"
    exit 1
fi

echo -e "${GREEN}Migrazioni completate con successo${NC}"

# Esegui i test
echo -e "${YELLOW}Esecuzione dei test automatici...${NC}"
pytest
if [[ $? -ne 0 ]]; then
    echo -e "${RED}Alcuni test non sono passati${NC}"
    exit 1
fi

echo -e "${GREEN}Tutti i test sono passati!${NC}"

# Avvia il server di sviluppo
echo -e "${YELLOW}Avvio del server di sviluppo...${NC}"
echo -e "${GREEN}Server di sviluppo avviato su http://127.0.0.1:8000/${NC}"
echo -e "${YELLOW}Premi CTRL+C per terminare il server${NC}"
python manage.py runserver