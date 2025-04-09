from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import UserRegisterForm, UserLoginForm, CustomUserCreationForm, CustomUserChangeForm
from .models import User
from blog.models import Post
from django.contrib.auth.decorators import login_required

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
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '회원가입이 완료되었습니다.')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '프로필이 업데이트되었습니다.')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    # 사용자의 게시글 통계
    posts = Post.objects.filter(author=request.user)
    published_posts = posts.filter(status='published')
    draft_posts = posts.filter(status='draft')
    
    context = {
        'form': form,
        'total_posts': posts.count(),
        'published_posts': published_posts.count(),
        'draft_posts': draft_posts.count(),
        'recent_posts': published_posts.order_by('-created_at')[:5]
    }
    
    return render(request, 'users/profile.html', context)

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user, status='published').order_by('-created_at')
    
    context = {
        'profile_user': user,
        'posts': posts,
        'total_posts': posts.count(),
    }
    
    return render(request, 'users/user_profile.html', context)
