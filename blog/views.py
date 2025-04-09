from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, CategoryForm
from users.models import User

class HomeView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'
    paginate_by = 16  # 4x4 그리드
    
    def get_queryset(self):
        return Post.objects.filter(status='published').order_by('-created_at')

class BlogDetailView(ListView):
    model = Post
    template_name = 'blog/blog_detail.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        self.blog_owner = get_object_or_404(User, username=self.kwargs['username'])
        return Post.objects.filter(
            author=self.blog_owner, 
            status='published'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_owner'] = self.blog_owner
        context['categories'] = Category.objects.filter(
            posts__author=self.blog_owner
        ).distinct()
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_object(self):
        post = super().get_object()
        # 조회수 증가
        post.increment_view_count()
        return post
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.filter(parent=None).order_by('-created_at')
        context['comment_form'] = CommentForm()
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        form.instance.categories.set(form.cleaned_data['categories'])
        return response

class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    
    def get_queryset(self):
        # 자신의 글만 수정 가능
        return Post.objects.filter(author=self.request.user)

class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('home')
    
    def get_queryset(self):
        # 자신의 글만 삭제 가능
        return Post.objects.filter(author=self.request.user)

@login_required
def post_comment(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            
            # 대댓글인 경우
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(Comment, id=parent_id)
            
            comment.save()
            return redirect('post_detail', slug=post.slug)
    
    return redirect('post_detail', slug=post.slug)

# 카테고리 관리 뷰
@login_required
def category_management(request):
    categories = Category.objects.filter(
        posts__author=request.user
    ).annotate(
        post_count=Count('posts')
    ).distinct()
    
    return render(request, 'blog/category_management.html', {'categories': categories})

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'blog/category_form.html'
    success_url = reverse_lazy('category_management')

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'blog/category_form.html'
    success_url = reverse_lazy('category_management')

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('category_management')
    template_name = 'blog/category_confirm_delete.html'
