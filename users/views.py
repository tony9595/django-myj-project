from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import UserRegisterForm, UserLoginForm

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # 자동 로그인 설정
            if not remember_me:
                request.session.set_expiry(0)
                
            return redirect('home')
        else:
            messages.error(request, '이메일/사용자명 또는 비밀번호가 올바르지 않습니다.')
            
    return render(request, 'users/login.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'계정이 생성되었습니다! 로그인할 수 있습니다.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})
