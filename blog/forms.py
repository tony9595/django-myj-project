from django import forms
from .models import Post, Comment, Category, Tag

class PostForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    tags = forms.CharField(
        required=False,
        help_text='쉼표로 구분하여 입력하세요'
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'categories', 'tags', 'status']
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if not tags:
            return []
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        return tag_list
    
    def save(self, commit=True):
        post = super().save(commit=False)
        if commit:
            post.save()
            self.save_m2m()  # 카테고리 저장
            
            # 태그 처리
            tag_list = self.cleaned_data.get('tags', [])
            post.tags.clear()
            for tag_name in tag_list:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                post.tags.add(tag)
        
        return post

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

class CategoryForm(forms.ModelForm):
    slug = forms.SlugField(required=False, help_text='입력하지 않으면 이름으로부터 자동 생성됩니다')
    
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']
