import pytest
from app.forms import AssunzioneFarmacoForm
from app.models import Paziente, Terapia, Farmaco
from django.utils import timezone

@pytest.mark.django_db
def test_validazione_quantita_assunzione():
    paziente = Paziente.objects.create(nome='Anna', cognome='Bianchi', data_nascita='1985-06-06')
    farmaco = Farmaco.objects.create(nome='Metformina', tipo='orale')
    terapia = Terapia.objects.create(
        paziente=paziente,
        medico=None,
        farmaco=farmaco,
        data_inizio=timezone.now().date(),
        data_fine=timezone.now().date(),
        numero_assunzioni_giornaliere=2,
        quantita_per_assunzione=1.0
    )
    form = AssunzioneFarmacoForm(
        data={'terapia': terapia.id, 'quantita': 0.5},
        paziente=paziente
    )
    assert not form.is_valid()
    assert 'quantita' in form.errors
