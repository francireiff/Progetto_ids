from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Utente, Paziente, Diabetologo, RilevazioneGlicemia,
    AssunzioneFarmaco, Sintomo, Terapia, Farmaco, Email
)

# Form per l'autenticazione degli utenti
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    class Meta:
        model = Utente
        fields = ['username', 'password']

# Form per la registrazione di una nuova rilevazione glicemica
class RilevazioneGlicemiaForm(forms.ModelForm):
    class Meta:
        model = RilevazioneGlicemia
        fields = ['valore', 'momento', 'pasto']
        
        widgets = {
            'valore': forms.NumberInput(attrs={
                'type': 'text',
                'placeholder': 'Valore glicemia',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
            }),
            'momento': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'placeholder': 'Data e ora della misurazione',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
            }),
            'pasto': forms.Select(attrs={
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
            }),
        }

        labels = {
            'valore': 'Valore glicemico (mg/dL)',
            'momento': 'Data e ora della misurazione',
            'pasto': 'Relazione con il pasto',
        }

    def clean_valore(self):
        valore = self.cleaned_data.get('valore')
        if valore < 10 or valore > 600:
            raise ValidationError("Il valore deve essere compreso tra 10 e 600 mg/dL")
        return valore

# Form per la registrazione di un'assunzione di farmaco
class AssunzioneFarmacoForm(forms.ModelForm):
    terapia = forms.ModelChoiceField(
        queryset=Terapia.objects.none(),
        widget=forms.Select(attrs={
            'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
        })
    )

    class Meta:
        model = AssunzioneFarmaco
        fields = ['terapia', 'quantita']
        widgets = {
            'quantita': forms.NumberInput(attrs={
                'type': 'text',  # per renderlo coerente con login.html
                'placeholder': 'Quantità del farmaco',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
            }),
        }

        labels = {
            'terapia': 'Seleziona Terapia',
            'quantita': 'Quantità',
        }

    def __init__(self, *args, **kwargs):
        paziente = kwargs.pop('paziente', None)
        super().__init__(*args, **kwargs)
        if paziente:
            # Filtra solo le terapie attive del paziente
            self.fields['terapia'].queryset = Terapia.objects.filter(
                paziente=paziente,
                attiva=True,
                data_inizio__lte=timezone.now().date(),
                data_fine__gte=timezone.now().date()
            )

    def clean(self):
        cleaned_data = super().clean()
        terapia = cleaned_data.get('terapia')
        quantita = cleaned_data.get('quantita')

        if terapia and quantita:
            # Verifica che la quantità sia positiva
            if quantita <= 0:
                self.add_error('quantita', "La quantità deve essere maggiore di zero")

            # Avvisa se la quantità è diversa da quella prescritta
            if quantita != terapia.quantita_per_assunzione:
                self.add_error('quantita', f"Attenzione: la quantità prescritta è {terapia.quantita_per_assunzione}")

        return cleaned_data

class SintomoForm(forms.ModelForm):
    class Meta:
        model = Sintomo
        fields = ['descrizione', 'data_inizio', 'data_fine']
        widgets = {
            'descrizione': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
                'placeholder': 'Descrivi il sintomo',
            }),
            'data_inizio': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
                'type': 'datetime-local',
            }),
            'data_fine': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
                'type': 'datetime-local',
                'required': False,
            }),
        }

        labels = {
            'descrizione': 'Descrizione del sintomo',
            'data_inizio': 'Data di inizio',
            'data_fine': 'Data di fine (opzionale)',
        }


    def clean(self):
        cleaned_data = super().clean()
        data_inizio = cleaned_data.get('data_inizio')
        data_fine = cleaned_data.get('data_fine')

        if data_inizio and data_fine and data_inizio > data_fine:
            self.add_error('data_fine', "La data di fine non può essere precedente alla data di inizio")

        return cleaned_data

# Form per la prescrizione di una terapia
class TerapiaForm(forms.ModelForm):
    class Meta:
        model = Terapia
        fields = ['farmaco', 'data_inizio', 'data_fine', 'numero_assunzioni_giornaliere',
                  'quantita_per_assunzione', 'indicazioni']
        widgets = {
            'farmaco': forms.Select(attrs={'class': 'form-control'}),
            'data_inizio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fine': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_assunzioni_giornaliere': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'quantita_per_assunzione': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'indicazioni': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inizio = cleaned_data.get('data_inizio')
        data_fine = cleaned_data.get('data_fine')

        if data_inizio and data_fine:
            if data_inizio > data_fine:
                self.add_error('data_fine', "La data di fine non può essere precedente alla data di inizio")

            if data_inizio < timezone.now().date():
                self.add_error('data_inizio', "La data di inizio non può essere nel passato")

        return cleaned_data

class EmailForm(forms.ModelForm):
    class Meta:
        model = Email
        fields = ['oggetto', 'testo']
        widgets = {
            'oggetto': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
                'placeholder': 'Oggetto del messaggio',
            }),
            'testo': forms.Textarea(attrs={
                'class': 'form-control',
                'style': 'width:90%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;',
                'rows': 5,
                'placeholder': 'Scrivi il tuo messaggio',
            }),
        }

        labels = {
            'oggetto': 'Oggetto',
            'testo': 'Messaggio',
        }

# Form per l'aggiornamento delle informazioni del paziente
class PazienteUpdateForm(forms.ModelForm):
    class Meta:
        model = Paziente
        fields = ['fumatore', 'ex_fumatore', 'problemi_alcol', 'problemi_stupefacenti',
                  'obesita', 'pregresse_patologie', 'comorbidita']
        widgets = {
            'fumatore': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ex_fumatore': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'problemi_alcol': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'problemi_stupefacenti': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'obesita': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pregresse_patologie': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'comorbidita': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
class RegistrazionePazienteForm(UserCreationForm):
    nome = forms.CharField(max_length=100)
    cognome = forms.CharField(max_length=100)
    data_nascita = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Utente
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        utente = super().save(commit=False)
        utente.tipo = 'paziente'
        if commit:
            utente.save()
            Paziente.objects.create(
                utente=utente,
                nome=self.cleaned_data['nome'],
                cognome=self.cleaned_data['cognome'],
                data_nascita=self.cleaned_data['data_nascita']
            )
        return utente