from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Service, Order, ConsultationSlot, Category 
import datetime


class AdminOrderFilterForm(forms.Form):
    status = forms.ChoiceField(choices=[('', 'Все статусы')] + Order.STATUS_CHOICES, required=False, label="Статус заказа")
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, label="Категория услуги", empty_label="Все категории")
    date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Дата заказа от")
    date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Дата заказа до")
    search_query = forms.CharField(required=False, label="Поиск (ID заказа, имя клиента, название услуги)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'class': 'form-select form-select-sm'})
        self.fields['category'].widget.attrs.update({'class': 'form-select form-select-sm'})
        self.fields['date_from'].widget.attrs.update({'class': 'form-control form-control-sm'})
        self.fields['date_to'].widget.attrs.update({'class': 'form-control form-control-sm'})
        self.fields['search_query'].widget.attrs.update({'class': 'form-control form-control-sm', 'placeholder': 'ID, клиент, услуга...'})


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        label="Начальная дата",
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
    )
    end_date = forms.DateField(
        label="Конечная дата",
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
    )


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
        fields = ['category', 'images', 'title', 'description', 'price', 'quantity', 'execution_time_days', 'agreement_document']

class EditServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'images', 'title', 'description', 'price', 'isAvaliable', 'quantity', 'execution_time_days', 'agreement_document']# <--- Добавлено execution_time_days

class OrderServiceForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)


class AdminOrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'phone', 'first_name', 'last_name', 'pfp', 'office_latitude', 'office_longitude'] 