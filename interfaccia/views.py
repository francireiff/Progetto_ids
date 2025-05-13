
from django.shortcuts import render
from django.views.generic import FormView
from django.urls import reverse_lazy
from .forms import RegistrazionePazienteForm

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