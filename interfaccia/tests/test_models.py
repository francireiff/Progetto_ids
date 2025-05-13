import pytest
from django.utils import timezone
from interfaccia.models import Alert, RilevazioneGlicemia

@pytest.mark.django_db
def test_alert_generato_da_valore_glicemico_alto(paziente):
    # Verifica che questo test crei correttamente un alert per valori glicemici anomali
    rilevazione = RilevazioneGlicemia.objects.create(
        paziente=paziente,
        valore=300,  # Valore alto che dovrebbe generare un alert
        momento='post',
        pasto='cena'
    )

    # Controlla che un alert sia stato creato
    alert = Alert.objects.filter(paziente=paziente).first()
    assert alert is not None
    assert alert.tipo == 'glicemia'
    assert alert.gravita == 'alta'  # Il valore 300 post-pasto è considerato grave