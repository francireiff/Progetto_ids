from django.test import TestCase, Client
from django.urls import reverse
from interfaccia.models import Utente, Paziente, Diabetologo
from django.utils import timezone
from datetime import date

class TestURLs(TestCase):
    def setUp(self):
        # Crea un utente paziente di test
        self.paziente_user = Utente.objects.create_user(
            username='paziente_test',
            password='password123',
            tipo='paziente'
        )
        self.paziente = Paziente.objects.create(
            utente=self.paziente_user,
            nome='Nome',
            cognome='Cognome',
            data_nascita=date(1990, 1, 1)
        )

        # Crea un utente medico di test
        self.medico_user = Utente.objects.create_user(
            username='medico_test',
            password='password123',
            tipo='medico'
        )
        self.medico = Diabetologo.objects.create(
            utente=self.medico_user,
            nome='Dott',
            cognome='Medico'
        )

        # Associa il medico al paziente
        self.paziente.medico_riferimento = self.medico
        self.paziente.save()

        # Crea un client per fare richieste
        self.client = Client()

    def test_home_url(self):
        """Test della home page"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_login_url(self):
        """Test della pagina di login"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_registrazione_paziente_url(self):
        """Test della pagina di registrazione paziente"""
        response = self.client.get(reverse('registrazione_paziente'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirect_not_logged_in(self):
        """Test che la dashboard reindirizza al login se non autenticati"""
        response = self.client.get(reverse('dashboard'), follow=True)
        self.assertRedirects(
            response,
            f'/login/?next={reverse("dashboard")}'
        )

    def test_dashboard_paziente_logged_in(self):
        """Test accesso alla dashboard paziente quando autenticati come paziente"""
        # Login come paziente
        self.client.login(username='paziente_test', password='password123')
        response = self.client.get(reverse('dashboard'), follow=True)
        self.assertRedirects(response, reverse('dashboard_paziente'))

    def test_dashboard_medico_logged_in(self):
        """Test accesso alla dashboard medico quando autenticati come medico"""
        # Login come medico
        self.client.login(username='medico_test', password='password123')
        response = self.client.get(reverse('dashboard'), follow=True)
        self.assertRedirects(response, reverse('dashboard_medico'))

    def test_paziente_restricted_area(self):
        """Test che un medico non può accedere alle aree riservate ai pazienti"""
        # Login come medico
        self.client.login(username='medico_test', password='password123')
        response = self.client.get(reverse('rileva_glicemia'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_medico_restricted_area(self):
        """Test che un paziente non può accedere alle aree riservate ai medici"""
        # Login come paziente
        self.client.login(username='paziente_test', password='password123')
        response = self.client.get(reverse('lista_pazienti'))
        self.assertEqual(response.status_code, 403)  # Forbidden