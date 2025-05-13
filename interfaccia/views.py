from django.views.generic import FormView
from django.urls import reverse_lazy
from .forms import RegistrazionePazienteForm

class RegistrazionePazienteView(FormView):
    template_name = 'registrazione_paziente.html'
    form_class = RegistrazionePazienteForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
