import pytest
from django.utils import timezone
from app.models import Terapia, Paziente, Diabetologo, Farmaco, Alert, RilevazioneGlicemia

@pytest.mark.django_db
def test_alert_generato_da_valore_glicemico_alto():
    paziente = Paziente.objects.create(nome='Mario', cognome='Rossi', data_nascita='1990-01-01')
    farmaco = Farmaco.objects.create(nome='Insulina A', tipo='insulina')
    medico = Diabetologo.objects.create(nome='Doc', cognome='Medico')
    paziente.medico_riferimento = medico
    paziente.save()

    rilevazione = RilevazioneGlicemia.objects.create(
        paziente=paziente, valore=300, momento='post', pasto='cena'
    )

    assert Alert.objects.filter(paziente=paziente).exists()