from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AddServiceForm, OrderServiceForm, EditServiceForm 
from .models import Service, Order, Holiday 
from .forms import UserProfileEditForm
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse 
import datetime


@login_required # Оформление заказа только для зарегистрированных пользователей
def checkout_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    if not cart:
        return HttpResponse("Ваша корзина пуста.") # Или перенаправить на страницу корзины

    for service_id, quantity in cart.items():
        service = get_object_or_404(Service, pk=service_id)
        item_total_price = service.price * quantity
        cart_items.append({
            'service': service,
            'quantity': quantity,
            'total_price': item_total_price,
        })
        total_price += item_total_price

    if request.method == 'POST': # Обработка POST запроса (например, после подтверждения заказа)
        # Здесь можно добавить логику создания заказа в базе данных
        # и обработки оплаты (если необходимо)

        # Создание заказа (пример - нужно адаптировать под вашу логику)
        for item in cart_items:
            service = item['service']
            quantity = item['quantity']
            order = Order.objects.create(
                user=request.user,
                service=service,
                quantity=quantity,
                total_price=item['total_price']
            )
            service.quantity -= quantity
            if service.quantity == 0:
                service.isAvaliable = False
            service.save()

        # Очистка корзины после оформления заказа
        del request.session['cart']

        return render(request, 'main/checkout_success.html', {'total_price': total_price}) # Страница успешного оформления заказа

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'main/checkout.html', context) # Страница оформления заказа (форма подтверждения)

@login_required
def order_service_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        form = OrderServiceForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if service.quantity >= quantity:
                total_price = service.price * quantity
                order = Order.objects.create(user=request.user, service=service, quantity=quantity, total_price=total_price)
                service.quantity -= quantity
                if service.quantity == 0:
                    service.isAvaliable = False
                service.save()

                # Расчет даты выполнения
                holidays = Holiday.objects.all()
                start_date = order.created_at
                estimated_completion_date = calculate_estimated_completion_date(start_date, service.execution_time_days, holidays)

                print(f"Рассчитанная дата выполнения перед сохранением: {estimated_completion_date}") # Отладка
                print(f"Тип данных даты выполнения: {type(estimated_completion_date)}") # Отладка

                order.estimated_completion_date = estimated_completion_date

                try: # Оборачиваем сохранение в try-except для отладки ошибок
                    order.save()
                    print("Заказ успешно сохранен с датой выполнения.") # Отладка
                except Exception as e:
                    print(f"Ошибка при сохранении заказа: {e}") # Отладка

                return render(request, 'main/order_success.html', {'order_id': order.id, 'seller': service.user, 'completion_date': estimated_completion_date})
            else:
                return HttpResponse("Извините, недостаточно товара на складе.")
    else:
        form = OrderServiceForm()
    return render(request, 'main/order_form.html', {'form': form, 'service': service})



# @login_required
# def order_service_view(request, service_id):
#     service = get_object_or_404(Service, pk=service_id)
#     if request.method == 'POST':
#         form = OrderServiceForm(request.POST)
#         if form.is_valid():
#             quantity = form.cleaned_data['quantity']
#             if service.quantity >= quantity:
#                 total_price = service.price * quantity
#                 order = Order.objects.create(user=request.user, service=service, quantity=quantity, total_price=total_price)
#                 service.quantity -= quantity
#                 if service.quantity == 0:
#                     service.isAvaliable = False
#                 service.save()

#                 # Расчет даты выполнения
#                 holidays = Holiday.objects.all()
#                 start_date = order.created_at
#                 estimated_completion_date = calculate_estimated_completion_date(start_date, service.execution_time_days, holidays)
#                 order.estimated_completion_date = estimated_completion_date
#                 order.save()

#                 return render(request, 'main/order_success.html', {'order_id': order.id, 'seller': service.user, 'completion_date': estimated_completion_date}) # Передаем дату в контекст
#             else:
#                 return HttpResponse("Извините, недостаточно товара на складе.")
#     else:
#         form = OrderServiceForm()
#     return render(request, 'main/order_form.html', {'form': form, 'service': service})

