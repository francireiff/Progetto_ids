import pytest
from interfaccia.forms import AssunzioneFarmacoForm

@pytest.mark.django_db
def test_validazione_quantita_assunzione(paziente, terapia):
    # Test con quantità negativa (dovrebbe fallire)
    form = AssunzioneFarmacoForm(
        data={'terapia': terapia.id, 'quantita': -1},
        paziente=paziente
    )
    assert not form.is_valid()
    assert 'quantita' in form.errors

    # Test con quantità zero (dovrebbe fallire)
    form = AssunzioneFarmacoForm(
        data={'terapia': terapia.id, 'quantita': 0},
        paziente=paziente
    )
    assert not form.is_valid()
    assert 'quantita' in form.errors

    # Test con quantità diversa da quella prescritta
    # Dovrebbe essere valido ma con avviso
    form = AssunzioneFarmacoForm(
        data={'terapia': terapia.id, 'quantita': 0.5},  # Diversa da 1.0
        paziente=paziente
    )
    assert not form.is_valid()
    assert 'quantita' in form.errors

    # Test con quantità corretta
    form = AssunzioneFarmacoForm(
        data={'terapia': terapia.id, 'quantita': 1.0},  # Uguale a quella prescritta
        paziente=paziente
    )
    assert form.is_valid()