from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from . import models


class CustomUserForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(widget=forms.NumberInput(attrs={'class': 'form-control phone-num'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'password1', 'password2']


class IShareBundleForm(forms.Form):
    phone_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control phone', 'placeholder': '0270000000'}))
    offers = forms.ModelChoiceField(queryset=models.IshareBundlePrice.objects.all(), to_field_name='price', empty_label=None,
                               widget=forms.Select(attrs={'class': 'form-control airtime-input'}))
            

class MTNForm(forms.Form):
    phone_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control mtn-phone', 'placeholder': '0200000000'}))
    offers = forms.ModelChoiceField(queryset=models.MTNBundlePrice.objects.all().order_by('price'), to_field_name='price', empty_label=None,
                               widget=forms.Select(attrs={'class': 'form-control mtn-offer'}))