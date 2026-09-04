from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect, render

def home(request):    
    return render(request,'home.html')

def resenas(request):
    return render(request, 'admin/reseñas.html', {'titulo': 'Reseñas'})

# modulo de registro de usuarios

def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validar contraseña
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'admin/registro.html')

        # Validar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está registrado.')
            return render(request, 'admin/registro.html')

        # Validar si el correo ya existe
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'admin/registro.html')

        # Crear y guardar el usuario en db.sqlite3
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        messages.success(request, 'Cuenta creada exitosamente.')
        return redirect('registro')

    return render(request, 'admin/registro.html', {'titulo': 'Registro'})