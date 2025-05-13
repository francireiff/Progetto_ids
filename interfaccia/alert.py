from django.utils import timezone
from datetime import timedelta, date
from interfaccia.models import Terapia, AssunzioneFarmaco, Alert

def verifica_assunzioni_farmaci():
    """
    Verifica se i pazienti stanno seguendo le terapie prescritte.
    - Genera alert per i medici se un paziente non segue la terapia per 3+ giorni
    - Genera promemoria per i pazienti
    """
    oggi = date.today()

    # Recupera tutte le terapie attive
    terapie_attive = Terapia.objects.filter(
        attiva=True,
        data_inizio__lte=oggi,
        data_fine__gte=oggi
    )

    for terapia in terapie_attive:
        paziente = terapia.paziente
        medico = terapia.medico

        # Controlla gli ultimi 3 giorni
        for giorni_indietro in range(3):
            data_controllo = oggi - timedelta(days=giorni_indietro)

            # Numero atteso di assunzioni per la giornata
            assunzioni_attese = terapia.numero_assunzioni_giornaliere

            # Numero effettivo di assunzioni per la giornata
            assunzioni_effettive = AssunzioneFarmaco.objects.filter(
                paziente=paziente,
                terapia=terapia,
                data_ora__date=data_controllo
            ).count()

            # Se le assunzioni sono meno di quelle previste
            if assunzioni_effettive < assunzioni_attese:
                assunzioni_mancanti = assunzioni_attese - assunzioni_effettive

                # Se è il giorno corrente, invia un promemoria al paziente
                if giorni_indietro == 0:
                    Alert.objects.create(
                        paziente=paziente,
                        medico=medico,
                        tipo='farmaco',
                        descrizione=f"Promemoria: Devi ancora assumere {assunzioni_mancanti} dose/i di {terapia.farmaco.nome} oggi",
                        gravita='bassa'
                    )

                # Se sono 3 giorni consecutivi di mancata assunzione, avvisa il medico
                if giorni_indietro == 2:
                    # Verifica se ci sono state assunzioni nei giorni precedenti
                    assunzioni_giorno_1 = AssunzioneFarmaco.objects.filter(
                        paziente=paziente,
                        terapia=terapia,
                        data_ora__date=oggi - timedelta(days=1)
                    ).count()

                    assunzioni_giorno_0 = AssunzioneFarmaco.objects.filter(
                        paziente=paziente,
                        terapia=terapia,
                        data_ora__date=oggi
                    ).count()

                    # Se in tutti e 3 i giorni ci sono state assunzioni mancanti
                    if (assunzioni_effettive < assunzioni_attese and
                            assunzioni_giorno_1 < assunzioni_attese and
                            assunzioni_giorno_0 < assunzioni_attese):

                        Alert.objects.create(
                            paziente=paziente,
                            medico=medico,
                            tipo='farmaco',
                            descrizione=f"Il paziente {paziente.nome} {paziente.cognome} non segue la terapia {terapia.farmaco.nome} da 3 giorni consecutivi",
                            gravita='alta'
                        )

def verifica_glicemie_anomale():
    """
    Verifica se ci sono pazienti con valori glicemici persistentemente anomali
    e genera alert con diversi livelli di gravità
    """
    # Implementazione del controllo dei valori glicemici anomali per periodi prolungati
    pass  # Questa funzione non è necessaria poiché gli alert per la glicemia vengono già generati nel metodo save() del modello

def genera_report_glicemia(paziente):
    """
    Genera un report settimanale/mensile delle glicemie per un paziente
    """
    # Implementazione del report di glicemia che può essere usato sia dai pazienti che dai medici
    pass  # Questa funzionalità è stata implementata direttamente nelle viste