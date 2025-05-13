from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import FormView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Max, Min, Count
from datetime import timedelta, date
import json

from .forms import (
    RegistrazionePazienteForm, RilevazioneGlicemiaForm, AssunzioneFarmacoForm,
    SintomoForm, TerapiaForm, EmailForm, PazienteUpdateForm
)
from .models import (
    Utente, Paziente, Diabetologo, RilevazioneGlicemia, AssunzioneFarmaco,
    Terapia, Sintomo, Alert, Email, LogOperazione
)

# Mixins per controllo accessi
class PazienteMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin per verificare che l'utente sia un paziente"""
    def test_func(self):
        return self.request.user.tipo == 'paziente'

class MedicoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin per verificare che l'utente sia un medico"""
    def test_func(self):
        return self.request.user.tipo == 'medico'

# Viste di base
def home(request):
    """Home page view"""
    return render(request, 'home.html')

class RegistrazionePazienteView(FormView):
    template_name = 'registrazione_paziente.html'
    form_class = RegistrazionePazienteForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

# Dashboard
@login_required
def dashboard(request):
    """Reindirizza alla dashboard appropriata in base al tipo di utente"""
    user = request.user
    if user.tipo == 'paziente':
        return redirect('dashboard_paziente')
    elif user.tipo == 'medico':
        return redirect('dashboard_medico')
    else:
        return redirect('admin:index')

# Dashboard Paziente
@login_required
def dashboard_paziente(request):
    """Dashboard per il paziente"""
    if request.user.tipo != 'paziente':
        return redirect('dashboard')

    paziente = request.user.profilo_paziente

    # Recupera gli ultimi dati del paziente
    rilevazioni = RilevazioneGlicemia.objects.filter(paziente=paziente).order_by('-data_ora')[:10]
    assunzioni = AssunzioneFarmaco.objects.filter(paziente=paziente).order_by('-data_ora')[:10]
    terapie_attive = Terapia.objects.filter(
        paziente=paziente,
        attiva=True,
        data_inizio__lte=date.today(),
        data_fine__gte=date.today()
    )
    alert_non_risolti = Alert.objects.filter(paziente=paziente, risolto=False).order_by('-data_ora')

    # Calcolo statistiche glicemia
    oggi = timezone.now().date()
    settimana_scorsa = oggi - timedelta(days=7)

    rilevazioni_settimana = RilevazioneGlicemia.objects.filter(
        paziente=paziente,
        data_ora__date__gte=settimana_scorsa
    )

    stat_glicemia = {
        'media': rilevazioni_settimana.aggregate(Avg('valore'))['valore__avg'],
        'max': rilevazioni_settimana.aggregate(Max('valore'))['valore__max'],
        'min': rilevazioni_settimana.aggregate(Min('valore'))['valore__min'],
        'count': rilevazioni_settimana.count()
    }

    context = {
        'paziente': paziente,
        'rilevazioni': rilevazioni,
        'assunzioni': assunzioni,
        'terapie_attive': terapie_attive,
        'alert_non_risolti': alert_non_risolti,
        'stat_glicemia': stat_glicemia,
    }

    return render(request, 'paziente/dashboard.html', context)

# Dashboard Medico
@login_required
def dashboard_medico(request):
    """Dashboard per il medico diabetologo"""
    if request.user.tipo != 'medico':
        return redirect('dashboard')

    medico = request.user.profilo_diabetologo

    # Recupera i dati rilevanti per il medico
    pazienti = Paziente.objects.filter(medico_riferimento=medico)
    alert_non_risolti = Alert.objects.filter(medico=medico, risolto=False).order_by('-gravita', '-data_ora')
    messaggi_non_letti = Email.objects.filter(medico_destinatario=medico, letto=False).count()

    # Pazienti con alert di glicemia alta negli ultimi 7 giorni
    oggi = timezone.now().date()
    settimana_scorsa = oggi - timedelta(days=7)

    pazienti_critici = Alert.objects.filter(
        medico=medico,
        tipo='glicemia',
        gravita='alta',
        data_ora__date__gte=settimana_scorsa
    ).values('paziente').annotate(count=Count('id')).order_by('-count')

    pazienti_critici_list = []
    for p in pazienti_critici:
        paziente_obj = Paziente.objects.get(id=p['paziente'])
        pazienti_critici_list.append({
            'paziente': paziente_obj,
            'alert_count': p['count']
        })

    context = {
        'medico': medico,
        'pazienti': pazienti,
        'alert_non_risolti': alert_non_risolti,
        'messaggi_non_letti': messaggi_non_letti,
        'pazienti_critici': pazienti_critici_list
    }

    return render(request, 'medico/dashboard.html', context)

