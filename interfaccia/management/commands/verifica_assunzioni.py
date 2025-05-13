from celery import shared_task
from django.core.management.base import BaseCommand
from interfaccia.alert import verifica_assunzioni_farmaci

@shared_task
def task_verifica_assunzioni_farmaci():
    """Task Celery per verificare le assunzioni di farmaci"""
    verifica_assunzioni_farmaci()
    return "Verifica assunzioni farmaci completata"

class Command(BaseCommand):
    help = 'Verifica le assunzioni di farmaci e genera alert se necessario'

    def handle(self, *args, **options):
        verifica_assunzioni_farmaci()
        self.stdout.write(self.style.SUCCESS('Verifica assunzioni farmaci completata con successo'))