def calculate_estimated_completion_date(start_date, execution_time_days, holidays):
    current_date = start_date
    working_days_count = 0

    while working_days_count < execution_time_days:
        current_date += datetime.timedelta(days=1)
        is_weekend = (current_date.weekday() >= 5) 
        is_holiday = current_date.date() in [holiday.date for holiday in holidays]

        if not is_weekend and not is_holiday:
            working_days_count += 1

    return current_date.date()



def index(request):
    services = Service.objects.filter(isAvaliable=True)
    max_price = Service.objects.filter(isAvaliable=True).order_by('-price').first()
    if max_price:
        max_price = int(max_price.price) # Получаем максимальную цену и преобразуем в int для range max
    else:
        max_price = 1000 # Дефолтное значение, если нет услуг

    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        services = services.filter(title__icontains=search_query)

    # Сортировка
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        services = services.order_by('price')
    elif sort_by == 'price_desc':
        services = services.order_by('-price')
    elif sort_by == 'title_asc':
        services = services.order_by('title')
    elif sort_by == 'title_desc':
        services = services.order_by('-title')

    # Фильтрация по цене
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')

    if price_from:
        services = services.filter(price__gte=price_from) # Фильтр "цена от" (больше или равно)
    if price_to:
        services = services.filter(price__lte=price_to) # Фильтр "цена до" (меньше или равно)

    context = {
        'services': services,
        'max_price': max_price, # Передаем max_price в шаблон
        'price_from_value': price_from or 0, # Передаем текущие значения или 0 по умолчанию
        'price_to_value': price_to or max_price, # Передаем текущие значения или max_price по умолчанию
    }
    return render(request, 'main/index.html', context)

def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    order_form = OrderServiceForm() 
    context = {
        'service': service,
        'order_form': order_form,
    }
    return render(request, 'main/service_detail.html', context)


@staff_member_required 
def delete_service_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    service.delete()
    return redirect('index') 

@staff_member_required 
def toggle_trusted_from_service_view(request, user_id): 
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=user_id)
            user.isTrusted = not user.isTrusted
            user.save()
            return redirect('service_detail', service_id=request.POST.get('service_id')) 
        except User.DoesNotExist:
            return HttpResponseForbidden("Пользователь не найден.")
    else:
        return HttpResponseForbidden("Недопустимый метод запроса.")


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Автоматический вход после регистрации
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index') 
    else:
        form = CustomAuthenticationForm()
    return render(request, 'main/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index') 

# @login_required 
# def order_service_view(request, service_id):
#     service = get_object_or_404(Service, pk=service_id)
#     if request.method == 'POST':
#         form = OrderServiceForm(request.POST)
#         if form.is_valid():
#             quantity = form.cleaned_data['quantity']
#             if service.quantity >= quantity: 
#                 total_price = service.price * quantity
#                 order = Order.objects.create(user=request.user, service=service, quantity=quantity, total_price=total_price)
#                 service.quantity -= quantity 
#                 if service.quantity == 0:
#                     service.isAvaliable = False 
#                 service.save()
#                 return render(request, 'main/order_success.html', {'order_id': order.id}) 
#             else:
#                 return HttpResponse("Извините, недостаточно товара на складе.") 
#     else:
#         form = OrderServiceForm()
#     return render(request, 'main/order_form.html', {'form': form, 'service': service}) 

def is_trusted_user(user): 
    return user.is_authenticated and user.isTrusted

@user_passes_test(is_trusted_user)
def add_service_view(request):
    if request.method == 'POST':
        form = AddServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False) 
            service.user = request.user # Назначаем текущего пользователя владельцем
            service.save() # Сохраняем уже с владельцем
            return redirect('service_detail', service_id=service.id) 
    else:
        form = AddServiceForm()
    return render(request, 'main/add_service.html', {'form': form})


@login_required
def edit_service_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if service.user != request.user: # Проверка, является ли текущий пользователь владельцем услуги
        return HttpResponseForbidden("Вы не можете редактировать эту услугу.")

    if request.method == 'POST':
        form = EditServiceForm(request.POST, request.FILES, instance=service) 
        if form.is_valid():
            form.save()
            return redirect('service_detail', service_id=service.id) 
    else:
        form = EditServiceForm(instance=service) 

    context = {
        'form': form,
        'service': service,
    }
    return render(request, 'main/edit_service.html', context)



