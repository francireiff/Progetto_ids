
from django.shortcuts import render
from django.views.generic import FormView
from django.urls import reverse_lazy
from .forms import RegistrazionePazienteForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

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
    

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  
        else:
            messages.error(request, "Credenziali non valide.")
    return render(request, 'login.html')