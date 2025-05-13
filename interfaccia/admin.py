from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utente, Paziente, Diabetologo, Farmaco,
    Terapia, RilevazioneGlicemia, AssunzioneFarmaco,
    Sintomo, Patologia, Alert, Email, LogOperazione
)

@admin.register(Utente)
class UtenteAdmin(UserAdmin):
    list_display = ('username', 'tipo', 'is_staff')
    list_filter = ('tipo', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Informazioni aggiuntive', {'fields': ('tipo',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informazioni aggiuntive', {'fields': ('tipo',)}),
    )

@admin.register(Paziente)
class PazienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cognome', 'medico_riferimento')
    search_fields = ('nome', 'cognome')

@admin.register(Diabetologo)
class DiabetologoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cognome')
    search_fields = ('nome', 'cognome')

@admin.register(Farmaco)
class FarmacoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo')
    list_filter = ('tipo',)

@admin.register(Terapia)
class TerapiaAdmin(admin.ModelAdmin):
    list_display = ('paziente', 'medico', 'farmaco', 'data_inizio', 'data_fine', 'attiva')
    list_filter = ('attiva', 'farmaco__tipo')
    date_hierarchy = 'data_inizio'

@admin.register(RilevazioneGlicemia)
class RilevazioneGlicemiaAdmin(admin.ModelAdmin):
    list_display = ('paziente', 'data_ora', 'valore', 'momento', 'pasto')
    list_filter = ('momento', 'pasto')
    date_hierarchy = 'data_ora'

@admin.register(AssunzioneFarmaco)
class AssunzioneFarmacoAdmin(admin.ModelAdmin):
    list_display = ('paziente', 'farmaco', 'data_ora', 'quantita')
    list_filter = ('farmaco__tipo',)
    date_hierarchy = 'data_ora'

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('paziente', 'medico', 'tipo', 'gravita', 'data_ora', 'risolto')
    list_filter = ('tipo', 'gravita', 'risolto')
    date_hierarchy = 'data_ora'

# Registra i modelli rimanenti
admin.site.register(Sintomo)
admin.site.register(Patologia)
admin.site.register(Email)
admin.site.register(LogOperazione)