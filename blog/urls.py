from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('blog/<str:username>/', views.BlogDetailView.as_view(), name='blog_detail'),
    path('post/new/', views.PostCreateView.as_view(), name='post_create'),
    re_path(r'^post/(?P<slug>[\w-]+)/$', views.PostDetailView.as_view(), name='post_detail'),
    re_path(r'^post/(?P<slug>[\w-]+)/edit/$', views.PostUpdateView.as_view(), name='post_update'),
    re_path(r'^post/(?P<slug>[\w-]+)/delete/$', views.PostDeleteView.as_view(), name='post_delete'),
    re_path(r'^post/(?P<slug>[\w-]+)/comment/$', views.post_comment, name='post_comment'),
    re_path(r'^post/(?P<slug>[\w-]+)/like/$', views.post_like, name='post_like'),
    re_path(r'^post/(?P<slug>[\w-]+)/bookmark/$', views.post_bookmark, name='post_bookmark'),
    path('bookmarks/', views.bookmarked_posts, name='bookmarked_posts'),
    path('manage/categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('manage/categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('manage/categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('manage/categories/', views.CategoryListView.as_view(), name='category_list'),
    path('manage/posts/', views.PostListView.as_view(), name='post_list'),
    path('manage/comments/', views.CommentListView.as_view(), name='comment_list'),
    path('manage/comments/<int:pk>/edit/', views.CommentUpdateView.as_view(), name='comment_update'),
    path('manage/comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
]
