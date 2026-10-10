from django import forms

from reviews.models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["score", "text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "Комментарий (необязательно)"}),
        }
