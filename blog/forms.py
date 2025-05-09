from django import forms
from .models import Post, Comment, Category


class PostForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Post
        fields = ["title", "content", "categories", "status"]

    def save(self, commit=True):
        post = super().save(commit=False)
        if commit:
            post.save()
            self.save_m2m()  # 카테고리 저장

        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
        }


class CategoryForm(forms.ModelForm):
    slug = forms.SlugField(
        required=False, help_text="입력하지 않으면 이름으로부터 자동 생성됩니다"
    )

    class Meta:
        model = Category
        fields = ["name", "slug", "description"]
