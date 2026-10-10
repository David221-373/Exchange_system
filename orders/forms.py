from decimal import Decimal

from django import forms

from core.models import City
from orders.models import ExchangeOrder
from rates.models import ExchangeRate


class ExchangeOrderForm(forms.ModelForm):
    class Meta:
        model = ExchangeOrder
        fields = ["rate", "crypto_amount", "contact_email", "contact_phone", "city", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Комментарий к заявке"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rate"].queryset = ExchangeRate.objects.filter(is_active=True).select_related(
            "base_currency", "quote_currency"
        )

    def clean(self):
        data = super().clean()
        email = (data.get("contact_email") or "").strip()
        phone = (data.get("contact_phone") or "").strip()
        if not email and not phone:
            raise forms.ValidationError("Укажите e-mail или телефон для связи.")
        return data


class HomeExchangeForm(forms.Form):
    city = forms.ModelChoiceField(queryset=City.objects.none(), label="Город")
    send_currency = forms.ChoiceField(choices=(), label="Вы отправляете")
    receive_currency = forms.ChoiceField(choices=(), label="Вы получаете")
    send_amount = forms.DecimalField(max_digits=18, decimal_places=8, required=False, min_value=Decimal("0.00000001"))
    receive_amount = forms.DecimalField(max_digits=18, decimal_places=8, required=False, min_value=Decimal("0.00000001"))
    contact_phone = forms.CharField(max_length=30, label="Телефон")
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Комментарий"}))
    rate_id = forms.IntegerField(widget=forms.HiddenInput())
    entry_mode = forms.ChoiceField(choices=[("send", "send"), ("receive", "receive")], widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["city"].queryset = City.objects.filter(is_active=True).order_by("sort_order", "name")
        rates = ExchangeRate.objects.filter(is_active=True).select_related("base_currency", "quote_currency")
        send_choices = sorted({(r.base_currency.code, r.base_currency.code) for r in rates})
        receive_choices = sorted({(r.quote_currency.code, r.quote_currency.code) for r in rates})
        self.fields["send_currency"].choices = send_choices
        self.fields["receive_currency"].choices = receive_choices
        self.fields["entry_mode"].initial = "send"

    def clean(self):
        data = super().clean()
        rate_id = data.get("rate_id")
        send_code = data.get("send_currency")
        receive_code = data.get("receive_currency")
        send_amount = data.get("send_amount")
        receive_amount = data.get("receive_amount")
        entry_mode = data.get("entry_mode") or "send"

        if not rate_id:
            raise forms.ValidationError("Не выбрано направление обмена.")

        try:
            rate = ExchangeRate.objects.select_related("base_currency", "quote_currency").get(pk=rate_id, is_active=True)
        except ExchangeRate.DoesNotExist as exc:
            raise forms.ValidationError("Направление недоступно.") from exc

        if rate.base_currency.code != send_code or rate.quote_currency.code != receive_code:
            raise forms.ValidationError("Направление и выбранные валюты не совпадают.")

        if not send_amount and not receive_amount:
            raise forms.ValidationError("Укажите сумму отправки или сумму получения.")

        if entry_mode == "receive":
            if not receive_amount:
                raise forms.ValidationError("Укажите сумму получения.")
            send_amount = (Decimal(receive_amount) / rate.sell_rate) if rate.sell_rate > 0 else None
        else:
            if not send_amount:
                raise forms.ValidationError("Укажите сумму отправки.")
            receive_amount = Decimal(send_amount) * rate.sell_rate

        if not send_amount or send_amount <= 0 or not receive_amount or receive_amount <= 0:
            raise forms.ValidationError("Некорректная сумма обмена.")

        data["rate"] = rate
        data["computed_send_amount"] = send_amount
        data["computed_receive_amount"] = receive_amount
        return data