# Gestione rilevazioni glicemia
class RilevazioneGlicemiaCreateView(PazienteMixin, CreateView):
    """Vista per inserire una nuova rilevazione glicemica"""
    model = RilevazioneGlicemia
    form_class = RilevazioneGlicemiaForm
    template_name = 'paziente/rileva_glicemia.html'
    success_url = reverse_lazy('dashboard_paziente')

    def form_valid(self, form):
        form.instance.paziente = self.request.user.profilo_paziente
        return super().form_valid(form)

class StoricoGlicemiaView(PazienteMixin, ListView):
    """Vista per visualizzare lo storico delle rilevazioni glicemiche"""
    model = RilevazioneGlicemia
    template_name = 'paziente/storico_glicemia.html'
    context_object_name = 'rilevazioni'
    paginate_by = 20

    def get_queryset(self):
        paziente = self.request.user.profilo_paziente
        return RilevazioneGlicemia.objects.filter(paziente=paziente).order_by('-data_ora')

@login_required
def grafico_glicemia(request, paziente_id=None):
    """API per fornire i dati per il grafico glicemico"""
    if request.user.tipo == 'paziente':
        paziente = request.user.profilo_paziente
    elif request.user.tipo == 'medico' and paziente_id:
        paziente = get_object_or_404(Paziente, id=paziente_id)
    else:
        return JsonResponse({'error': 'Operazione non consentita'}, status=403)

    # Periodo di tempo richiesto
    periodo = request.GET.get('periodo', 'settimana')
    oggi = timezone.now().date()

    if periodo == 'settimana':
        inizio = oggi - timedelta(days=7)
    elif periodo == 'mese':
        inizio = oggi - timedelta(days=30)
    else:  # anno
        inizio = oggi - timedelta(days=365)

    rilevazioni = RilevazioneGlicemia.objects.filter(
        paziente=paziente,
        data_ora__date__gte=inizio,
        data_ora__date__lte=oggi
    ).order_by('data_ora')

    dati = []
    for rilev in rilevazioni:
        dati.append({
            'data': rilev.data_ora.strftime('%Y-%m-%d %H:%M'),
            'valore': rilev.valore,
            'momento': rilev.get_momento_display(),
            'pasto': rilev.get_pasto_display()
        })

    return JsonResponse({'rilevazioni': dati})

# Gestione assunzioni farmaci
class AssunzioneFarmacoCreateView(PazienteMixin, CreateView):
    """Vista per registrare una nuova assunzione di farmaco"""
    model = AssunzioneFarmaco
    form_class = AssunzioneFarmacoForm
    template_name = 'paziente/assunzione_farmaco.html'
    success_url = reverse_lazy('dashboard_paziente')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['paziente'] = self.request.user.profilo_paziente
        return kwargs

    def form_valid(self, form):
        form.instance.paziente = self.request.user.profilo_paziente
        form.instance.farmaco = form.cleaned_data['terapia'].farmaco
        return super().form_valid(form)

class StoricoAssunzioniView(PazienteMixin, ListView):
    """Vista per visualizzare lo storico delle assunzioni di farmaci"""
    model = AssunzioneFarmaco
    template_name = 'paziente/storico_assunzioni.html'
    context_object_name = 'assunzioni'
    paginate_by = 20

    def get_queryset(self):
        paziente = self.request.user.profilo_paziente
        return AssunzioneFarmaco.objects.filter(paziente=paziente).order_by('-data_ora')

