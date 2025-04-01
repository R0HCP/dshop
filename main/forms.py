from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Service, Order

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=15, required=False)
    first_name = forms.CharField(max_length=250, required=False)
    last_name = forms.CharField(max_length=250, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'phone', 'first_name', 'last_name')

class CustomAuthenticationForm(AuthenticationForm):
    pass # Используем стандартную форму Django

class AddServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['images', 'title', 'description', 'price', 'quantity', 'execution_time_days'] 

class OrderServiceForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)


class EditServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['images', 'title', 'description', 'price', 'isAvaliable', 'quantity', 'execution_time_days'] # <--- Добавлено execution_time_days

class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'phone', 'first_name', 'last_name', 'pfp'] 