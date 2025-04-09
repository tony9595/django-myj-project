from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('blog/<str:username>/', views.BlogDetailView.as_view(), name='blog_detail'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/new/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_update'),
    path('post/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('post/<slug:slug>/comment/', views.post_comment, name='post_comment'),
    path('manage/categories/', views.category_management, name='category_management'),
    path('manage/categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('manage/categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('manage/categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]
