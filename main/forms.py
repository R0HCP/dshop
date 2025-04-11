from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Service, Order, ConsultationSlot


from django import forms
from .models import ConsultationSlot
import datetime

class ConsultationSlotForm(forms.Form): 
    days_of_week = forms.MultipleChoiceField(
        label="Дни недели",
        choices=[
            ('0', 'Понедельник'),
            ('1', 'Вторник'),
            ('2', 'Среда'),
            ('3', 'Четверг'),
            ('4', 'Пятница'),
            ('5', 'Суббота'),
            ('6', 'Воскресенье'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    start_time = forms.TimeField(
        label="Время начала приема",
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True,
    )
    end_time = forms.TimeField(
        label="Время окончания приема",
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True,
    )
    duration_minutes = forms.IntegerField(
        label="Длительность консультации (в минутах)",
        min_value=15,
        max_value=120,
        initial=30,
        required=True,
    )
    break_start_time = forms.TimeField(
        label="Время начала перерыва (необязательно)",
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=False,
    )
    break_end_time = forms.TimeField(
        label="Время окончания перерыва (необязательно)",
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=False,
    )
    start_date = forms.DateField(
        label="Дата начала действия расписания",
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date.today,
        required=True,
    )
    end_date = forms.DateField(
        label="Дата окончания действия расписания",
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False, # Продавец будет работать до конца своих дней
    )

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
        fields = ['category', 'images', 'title', 'description', 'price', 'quantity', 'execution_time_days'] 

class EditServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'images', 'title', 'description', 'price', 'isAvaliable', 'quantity', 'execution_time_days'] # <--- Добавлено execution_time_days

class OrderServiceForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'phone', 'first_name', 'last_name', 'pfp'] 