# @login_required
# def order_service_view(request, service_id):
#     service = get_object_or_404(Service, pk=service_id)
#     if request.method == 'POST':
#         form = OrderServiceForm(request.POST)
#         if form.is_valid():
#             quantity = form.cleaned_data['quantity']
#             if service.quantity >= quantity:
#                 total_price = service.price * quantity
#                 order = Order.objects.create(user=request.user, service=service, quantity=quantity, total_price=total_price)
#                 service.quantity -= quantity
#                 if service.quantity == 0:
#                     service.isAvaliable = False
#                 service.save()
#                 return render(request, 'main/order_success.html', {'order_id': order.id, 'seller': service.user}) # Передаем продавца в контекст
#             else:
#                 return HttpResponse("Извините, недостаточно товара на складе.")
#     else:
#         form = OrderServiceForm()
#     return render(request, 'main/order_form.html', {'form': form, 'service': service})




@login_required #  только для авторизованных пользователей
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile') #  на страницу профиля после сохранения
    else:
        form = UserProfileEditForm(instance=request.user) # Инициализация формы с данными текущего пользователя

    context = {
        'form': form,
    }
    return render(request, 'main/profile.html', context)

@login_required
def toggle_trusted_view(request):
    if request.user.is_staff or request.user.is_superuser: 
        user_id = request.POST.get('user_id') # Получаем ID пользователя из запроса
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                user.isTrusted = not user.isTrusted 
                user.save()
                return redirect('admin:main_user_change', object_id=user_id) # Перенаправляем обратно в админку редактирования пользователя
            except User.DoesNotExist:
                return HttpResponseForbidden("Пользователь не найден.")
        else:
            return HttpResponseForbidden("Не указан ID пользователя.")
    else:
        return HttpResponseForbidden("У вас нет прав для выполнения этого действия.") 
    

def view_cart(request):
    cart = request.session.get('cart', {}) # Получаем корзину из сессии или пустой словарь
    cart_items = []
    total_price = 0

    for service_id, quantity in cart.items():
        service = get_object_or_404(Service, pk=service_id)
        item_total_price = service.price * quantity
        cart_items.append({
            'service': service,
            'quantity': quantity,
            'total_price': item_total_price,
        })
        total_price += item_total_price

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'main/cart.html', context)

def add_to_cart(request, service_id):
    quantity = int(request.POST.get('quantity', 1)) # Получаем количество из POST, по умолчанию 1
    cart = request.session.get('cart', {}) # Получаем корзину из сессии или пустой словарь

    if service_id in cart:
        cart[service_id] += quantity # Увеличиваем количество, если услуга уже в корзине
    else:
        cart[service_id] = quantity # Добавляем услугу в корзину

    request.session['cart'] = cart # Сохраняем обновленную корзину в сессию
    return redirect('view_cart') # Перенаправляем на страницу корзины

def remove_from_cart(request, service_id):
    cart = request.session.get('cart', {}) # Получаем корзину из сессии

    if service_id in cart:
        del cart[service_id] # Удаляем услугу из корзины
        request.session['cart'] = cart # Обновляем сессию

    return redirect('view_cart') # Перенаправляем на страницу корзины

def update_cart_quantity(request, service_id):
    quantity = int(request.POST.get('quantity', 1)) # Получаем новое количество из POST, по умолчанию 1
    if quantity < 1:
        return remove_from_cart(request, service_id) # Если количество < 1, удаляем из корзины

    cart = request.session.get('cart', {}) # Получаем корзину из сессии

    if service_id in cart:
        cart[service_id] = quantity # Обновляем количество услуги в корзине
        request.session['cart'] = cart # Обновляем сессию

    return redirect('view_cart') # Перенаправляем на страницу корзины

def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart'] # Удаляем корзину из сессии
    return redirect('view_cart') # Перенаправляем на страницу корзины