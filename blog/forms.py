from django import forms
from .models import Post, Comment, Category

class PostForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'status', 'categories']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug']
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': '입력하지 않으면 자동 생성됩니다'}),
        }