# Gestione sintomi
class SintomoCreateView(PazienteMixin, CreateView):
    """Vista per segnalare un nuovo sintomo"""
    model = Sintomo
    form_class = SintomoForm
    template_name = 'paziente/segnala_sintomo.html'
    success_url = reverse_lazy('dashboard_paziente')

    def form_valid(self, form):
        form.instance.paziente = self.request.user.profilo_paziente
        return super().form_valid(form)

class StoricoSintomiView(PazienteMixin, ListView):
    """Vista per visualizzare lo storico dei sintomi"""
    model = Sintomo
    template_name = 'paziente/storico_sintomi.html'
    context_object_name = 'sintomi'
    paginate_by = 20

    def get_queryset(self):
        paziente = self.request.user.profilo_paziente
        return Sintomo.objects.filter(paziente=paziente).order_by('-data_inizio')

# Viste per medici
class ListaPazientiView(MedicoMixin, ListView):
    """Vista per visualizzare l'elenco dei pazienti"""
    model = Paziente
    template_name = 'medico/lista_pazienti.html'
    context_object_name = 'pazienti'

    def get_queryset(self):
        medico = self.request.user.profilo_diabetologo
        return Paziente.objects.filter(medico_riferimento=medico)

class DettaglioPazienteView(MedicoMixin, DetailView):
    """Vista per visualizzare i dettagli di un paziente"""
    model = Paziente
    template_name = 'medico/dettaglio_paziente.html'
    context_object_name = 'paziente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paziente = self.object

        # Recupera i dati del paziente
        rilevazioni_recenti = RilevazioneGlicemia.objects.filter(paziente=paziente).order_by('-data_ora')[:10]
        assunzioni_recenti = AssunzioneFarmaco.objects.filter(paziente=paziente).order_by('-data_ora')[:10]
        terapie_attive = Terapia.objects.filter(paziente=paziente, attiva=True)
        sintomi_attivi = Sintomo.objects.filter(paziente=paziente, data_fine__isnull=True)
        alert_non_risolti = Alert.objects.filter(paziente=paziente, risolto=False)

        # Calcolo statistiche glicemia
        oggi = timezone.now().date()
        settimana_scorsa = oggi - timedelta(days=7)
        mese_scorso = oggi - timedelta(days=30)

        rilevazioni_settimana = RilevazioneGlicemia.objects.filter(
            paziente=paziente,
            data_ora__date__gte=settimana_scorsa
        )

        rilevazioni_mese = RilevazioneGlicemia.objects.filter(
            paziente=paziente,
            data_ora__date__gte=mese_scorso
        )

        stat_glicemia_settimana = {
            'media': rilevazioni_settimana.aggregate(Avg('valore'))['valore__avg'],
            'max': rilevazioni_settimana.aggregate(Max('valore'))['valore__max'],
            'min': rilevazioni_settimana.aggregate(Min('valore'))['valore__min'],
            'count': rilevazioni_settimana.count()
        }

        stat_glicemia_mese = {
            'media': rilevazioni_mese.aggregate(Avg('valore'))['valore__avg'],
            'max': rilevazioni_mese.aggregate(Max('valore'))['valore__max'],
            'min': rilevazioni_mese.aggregate(Min('valore'))['valore__min'],
            'count': rilevazioni_mese.count()
        }

        context.update({
            'rilevazioni_recenti': rilevazioni_recenti,
            'assunzioni_recenti': assunzioni_recenti,
            'terapie_attive': terapie_attive,
            'sintomi_attivi': sintomi_attivi,
            'alert_non_risolti': alert_non_risolti,
            'stat_glicemia_settimana': stat_glicemia_settimana,
            'stat_glicemia_mese': stat_glicemia_mese,
        })

        return context

class PazienteUpdateView(MedicoMixin, UpdateView):
    """Vista per aggiornare le informazioni di un paziente"""
    model = Paziente
    form_class = PazienteUpdateForm
    template_name = 'medico/aggiorna_paziente.html'

    def get_success_url(self):
        return reverse('dettaglio_paziente', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)

        # Crea log dell'operazione
        LogOperazione.objects.create(
            medico=self.request.user.profilo_diabetologo,
            paziente=self.object,
            tipo_operazione="Aggiornamento informazioni paziente",
            dettagli="Aggiornate informazioni paziente"
        )

        return response

