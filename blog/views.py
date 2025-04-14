from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Q
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, CategoryForm
from users.models import User
from django.http import JsonResponse
from django.utils.text import slugify
from unidecode import unidecode

class HomeView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'
    paginate_by = 16  # 4x4 그리드
    
    def get_queryset(self):
        queryset = Post.objects.filter(status='published').exclude(slug='')
        search_query = self.request.GET.get('q')
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(author__username__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

class BlogDetailView(ListView):
    model = Post
    template_name = 'blog/blog_detail.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username)
        return Post.objects.filter(
            author=user,
            status='published'
        ).exclude(slug='').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        context['blog_owner'] = get_object_or_404(User, username=username)
        context['categories'] = Category.objects.filter(
            posts__author=context['blog_owner']
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
        
        # 카테고리 처리
        categories = self.request.POST.getlist('categories')
        for category_id in categories:
            category = get_object_or_404(Category, id=category_id)
            form.instance.categories.add(category)
            
        return response
    
    def get_success_url(self):
        return reverse('post_detail', kwargs={'slug': self.object.slug})

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

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

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'blog/category_management.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # 사용자가 작성한 게시물에 연결된 카테고리만 가져옴
        return Category.objects.filter(
            posts__author=self.request.user
        ).annotate(
            post_count=Count('posts')
        ).distinct()

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'blog/category_form.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'blog/category_form.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        category = self.get_object()
        # 카테고리의 글 중에 자신이 작성한 글이 있는지 확인
        return category.posts.filter(author=self.request.user).exists() or (category.author == self.request.user)

class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('category_list')

    def test_func(self):
        category = self.get_object()
        # 카테고리의 글 중에 자신이 작성한 글이 있는지 확인
        return category.posts.filter(author=self.request.user).exists() or (category.author == self.request.user)

@login_required
def post_like(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'like_count': post.like_count()
    })

@login_required
def post_bookmark(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    if request.user in post.bookmarks.all():
        post.bookmarks.remove(request.user)
        bookmarked = False
    else:
        post.bookmarks.add(request.user)
        bookmarked = True
    
    return JsonResponse({
        'bookmarked': bookmarked,
        'bookmark_count': post.bookmark_count()
    })

@login_required
def bookmarked_posts(request):
    posts = Post.objects.filter(
        bookmarks=request.user,
        status='published'
    ).order_by('-created_at')
    
    return render(request, 'blog/bookmarked_posts.html', {'posts': posts})

class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        # 빈 slug를 가진 게시물들에 slug 생성
        posts_without_slug = Post.objects.filter(author=self.request.user, slug='')
        for post in posts_without_slug:
            # 한글 제목을 ASCII로 변환하여 slug 생성
            base_slug = slugify(unidecode(post.title))
            if not base_slug:
                # 만약 변환 후 빈 문자열이면 기본값 사용
                base_slug = 'post'
            
            unique_slug = base_slug
            counter = 1
            
            # 고유한 slug 생성
            while Post.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            
            post.slug = unique_slug
            post.save(update_fields=['slug'])
            
        return Post.objects.filter(author=self.request.user)

class CommentListView(LoginRequiredMixin, ListView):
    model = Comment
    template_name = 'blog/comment_list.html'
    context_object_name = 'comments'

    def get_queryset(self):
        return Comment.objects.filter(post__author=self.request.user)

class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ['content']
    template_name = 'blog/comment_form.html'
    success_url = reverse_lazy('comment_list')

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.post.author

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    success_url = reverse_lazy('comment_list')

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.post.author
