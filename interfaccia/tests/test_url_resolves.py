from django.test import TestCase
from django.urls import reverse, resolve
from interfaccia import views

class TestURLResolves(TestCase):
    """
    Verifica che le URL vengano risolte nelle giuste viste
    """

    def test_home_url_resolves(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func, views.home)

    def test_dashboard_url_resolves(self):
        url = reverse('dashboard')
        self.assertEqual(resolve(url).func, views.dashboard)

    def test_paziente_dashboard_url_resolves(self):
        url = reverse('dashboard_paziente')
        self.assertEqual(resolve(url).func, views.dashboard_paziente)

    def test_medico_dashboard_url_resolves(self):
        url = reverse('dashboard_medico')
        self.assertEqual(resolve(url).func, views.dashboard_medico)

    def test_registrazione_paziente_url_resolves(self):
        url = reverse('registrazione_paziente')
        self.assertEqual(resolve(url).func.view_class, views.RegistrazionePazienteView)

    def test_glicemia_create_url_resolves(self):
        url = reverse('rileva_glicemia')
        self.assertEqual(resolve(url).func.view_class, views.RilevazioneGlicemiaCreateView)

    def test_lista_pazienti_url_resolves(self):
        url = reverse('lista_pazienti')
        self.assertEqual(resolve(url).func.view_class, views.ListaPazientiView)

    def test_grafico_glicemia_api_url_resolves(self):
        url = reverse('api_glicemia', args=[1])  # con un ID paziente di esempio
        self.assertEqual(resolve(url).func, views.grafico_glicemia)

    def test_prescrivere_terapia_url_resolves(self):
        url = reverse('prescrivi_terapia', args=[1])  # con un ID paziente di esempio
        self.assertEqual(resolve(url).func.view_class, views.TerapiaCreateView)