class TerapiaCreateView(MedicoMixin, CreateView):
    """Vista per prescrivere una nuova terapia"""
    model = Terapia
    form_class = TerapiaForm
    template_name = 'medico/prescrivi_terapia.html'

    def dispatch(self, request, *args, **kwargs):
        self.paziente = get_object_or_404(Paziente, pk=self.kwargs['paziente_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paziente'] = self.paziente
        return context

    def form_valid(self, form):
        form.instance.paziente = self.paziente
        form.instance.medico = self.request.user.profilo_diabetologo
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('dettaglio_paziente', kwargs={'pk': self.paziente.pk})

class AlertListView(MedicoMixin, ListView):
    """Vista per visualizzare gli alert"""
    model = Alert
    template_name = 'medico/lista_alert.html'
    context_object_name = 'alerts'
    paginate_by = 20

    def get_queryset(self):
        medico = self.request.user.profilo_diabetologo
        return Alert.objects.filter(medico=medico).order_by('-data_ora')

@login_required
def risolvi_alert(request, alert_id):
    """Funzione per risolvere un alert"""
    if request.user.tipo != 'medico':
        return JsonResponse({'error': 'Operazione non consentita'}, status=403)

    alert = get_object_or_404(Alert, id=alert_id, medico=request.user.profilo_diabetologo)
    alert.risolto = True
    alert.save()

    LogOperazione.objects.create(
        medico=request.user.profilo_diabetologo,
        paziente=alert.paziente,
        tipo_operazione="Risoluzione alert",
        dettagli=f"Risolto alert: {alert.descrizione}"
    )

    return JsonResponse({'success': True})

# Gestione email tra paziente e medico
class EmailCreateView(PazienteMixin, CreateView):
    """Vista per inviare un'email al medico"""
    model = Email
    form_class = EmailForm
    template_name = 'paziente/invia_email.html'
    success_url = reverse_lazy('dashboard_paziente')

    def form_valid(self, form):
        paziente = self.request.user.profilo_paziente
        form.instance.paziente_mittente = paziente
        form.instance.medico_destinatario = paziente.medico_riferimento
        return super().form_valid(form)

class EmailListView(LoginRequiredMixin, ListView):
    """Vista per visualizzare le email"""
    model = Email
    template_name = 'email_list.html'
    context_object_name = 'emails'
    paginate_by = 20

    def get_template_names(self):
        if self.request.user.tipo == 'paziente':
            return ['paziente/email_list.html']
        else:
            return ['medico/email_list.html']

    def get_queryset(self):
        user = self.request.user
        if user.tipo == 'paziente':
            return Email.objects.filter(paziente_mittente=user.profilo_paziente).order_by('-data_ora')
        elif user.tipo == 'medico':
            return Email.objects.filter(medico_destinatario=user.profilo_diabetologo).order_by('-data_ora')
        return Email.objects.none()

class EmailDetailView(LoginRequiredMixin, DetailView):
    """Vista per visualizzare il dettaglio di un'email"""
    model = Email
    template_name = 'email_detail.html'
    context_object_name = 'email'

    def get_template_names(self):
        if self.request.user.tipo == 'paziente':
            return ['paziente/email_detail.html']
        else:
            return ['medico/email_detail.html']

    def get_queryset(self):
        user = self.request.user
        if user.tipo == 'paziente':
            return Email.objects.filter(paziente_mittente=user.profilo_paziente)
        elif user.tipo == 'medico':
            emails = Email.objects.filter(medico_destinatario=user.profilo_diabetologo)
            # Imposta l'email come letta quando un medico la visualizza
            email_id = self.kwargs.get('pk')
            email = emails.filter(id=email_id).first()
            if email and not email.letto:
                email.letto = True
                email.save()
            return emails
        return Email.objects.none()