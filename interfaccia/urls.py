from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

urlpatterns = [
    # Viste di base
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        authentication_form=LoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('registrazione/paziente/', views.RegistrazionePazienteView.as_view(), name='registrazione_paziente'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Dashboard
    path('dashboard/paziente/', views.dashboard_paziente, name='dashboard_paziente'),
    path('dashboard/medico/', views.dashboard_medico, name='dashboard_medico'),

    # Viste paziente - Glicemia
    path('paziente/glicemia/rileva/', views.RilevazioneGlicemiaCreateView.as_view(), name='rileva_glicemia'),
    path('paziente/glicemia/storico/', views.StoricoGlicemiaView.as_view(), name='storico_glicemia'),
    path('paziente/glicemia/grafico/', views.grafico_glicemia, name='grafico_glicemia'),

    # Viste paziente - Farmaci
    path('paziente/farmaco/assunzione/', views.AssunzioneFarmacoCreateView.as_view(), name='assunzione_farmaco'),
    path('paziente/farmaco/storico/', views.StoricoAssunzioniView.as_view(), name='storico_assunzioni'),

    # Viste paziente - Sintomi
    path('paziente/sintomo/segnala/', views.SintomoCreateView.as_view(), name='segnala_sintomo'),
    path('paziente/sintomo/storico/', views.StoricoSintomiView.as_view(), name='storico_sintomi'),

    # Viste paziente - Email
    path('paziente/email/invia/', views.EmailCreateView.as_view(), name='invia_email'),
    path('paziente/email/lista/', views.EmailListView.as_view(), name='lista_email_paziente'),
    path('paziente/email/<int:pk>/', views.EmailDetailView.as_view(), name='dettaglio_email_paziente'),

    # Viste medico - Pazienti
    path('medico/pazienti/', views.ListaPazientiView.as_view(), name='lista_pazienti'),
    path('medico/paziente/<int:pk>/', views.DettaglioPazienteView.as_view(), name='dettaglio_paziente'),
    path('medico/paziente/<int:pk>/aggiorna/', views.PazienteUpdateView.as_view(), name='aggiorna_paziente'),
    path('medico/paziente/<int:paziente_id>/terapia/prescrivere/', views.TerapiaCreateView.as_view(), name='prescrivi_terapia'),

    # Viste medico - Alert
    path('medico/alert/', views.AlertListView.as_view(), name='lista_alert'),
    path('medico/alert/<int:alert_id>/risolvi/', views.risolvi_alert, name='risolvi_alert'),

    # Viste medico - Email
    path('medico/email/lista/', views.EmailListView.as_view(), name='lista_email_medico'),
    path('medico/email/<int:pk>/', views.EmailDetailView.as_view(), name='dettaglio_email_medico'),

    # API per dati grafici (usato da entrambi pazienti e medici)
    path('api/glicemia/<int:paziente_id>/', views.grafico_glicemia, name='api_glicemia'),
]