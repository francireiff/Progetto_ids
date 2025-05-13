from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Manager personalizzato per il modello Utente
class UserManager(BaseUserManager):
    def create_user(self, username, password=None, tipo=None, **extra_fields):
        if not username:
            raise ValueError('L\'username è obbligatorio')
        user = self.model(username=username, tipo=tipo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo', 'admin')

        return self.create_user(username, password, **extra_fields)

# Modello Utente esteso
class Utente(AbstractUser):
    TIPI_UTENTE = (
        ('paziente', 'Paziente'),
        ('medico', 'Diabetologo'),
        ('admin', 'Amministratore'),
    )

    tipo = models.CharField(max_length=10, choices=TIPI_UTENTE)
    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.get_tipo_display()})"

# Modello per il Diabetologo
class Diabetologo(models.Model):
    utente = models.OneToOneField(Utente, on_delete=models.CASCADE, related_name='profilo_diabetologo')
    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)

    def __str__(self):
        return f"Dr. {self.nome} {self.cognome}"

    class Meta:
        verbose_name = "Diabetologo"
        verbose_name_plural = "Diabetologi"

# Modello per il Paziente
class Paziente(models.Model):
    utente = models.OneToOneField(Utente, on_delete=models.CASCADE, related_name='profilo_paziente')
    medico_riferimento = models.ForeignKey(Diabetologo, on_delete=models.SET_NULL, null=True, related_name='pazienti')
    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    data_nascita = models.DateField()

    # Fattori di rischio
    fumatore = models.BooleanField(default=False)
    ex_fumatore = models.BooleanField(default=False)
    problemi_alcol = models.BooleanField(default=False)
    problemi_stupefacenti = models.BooleanField(default=False)
    obesita = models.BooleanField(default=False)

    # Patologie e comorbidità
    pregresse_patologie = models.TextField(blank=True)
    comorbidita = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nome} {self.cognome}"

    class Meta:
        verbose_name = "Paziente"
        verbose_name_plural = "Pazienti"

# Modello per i Farmaci
class Farmaco(models.Model):
    TIPI_FARMACO = (
        ('insulina', 'Insulina'),
        ('orale', 'Farmaco Antidiabetico Orale'),
    )

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPI_FARMACO)
    descrizione = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Farmaco"
        verbose_name_plural = "Farmaci"

# Modello per le Terapie
class Terapia(models.Model):
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='terapie')
    medico = models.ForeignKey(Diabetologo, on_delete=models.CASCADE, related_name='terapie_prescritte')
    farmaco = models.ForeignKey(Farmaco, on_delete=models.CASCADE, related_name='terapie')
    data_inizio = models.DateField()
    data_fine = models.DateField()
    numero_assunzioni_giornaliere = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    quantita_per_assunzione = models.FloatField(validators=[MinValueValidator(0.1)])
    indicazioni = models.TextField(blank=True)
    attiva = models.BooleanField(default=True)

    def __str__(self):
        return f"Terapia {self.farmaco.nome} per {self.paziente}"

    def save(self, *args, **kwargs):
        # Se è una nuova terapia, crea un log
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            LogOperazione.objects.create(
                medico=self.medico,
                paziente=self.paziente,
                tipo_operazione="Prescrizione terapia",
                dettagli=f"Prescritta terapia con {self.farmaco.nome}, {self.numero_assunzioni_giornaliere} volte al giorno"
            )

    class Meta:
        verbose_name = "Terapia"
        verbose_name_plural = "Terapie"

# Modello per le Rilevazioni di Glicemia
class RilevazioneGlicemia(models.Model):
    MOMENTI = (
        ('pre', 'Pre-pasto'),
        ('post', 'Post-pasto'),
    )

    PASTI = (
        ('colazione', 'Colazione'),
        ('pranzo', 'Pranzo'),
        ('cena', 'Cena'),
    )

    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='rilevazioni_glicemia')
    data_ora = models.DateTimeField(default=timezone.now)
    valore = models.FloatField(validators=[MinValueValidator(10), MaxValueValidator(600)])
    momento = models.CharField(max_length=4, choices=MOMENTI)
    pasto = models.CharField(max_length=10, choices=PASTI)

    def __str__(self):
        return f"Glicemia {self.paziente}: {self.valore} mg/dL ({self.get_momento_display()} {self.get_pasto_display()})"

    def is_normale(self):
        """Verifica se il valore glicemico è nei limiti normali"""
        if self.momento == 'pre':
            return 80 <= self.valore <= 130
        else:  # post-pasto
            return self.valore <= 180

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Verifica se il valore è fuori norma e genera un alert se necessario
        if not self.is_normale():
            # Determina la gravità dell'alert
            gravita = self._valuta_gravita()

            # Crea l'alert
            Alert.objects.create(
                paziente=self.paziente,
                medico=self.paziente.medico_riferimento,
                tipo='glicemia',
                descrizione=f"Valore glicemico anomalo: {self.valore} mg/dL ({self.get_momento_display()} {self.get_pasto_display()}). Gravità: {gravita}",
                gravita=gravita
            )

    def _valuta_gravita(self):
        """Valuta la gravità dell'anomalia glicemica"""
        if self.momento == 'pre':
            if self.valore < 60 or self.valore > 200:
                return 'alta'
            elif self.valore < 70 or self.valore > 160:
                return 'media'
            else:
                return 'bassa'
        else:  # post-pasto
            if self.valore > 250:
                return 'alta'
            elif self.valore > 220:
                return 'media'
            else:
                return 'bassa'

    class Meta:
        verbose_name = "Rilevazione Glicemia"
        verbose_name_plural = "Rilevazioni Glicemia"
        ordering = ['-data_ora']

