from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Q
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, CategoryForm
from users.models import User
from django.http import JsonResponse
from django.utils.text import slugify
from unidecode import unidecode
import random
from datetime import datetime


class HomeView(ListView):
    model = Post
    template_name = "blog/index.html"
    context_object_name = "posts"
    paginate_by = 15  # 한 페이지당 15개 게시글

    def get_queryset(self):
        queryset = Post.objects.filter(status="published").exclude(slug="")
        search_query = self.request.GET.get("q")

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(author__username__icontains=search_query)
                | Q(categories__name__icontains=search_query)
            ).distinct()

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class BlogDetailView(ListView):
    model = Post
    template_name = "blog/blog_detail.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username)
        queryset = (
            Post.objects.filter(author=user, status="published")
            .exclude(slug="")
            .order_by("-created_at")
        )

        # 카테고리 필터링
        category_slug = self.request.GET.get("category")
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(categories=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get("username")
        context["blog_owner"] = get_object_or_404(User, username=username)
        context["categories"] = Category.objects.filter(
            posts__author=context["blog_owner"]
        ).distinct()
        context["selected_category"] = self.request.GET.get("category")
        
        


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_object(self):
        post = super().get_object()
        # 조회수 증가
        post.increment_view_count()
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.filter(parent=None).order_by(
            "-created_at"
        )
        context["comment_form"] = CommentForm()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # 카테고리 처리
        categories = self.request.POST.getlist("categories")
        for category_id in categories:
            category = get_object_or_404(Category, id=category_id)
            form.instance.categories.add(category)

        return response

    def get_success_url(self):
        return reverse("post_detail", kwargs={"slug": self.object.slug})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    success_url = reverse_lazy("post_list")

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("post_list")

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


@login_required
def post_comment(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user

            # 대댓글인 경우
            parent_id = request.POST.get("parent_id")
            if parent_id:
                comment.parent = get_object_or_404(Comment, id=parent_id)

            comment.save()
            return redirect("post_detail", slug=post.slug)

    return redirect("post_detail", slug=post.slug)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "blog/category_management.html"
    context_object_name = "categories"

    def get_queryset(self):
        # 사용자가 작성한 게시물에 연결된 카테고리만 가져옴
        return (
            Category.objects.filter(posts__author=self.request.user)
            .annotate(post_count=Count("posts"))
            .distinct()
        )


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "blog/category_form.html"
    success_url = reverse_lazy("category_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "blog/category_form.html"
    success_url = reverse_lazy("category_list")

    def test_func(self):
        category = self.get_object()
        # 카테고리의 글 중에 자신이 작성한 글이 있는지 확인
        return category.posts.filter(author=self.request.user).exists() or (
            category.author == self.request.user
        )


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("category_list")

    def test_func(self):
        category = self.get_object()
        # 카테고리의 글 중에 자신이 작성한 글이 있는지 확인
        return category.posts.filter(author=self.request.user).exists() or (
            category.author == self.request.user
        )


@login_required
def post_like(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({"liked": liked, "like_count": post.like_count()})


@login_required
def post_bookmark(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.user in post.bookmarks.all():
        post.bookmarks.remove(request.user)
        bookmarked = False
    else:
        post.bookmarks.add(request.user)
        bookmarked = True

    return JsonResponse(
        {"bookmarked": bookmarked, "bookmark_count": post.bookmark_count()}
    )


@login_required
def bookmarked_posts(request):
    posts = Post.objects.filter(bookmarks=request.user, status="published").order_by(
        "-created_at"
    )

    # 카테고리 필터링
    category_slug = request.GET.get("category")
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        posts = posts.filter(categories=category)

    categories = Category.objects.all()
    selected_category = request.GET.get("category")

    return render(
        request,
        "blog/bookmarked_posts.html",
        {
            "posts": posts,
            "categories": categories,
            "selected_category": selected_category,
        },
    )


class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        # 로그인한 사용자가 작성한 모든 게시글 (임시저장 포함)
        queryset = Post.objects.filter(author=self.request.user).order_by("-created_at")

        # 카테고리 필터링
        category_slug = self.request.GET.get("category")
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(categories=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 사용자가 작성한 게시물에 연결된 카테고리만 표시
        context["categories"] = Category.objects.filter(
            posts__author=self.request.user
        ).distinct()
        context["selected_category"] = self.request.GET.get("category")
        return context


class CommentListView(LoginRequiredMixin, ListView):
    model = Comment
    template_name = "blog/comment_list.html"
    context_object_name = "comments"

    def get_queryset(self):
        return Comment.objects.filter(post__author=self.request.user)


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ["content"]
    template_name = "blog/comment_form.html"
    success_url = reverse_lazy("comment_list")

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.post.author


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    success_url = reverse_lazy("comment_list")

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.post.author


def rock_paper_scissors_game(request):
    """
    가위바위보 게임 뷰 함수
    """
    context = {
        "title": "가위바위보 게임",
        "result": None,
        "user_choice": None,
        "computer_choice": None,
    }

    if request.method == "POST":
        user_choice = request.POST.get("choice")
        choices = ["rock", "paper", "scissors"]
        computer_choice = random.choice(choices)

        context["user_choice"] = user_choice
        context["computer_choice"] = computer_choice

        # 승패 결정
        if user_choice == computer_choice:
            context["result"] = "draw"
        elif (
            (user_choice == "rock" and computer_choice == "scissors")
            or (user_choice == "paper" and computer_choice == "rock")
            or (user_choice == "scissors" and computer_choice == "paper")
        ):
            context["result"] = "win"
        else:
            context["result"] = "lose"

    return render(request, "blog/game.html", context)


def lotto_generator(request):
    """
    로또 번호 추첨 뷰 함수
    """
    context = {"title": "로또 번호 추첨", "numbers": None, "bonus": None, "history": []}

    if request.method == "POST":
        # 1부터 45까지의 숫자 중 7개를 무작위로 선택 (6개 번호 + 1개 보너스)
        numbers = random.sample(range(1, 46), 7)

        # 앞의 6개는 정렬된 로또 번호, 마지막 1개는 보너스 번호
        context["numbers"] = sorted(numbers[:6])
        context["bonus"] = numbers[6]

        # 세션에서 기존 이력 가져오기
        history = request.session.get("lotto_history", [])

        # 새로운 번호를 이력에 추가 (최대 5개까지만 저장)
        history.insert(
            0,
            {
                "numbers": context["numbers"],
                "bonus": context["bonus"],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        if len(history) > 5:
            history = history[:5]

        # 이력 업데이트
        request.session["lotto_history"] = history
        context["history"] = history
    else:
        # GET 요청 시 이력 표시
        context["history"] = request.session.get("lotto_history", [])

    return render(request, "blog/lotto.html", context)
