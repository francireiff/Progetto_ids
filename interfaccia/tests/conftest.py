import pytest
from django.contrib.auth import get_user_model
from interfaccia.models import (
    Utente, Paziente, Diabetologo, Farmaco,
    Terapia, RilevazioneGlicemia
)
from django.utils import timezone

@pytest.fixture
def utente_paziente():
    user = get_user_model().objects.create_user(
        username='paziente_test',
        password='password123',
        tipo='paziente'
    )
    return user

@pytest.fixture
def utente_medico():
    user = get_user_model().objects.create_user(
        username='medico_test',
        password='password123',
        tipo='medico'
    )
    return user

@pytest.fixture
def diabetologo(utente_medico):
    return Diabetologo.objects.create(
        utente=utente_medico,
        nome='Dottore',
        cognome='Test'
    )

@pytest.fixture
def paziente(utente_paziente, diabetologo):
    return Paziente.objects.create(
        utente=utente_paziente,
        nome='Paziente',
        cognome='Test',
        data_nascita='1990-01-01',
        medico_riferimento=diabetologo
    )

@pytest.fixture
def farmaco():
    return Farmaco.objects.create(
        nome='Insulina Test',
        tipo='insulina',
        descrizione='Farmaco di test'
    )

@pytest.fixture
def terapia(paziente, diabetologo, farmaco):
    data_oggi = timezone.now().date()
    data_fine = data_oggi.replace(year=data_oggi.year + 1)  # Un anno dopo
    return Terapia.objects.create(
        paziente=paziente,
        medico=diabetologo,
        farmaco=farmaco,
        data_inizio=data_oggi,
        data_fine=data_fine,
        numero_assunzioni_giornaliere=2,
        quantita_per_assunzione=1.0,
        indicazioni='Terapia di test'
    )