# Modello per le Assunzioni di Farmaci
class AssunzioneFarmaco(models.Model):
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='assunzioni_farmaci')
    farmaco = models.ForeignKey(Farmaco, on_delete=models.CASCADE, related_name='assunzioni')
    terapia = models.ForeignKey(Terapia, on_delete=models.CASCADE, related_name='assunzioni')
    data_ora = models.DateTimeField(default=timezone.now)
    quantita = models.FloatField(validators=[MinValueValidator(0.1)])

    def __str__(self):
        return f"Assunzione {self.farmaco.nome} da {self.paziente} ({self.data_ora.strftime('%d/%m/%Y %H:%M')})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Verifica se la quantità è coerente con la terapia
        if self.quantita != self.terapia.quantita_per_assunzione:
            Alert.objects.create(
                paziente=self.paziente,
                medico=self.paziente.medico_riferimento,
                tipo='farmaco',
                descrizione=f"Quantità assunta ({self.quantita}) diversa da quella prescritta ({self.terapia.quantita_per_assunzione})",
                gravita='media'
            )

    class Meta:
        verbose_name = "Assunzione Farmaco"
        verbose_name_plural = "Assunzioni Farmaci"
        ordering = ['-data_ora']

# Modello per i Sintomi
class Sintomo(models.Model):
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='sintomi')
    descrizione = models.CharField(max_length=200)
    data_inizio = models.DateTimeField(default=timezone.now)
    data_fine = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sintomo {self.paziente}: {self.descrizione}"

    class Meta:
        verbose_name = "Sintomo"
        verbose_name_plural = "Sintomi"
        ordering = ['-data_inizio']

# Modello per le Patologie
class Patologia(models.Model):
    TIPI_PATOLOGIA = (
        ('pregressa', 'Patologia Pregressa'),
        ('concomitante', 'Patologia Concomitante'),
    )

    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='patologie')
    nome = models.CharField(max_length=100)
    descrizione = models.TextField(blank=True)
    tipo = models.CharField(max_length=12, choices=TIPI_PATOLOGIA)
    data_inizio = models.DateField()
    data_fine = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Patologia {self.paziente}: {self.nome} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Patologia"
        verbose_name_plural = "Patologie"

# Modello per gli Alert
class Alert(models.Model):
    TIPI_ALERT = (
        ('glicemia', 'Alert Glicemia'),
        ('farmaco', 'Alert Farmaco'),
    )

    GRAVITA = (
        ('bassa', 'Gravità bassa'),
        ('media', 'Gravità media'),
        ('alta', 'Gravità alta'),
    )

    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='alert')
    medico = models.ForeignKey(Diabetologo, on_delete=models.CASCADE, related_name='alert_ricevuti')
    data_ora = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=TIPI_ALERT)
    descrizione = models.TextField()
    gravita = models.CharField(max_length=5, choices=GRAVITA, default='media')
    risolto = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert {self.get_tipo_display()} per {self.paziente}"

    class Meta:
        verbose_name = "Alert"
        verbose_name_plural = "Alert"
        ordering = ['-data_ora']

# Modello per i Messaggi tra Pazienti e Medici
class Email(models.Model):
    paziente_mittente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='email_inviate')
    medico_destinatario = models.ForeignKey(Diabetologo, on_delete=models.CASCADE, related_name='email_ricevute')
    data_ora = models.DateTimeField(default=timezone.now)
    oggetto = models.CharField(max_length=200)
    testo = models.TextField()
    letto = models.BooleanField(default=False)

    def __str__(self):
        return f"Email da {self.paziente_mittente} a {self.medico_destinatario}: {self.oggetto}"

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Email"
        ordering = ['-data_ora']

# Modello per il Log delle Operazioni
class LogOperazione(models.Model):
    medico = models.ForeignKey(Diabetologo, on_delete=models.CASCADE, related_name='operazioni')
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='operazioni_ricevute')
    data_ora = models.DateTimeField(default=timezone.now)
    tipo_operazione = models.CharField(max_length=50)
    dettagli = models.TextField()

    def __str__(self):
        return f"Operazione {self.tipo_operazione} di {self.medico} su {self.paziente}"

    class Meta:
        verbose_name = "Log Operazione"
        verbose_name_plural = "Log Operazioni"
        ordering = ['-data_ora']
