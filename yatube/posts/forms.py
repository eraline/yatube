from django import forms
from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {'group': forms.Select()}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
