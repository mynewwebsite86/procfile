from django import forms
from .models import Product, Review

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'category', 'stock', 'image', 'delivery_info']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]

from django import forms
from .models import Profile

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["image"]