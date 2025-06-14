from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms 
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AddServiceForm, OrderServiceForm, EditServiceForm, UserProfileEditForm, ConsultationSlotForm, DateRangeForm
from .models import Service, Order, Holiday, User, Category, ConsultationSlot, ConsultationBooking
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse 
import datetime
from django.utils import timezone
from django.conf import settings 
from django.db import transaction # Импортируем transaction для атомарности
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from .forms import UserProfileEditForm, AdminOrderStatusForm 
from django.db.models import Q # Для сложных запросов
from django.core.paginator import Paginator # Для пагинации (если заказов много)


try:
    pdfmetrics.registerFont(TTFont('IBMPlexSerif-Regular', 'static/fonts/IBMPlexSerif-Regular.ttf'))
except Exception as e:
    print(f"Ошибка загрузки шрифта IBMPlexSerif-Regular для PDF: {e}")


def price_list_view(request):
    services = Service.objects.filter(isAvaliable=True).select_related('category', 'user').order_by('category__name', 'title') # Получаем все доступные услуги, сортируем по категории и названию
    categories = Category.objects.all().order_by('name') # Получаем все категории для фильтра

    # Фильтрация по категориям
    category_id = request.GET.get('category')
    selected_category_id = None
    if category_id:
        try:
            selected_category_id = int(category_id) # Преобразуем в int для сравнения в шаблоне
            services = services.filter(category_id=category_id)
        except (ValueError, TypeError):
            pass # Игнорируем нечисловые значения категории

    context = {
        'services': services,
        'categories': categories,
        'selected_category_id': selected_category_id, # Передаем ID выбранной категории
    }
    return render(request, 'main/price_list.html', context)


@login_required
def view_agreement_details(request, order_id):
    order = get_object_or_404(Order.objects.select_related('user', 'service', 'service__user'), pk=order_id)

    # Проверка, что текущий пользователь является покупателем или продавцом в этом заказе (или админом)
    if not (request.user == order.user or request.user == order.service.user or request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("У вас нет доступа к этому документу.")

    context = {
        'order': order,
    }
    return render(request, 'main/agreement_details.html', context)


@staff_member_required
def admin_sales_report_view(request):
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            end_date_with_time = timezone.make_aware(
                datetime.datetime.combine(end_date, datetime.time.max)
            )

            category_sales = Order.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date_with_time
            ).select_related('service__category').values(
                'service__category__name'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum('total_price')
            ).order_by('-total_revenue')

            daily_category_sales = Order.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date_with_time
            ).annotate(
                date=TruncDate('created_at')
            ).values(
                'date', 'service__category__name'
            ).annotate(
                daily_quantity=Sum('quantity')
            ).order_by('date', 'service__category__name')

            pdf_buffer = generate_sales_report_pdf(
                start_date, end_date, category_sales, daily_category_sales, request.user
            )

            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.pdf"'
            return response
    else:
        form = DateRangeForm()

    return render(request, 'main/admin_sales_report.html', {'form': form})

def generate_sales_report_pdf(start_date, end_date, category_sales, daily_category_sales, user):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'IBMPlexSerif-Regular'
    styles['Heading1'].fontName = 'IBMPlexSerif-Regular'
    styles['Heading2'].fontName = 'IBMPlexSerif-Regular'

    story = []

    story.append(Paragraph(f"Отчет о продажах с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}", styles['h1']))
    story.append(Paragraph(f"Сгенерирован: {timezone.now().strftime('%d.%m.%Y %H:%M')} пользователем {user.username}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Общие продажи по категориям", styles['h2']))
    story.append(Spacer(1, 0.1*inch))

    data_cat_table = [['Категория', 'Продано (шт.)', 'Выручка (руб.)']]
    category_names = []
    category_revenues = []
    for sale in category_sales:
        category_name = sale['service__category__name'] if sale['service__category__name'] else 'Без категории'
        data_cat_table.append([
            category_name,
            str(sale['total_quantity']),
            f"{sale['total_revenue']:.2f}"
        ])
        category_names.append(category_name)
        category_revenues.append(float(sale['total_revenue'])) # Для графика

    if data_cat_table:
        cat_table = Table(data_cat_table)
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'IBMPlexSerif-Regular'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 0.3*inch))

        if category_names and category_revenues:
            story.append(Paragraph("Распределение выручки по категориям", styles['h2']))
            story.append(Spacer(1, 0.1*inch))
            try:
                fig, ax = plt.subplots(figsize=(6, 6)) 
                ax.pie(category_revenues, labels=category_names, autopct='%1.1f%%', startangle=90)
                ax.axis('equal') 
                plt.title("Выручка по категориям", fontname='IBMPlexSerif')

                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', bbox_inches='tight')
                plt.close(fig)
                img_buffer.seek(0)
                story.append(Image(img_buffer, width=4*inch, height=4*inch))
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                story.append(Paragraph(f"Не удалось создать круговую диаграмму: {e}", styles['Normal']))

    story.append(PageBreak()) 
    story.append(Paragraph("Динамика продаж по дням и категориям", styles['h2']))
    story.append(Spacer(1, 0.1*inch))

    # Подготовка данных для графика
    dates = sorted(list(set(item['date'] for item in daily_category_sales)))
    categories_in_period = sorted(list(set(item['service__category__name'] if item['service__category__name'] else 'Без категории' for item in daily_category_sales)))
    sales_data_dict = {cat: {date: 0 for date in dates} for cat in categories_in_period}

    for item in daily_category_sales:
        category_name = item['service__category__name'] if item['service__category__name'] else 'Без категории'
        sales_data_dict[category_name][item['date']] = item['daily_quantity']

    if dates and categories_in_period:
        try:
            fig, ax = plt.subplots(figsize=(10, 5)) # Размер мерзкого графика

            for category in categories_in_period:
                quantities = [sales_data_dict[category][date] for date in dates]
                ax.plot(dates, quantities, marker='o', linestyle='-', label=category)

            ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10)) # Автоматическое размещение тиков
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
            plt.xticks(rotation=45, ha='right') # Поворот дат

            ax.set_xlabel("Дата", fontname='IBMPlexSerif')
            ax.set_ylabel("Количество продано (шт.)", fontname='IBMPlexSerif')
            ax.set_title("Продажи по дням и категориям", fontname='IBMPlexSerif')
            ax.legend(prop={'family': 'IBMPlexSerif'}) 
            # ax.set_xlabel("Дата", fontname='IBMPlexSerif-Regular')
            # ax.set_ylabel("Количество продано (шт.)", fontname='IBMPlexSerif-Regular')
            # ax.set_title("Продажи по дням и категориям", fontname='IBMPlexSerif-Regular')
            # ax.legend(prop={'family': 'IBMPlexSerif-Regular'}) 
            ax.grid(True)
            plt.tight_layout() 

            img_buffer_daily = io.BytesIO()
            plt.savefig(img_buffer_daily, format='png')
            plt.close(fig)
            img_buffer_daily.seek(0)
            story.append(Image(img_buffer_daily, width=9*inch, height=4.5*inch)) 
        except Exception as e:
            story.append(Paragraph(f"Не удалось создать график по дням: {e}", styles['Normal']))
    else:
        story.append(Paragraph("Нет данных для построения графика по дням.", styles['Normal']))


    try:
        doc.build(story)
    except Exception as e:
        print(f"Ошибка сборки PDF: {e}")
        buffer = io.BytesIO() # Возвращаем пустой буфер в случае ошибки сборки
    buffer.seek(0)
    return buffer


@login_required
def profile_view(request):
    current_user = request.user # Используем current_user для ясности, что это текущий пользователь сессии
    user_profile_to_display = current_user # Пользователь, чей профиль мы отображаем (по умолчанию - свой)

    # Получаем заказы и бронирования для текущего пользователя (клиента)
    user_orders = Order.objects.filter(user=current_user).select_related('service').order_by('-created_at')
    user_bookings = ConsultationBooking.objects.filter(client=current_user).select_related('slot', 'slot__seller').order_by('-slot__start_time')

    # Инициализация переменных для администратора
    admin_all_orders = None
    order_status_form_dict = {}
    order_filter_form = AdminOrderFilterForm(request.GET or None) # Инициализируем форму фильтра данными из GET или пустую

    # Логика для администратора
    if current_user.is_staff or current_user.is_superuser:
        admin_all_orders_query = Order.objects.all().select_related('user', 'service', 'service__category').order_by('-created_at')

        if order_filter_form.is_valid(): # Проверяем валидность формы фильтра
            status = order_filter_form.cleaned_data.get('status')
            category = order_filter_form.cleaned_data.get('category')
            date_from = order_filter_form.cleaned_data.get('date_from')
            date_to = order_filter_form.cleaned_data.get('date_to')
            search_query = order_filter_form.cleaned_data.get('search_query')

            if status:
                admin_all_orders_query = admin_all_orders_query.filter(status=status)
            if category:
                admin_all_orders_query = admin_all_orders_query.filter(service__category=category)
            if date_from:
                admin_all_orders_query = admin_all_orders_query.filter(created_at__gte=date_from)
            if date_to:
                admin_all_orders_query = admin_all_orders_query.filter(created_at__lt=date_to + datetime.timedelta(days=1))
            if search_query:
                admin_all_orders_query = admin_all_orders_query.filter(
                    Q(id__icontains=search_query) | # Поиск по ID заказа
                    Q(user__username__icontains=search_query) |
                    Q(service__title__icontains=search_query)
                )
        # Если форма фильтра невалидна или не отправлена, используем полный запрос
        admin_all_orders = admin_all_orders_query

        for order in admin_all_orders:
            order_status_form_dict[order.id] = AdminOrderStatusForm(instance=order, prefix=f"order-{order.id}")

    # Обработка POST-запросов
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_profile':
            profile_form = UserProfileEditForm(request.POST, request.FILES, instance=current_user)
            if profile_form.is_valid():
                saved_user = profile_form.save(commit=False)
                latitude_str = request.POST.get('office_latitude')
                longitude_str = request.POST.get('office_longitude')
                saved_user.office_latitude = float(latitude_str) if latitude_str else None
                saved_user.office_longitude = float(longitude_str) if longitude_str else None
                saved_user.save()
                # Можно добавить сообщение messages.success(request, 'Профиль успешно обновлен!')
                return redirect('profile')
            # Если форма профиля невалидна, она будет передана в контекст ниже
        elif action == 'change_order_status':
            if current_user.is_staff or current_user.is_superuser:
                order_id = request.POST.get('order_id')
                if order_id:
                    order_to_update = get_object_or_404(Order, pk=order_id)
                    # Пересоздаем форму с данными POST для конкретного заказа
                    status_form = AdminOrderStatusForm(request.POST, instance=order_to_update, prefix=f"order-{order_id}")
                    if status_form.is_valid():
                        status_form.save()
                        # messages.success(request, f'Статус заявки #{order_id} успешно изменен.')
                        return redirect('profile')
                    else:
                        # Если форма статуса невалидна, нужно как-то обработать ошибку
                        # Например, добавить ее в order_status_form_dict для отображения в шаблоне
                        order_status_form_dict[int(order_id)] = status_form # Обновляем форму в словаре, чтобы показать ошибки
                        # messages.error(request, f'Ошибка изменения статуса заявки #{order_id}.')
            # Если не админ, можно вернуть HttpResponseForbidden или проигнорировать
        elif action == 'toggle_trust':
            if current_user.is_staff or current_user.is_superuser:
                user_id_to_toggle = request.POST.get('user_id') # ID пользователя, чей статус меняем (в данном случае, это user_profile_to_display.id)
                if user_id_to_toggle:
                    try:
                        user_to_toggle = User.objects.get(pk=user_id_to_toggle)
                        user_to_toggle.isTrusted = not user_to_toggle.isTrusted
                        user_to_toggle.save()
                        # messages.success(request, f'Статус доверия для пользователя {user_to_toggle.username} изменен.')
                    except User.DoesNotExist:
                        # messages.error(request, 'Пользователь для изменения статуса доверия не найден.')
                        pass # Обработка ошибки, если пользователь не найден
                return redirect('profile')
            # Если не админ, можно вернуть HttpResponseForbidden или проигнорировать

        # После обработки POST, если не было redirect, нужно подготовить форму профиля для отображения (возможно, с ошибками)
        profile_form = UserProfileEditForm(request.POST if action == 'save_profile' else None, instance=current_user)

    else: # Если метод GET
        profile_form = UserProfileEditForm(instance=current_user)

    context = {
        'form': profile_form, # Эта переменная теперь всегда содержит актуальную форму профиля
        'user_profile_to_display': user_profile_to_display, # Пользователь, чей профиль отображается
        'user_orders': user_orders,
        'user_bookings': user_bookings,
        'admin_all_orders': admin_all_orders,
        'order_status_form_dict': order_status_form_dict,
        'order_filter_form': order_filter_form,
        'yandex_maps_api_key': settings.YANDEX_MAPS_API_KEY,
    }
    return render(request, 'main/profile.html', context)




class AdminOrderFilterForm(forms.Form):
    status = forms.ChoiceField(choices=[('', 'Все статусы')] + Order.STATUS_CHOICES, required=False, label="Статус")
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, label="Категория", empty_label="Все категории")
    date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Дата от")
    date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Дата до")
    search_query = forms.CharField(required=False, label="Поиск (ID, Имя пользователя, Название услуги)")


# --- Представление для генерации PDF отчета ---
@login_required
def download_purchase_report_pdf(request):
    # Получаем заказы пользователя
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at').select_related('service')

    # Создаем байтовый буфер для PDF
    buffer = io.BytesIO()

    # Создаем PDF документ
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # --- Настройка шрифтов для кириллицы (важно!) ---
    # Убедитесь, что у вас есть шрифт IBMPlexSerif-Regular.ttf или другой шрифт, поддерживающий кириллицу
    # Скачать можно, например, с https://dejavu-fonts.github.io/
    # Поместите файл шрифта в ваш проект (например, в папку static/fonts/)
    try:
        # Укажите правильный путь к вашему файлу шрифта
        pdfmetrics.registerFont(TTFont('IBMPlexSerif-Regular', 'static/fonts/IBMPlexSerif-Regular.ttf'))
        styles['Normal'].fontName = 'IBMPlexSerif-Regular'
        styles['Heading1'].fontName = 'IBMPlexSerif-Regular'
        styles['Heading2'].fontName = 'IBMPlexSerif-Regular'
    except Exception as e:
        print(f"Ошибка загрузки шрифта для PDF: {e}")
        # Если шрифт не найден, кириллица может отображаться некорректно
    # --------------------------------------------------

    story = [] # Список элементов для PDF

    # Заголовок
    story.append(Paragraph(f"Отчет о покупках для {request.user.username}", styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    # Данные для таблицы
    data = [['Дата заказа', 'Услуга', 'Количество', 'Цена']]
    total_spent = 0

    for order in user_orders:
        data.append([
            order.created_at.strftime('%d.%m.%Y %H:%M'),
            order.service.title,
            str(order.quantity),
            str(order.total_price)
        ])
        total_spent += order.total_price

    # Создаем таблицу
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'IBMPlexSerif-Regular'), # Используем шрифт
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'IBMPlexSerif-Regular') # Используем шрифт для данных
    ]))

    story.append(table)
    story.append(Spacer(1, 0.2*inch))

    # Итоговая сумма
    story.append(Paragraph(f"Итого потрачено: {total_spent}", styles['h2']))

    # Собираем PDF
    doc.build(story)

    # Устанавливаем указатель буфера в начало
    buffer.seek(0)

    # Возвращаем PDF как ответ
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="purchase_report_{request.user.username}.pdf"'
    return response

@login_required
def client_profile_view(request, booking_id):
    booking = get_object_or_404(ConsultationBooking, pk=booking_id, slot__seller=request.user) 
    client = booking.client

    context = {
        'client': client,
        'booking': booking, 
    }
    return render(request, 'main/client_profile.html', context)

@login_required
def seller_slots_view(request):
    slots = ConsultationSlot.objects.filter(seller=request.user).order_by('start_time')
    if request.method == 'POST':
        form = ConsultationSlotForm(request.POST)
        if form.is_valid():
            days_of_week = form.cleaned_data['days_of_week']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            duration_minutes = form.cleaned_data['duration_minutes']
            break_start_time = form.cleaned_data['break_start_time']
            break_end_time = form.cleaned_data['break_end_time']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date'] or datetime.date.today() + datetime.timedelta(days=365)

            current_date = start_date
            while current_date <= end_date:
                if str(current_date.weekday()) in days_of_week:
                    current_slot_start = datetime.datetime.combine(current_date, start_time, tzinfo=timezone.get_current_timezone()) 
                    current_slot_end = datetime.datetime.combine(current_date, start_time, tzinfo=timezone.get_current_timezone()) 

                    while current_slot_end.time() < end_time:
                        current_slot_end += datetime.timedelta(minutes=duration_minutes)

                        if break_start_time and break_end_time: 
                            slot_break_start = datetime.datetime.combine(current_date, break_start_time, tzinfo=timezone.get_current_timezone()).time() 
                            slot_break_end = datetime.datetime.combine(current_date, break_end_time, tzinfo=timezone.get_current_timezone()).time() 

                            if not (slot_break_start <= current_slot_start.time() < slot_break_end or slot_break_start < current_slot_end.time() <= slot_break_end): 
                                if current_slot_end.time() <= end_time:
                                    ConsultationSlot.objects.create(
                                        seller=request.user,
                                        start_time=current_slot_start,
                                        end_time=current_slot_end
                                    )
                        else: 
                            if current_slot_end.time() <= end_time: 
                                ConsultationSlot.objects.create(
                                    seller=request.user,
                                    start_time=current_slot_start,
                                    end_time=current_slot_end
                                )
                        current_slot_start = current_slot_end 

                current_date += datetime.timedelta(days=1) 

            return redirect('seller_slots')
    else:
        form = ConsultationSlotForm()
    return render(request, 'main/seller_slots.html', {'form': form, 'slots': slots})



@login_required 
def service_consultation_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    seller = service.user

    nearest_available_slot = ConsultationSlot.objects.filter(
        seller=seller,
        is_booked=False,
        start_time__gte=timezone.now() 
    ).order_by('start_time').first() 

    if request.method == 'POST':
        if nearest_available_slot:
            try:
                with transaction.atomic():
                    slot_to_book = ConsultationSlot.objects.select_for_update().get(
                        pk=nearest_available_slot.pk,
                        is_booked=False 
                    )
                    ConsultationBooking.objects.create(slot=slot_to_book, client=request.user)
                    slot_to_book.is_booked = True
                    slot_to_book.save()
                    return render(request, 'main/consultation_success.html', {'slot': slot_to_book})
            except ConsultationSlot.DoesNotExist:
                pass 
            except Exception as e:
                print(f"Ошибка при бронировании слота: {e}") 

        context = {
            'service': service,
            'seller': seller,
            'error': 'К сожалению, не удалось найти или забронировать ближайший доступный слот. Попробуйте позже.'
        }
        return render(request, 'main/service_consultation.html', context)

    # Если метод GET
    context = {
        'service': service,
        'seller': seller,
        'nearest_slot': nearest_available_slot, 
    }
    return render(request, 'main/service_consultation.html', context)

def seller_detail_view(request, seller_id):
    seller = get_object_or_404(User, pk=seller_id)
    services = Service.objects.filter(user=seller, isAvaliable=True) 

    try:
        lat_str = f"{seller.office_latitude:.9f}" if seller.office_latitude is not None else "null"
        lon_str = f"{seller.office_longitude:.9f}" if seller.office_longitude is not None else "null"
    except (ValueError, TypeError):
        lat_str = "null"
        lon_str = "null"
        print(f"Warning: Could not format coordinates for seller {seller_id}") #

    context = {
        'seller': seller,
        'services': services,
        'yandex_maps_api_key': settings.YANDEX_MAPS_API_KEY,
        'office_latitude_str': lat_str,
        'office_longitude_str': lon_str,
    }
    return render(request, 'main/seller_detail.html', context)


@staff_member_required 
def approve_service_from_index_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    service.status = 'approved'
    service.moderated_by = request.user
    service.moderated_at = datetime.datetime.now()
    service.save()
    return redirect('index')

@staff_member_required 
def reject_service_from_index_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    service.status = 'rejected'
    service.moderated_by = request.user
    service.moderated_at = datetime.datetime.now()
    service.save()
    return redirect('index')


@login_required 
def checkout_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    errors = [] 

    if not cart:
        
        return render(request, 'main/cart.html', {'cart_items': [], 'total_price': 0, 'errors': ['Тут ничего нет .']})

    for service_id, quantity in list(cart.items()): 
        try:
            service = Service.objects.get(pk=service_id)
            if not service.isAvaliable:
                 errors.append(f"Услуга '{service.title}' больше недоступна.")
                 del cart[service_id] 
                 continue

            if service.quantity < quantity:
                errors.append(f"Недостаточное количество для услуги '{service.title}'. Доступно: {service.quantity}, запрошено: {quantity}.")
                del cart[service_id]
                continue 

            item_total_price = service.price * quantity
            cart_items.append({
                'service': service,
                'quantity': quantity,
                'total_price': item_total_price,
            })
            total_price += item_total_price

        except Service.DoesNotExist:
             errors.append(f"Услуга с ID {service_id} не найдена.")
             del cart[service_id]

    request.session['cart'] = cart

    if not cart_items and request.method != 'POST':
         request.session['cart_errors'] = errors
         return redirect('view_cart') 

    if request.method == 'POST':
        if errors:
             context = {
                 'cart_items': cart_items,
                 'total_price': total_price,
                 'errors': errors, 
             }
             return render(request, 'main/checkout.html', context)

        for item in cart_items:
            service = item['service']
            quantity = item['quantity']

            service.refresh_from_db() 
            if service.quantity < quantity or not service.isAvaliable:
                 request.session['cart_errors'] = [f"К сожалению, количество товара '{service.title}' изменилось. Пожалуйста, проверьте наличие."]
                 current_cart = request.session.get('cart', {})
                 if str(service.id) in current_cart:
                     del current_cart[str(service.id)]
                     request.session['cart'] = current_cart
                 return redirect('view_cart')

            order = Order.objects.create(
                user=request.user,
                service=service,
                quantity=quantity,
                total_price=item['total_price']
            )
            service.quantity -= quantity
            if service.quantity == 0:
                service.isAvaliable = False
            service.save() # Теперь эта строка безопасна


        return render(request, 'main/checkout_success.html', {'total_price': total_price})

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'errors': errors,
    }
    return render(request, 'main/checkout.html', context)

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

                holidays = Holiday.objects.all()
                start_date = order.created_at
                estimated_completion_date = calculate_estimated_completion_date(start_date, service.execution_time_days, holidays)

                print(f"Рассчитанная дата выполнения перед сохранением: {estimated_completion_date}") # Отладка
                print(f"Тип данных даты выполнения: {type(estimated_completion_date)}") # Отладка

                order.estimated_completion_date = estimated_completion_date

                try: # Оборачиваем сохранение в try-except для отладки ошибок
                    order.save()
                    print("Заявка успешно сохранен с датой выполнения.") # Отладка
                except Exception as e:
                    print(f"Ошибка при сохранении заявки  {e}") # Отладка

                return render(request, 'main/order_success.html', {'order_id': order.id, 'seller': service.user, 'completion_date': estimated_completion_date})
            else:
                return HttpResponse("Извините, недостаточно товара на складе.")
    else:
        form = OrderServiceForm()
    return render(request, 'main/order_form.html', {'form': form, 'service': service})




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
    services = Service.objects.filter(isAvaliable=True, status='approved').select_related('category') 
    categories = Category.objects.all()
    max_price = Service.objects.filter(isAvaliable=True).order_by('-price').first()
    if max_price:
        max_price = int(max_price.price)
    else:
        max_price = 1000

    category_id = request.GET.get('category')
    if category_id:
        services = services.filter(category_id=category_id)

    search_query = request.GET.get('search')
    if search_query:
        services = services.filter(title__icontains=search_query)

    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        services = services.order_by('price')
    elif sort_by == 'price_desc':
        services = services.order_by('-price')
    elif sort_by == 'title_asc':
        services = services.order_by('title')
    elif sort_by == 'title_desc':
        services = services.order_by('-title')

    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')

    if price_from:
        services = services.filter(price__gte=price_from)
    if price_to:
        services = services.filter(price__lte=price_to)


    pending_services = None 
    if request.user.is_staff or request.user.is_superuser: 
        pending_services = Service.objects.filter(status='pending').select_related('category')

    context = {
        'services': services,
        'categories': categories,
        'max_price': max_price,
        'price_from_value': price_from or 0,
        'price_to_value': price_to or max_price,
        'pending_services': pending_services, 
    }
    return render(request, 'main/index.html', context)


def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    order_form = OrderServiceForm()
    seller = service.user 

    try:
        lat_str = f"{seller.office_latitude:.9f}" if seller.office_latitude is not None else "null"
        lon_str = f"{seller.office_longitude:.9f}" if seller.office_longitude is not None else "null"
    except (ValueError, TypeError):
        lat_str = "null"
        lon_str = "null"
        print(f"Warning: Could not format coordinates for user {seller.id} on service detail page {service_id}")

    context = {
        'service': service,
        'order_form': order_form,
        'seller': seller, # Передаем продавца на всякий случай
        'office_latitude_str': lat_str,
        'office_longitude_str': lon_str,
        'yandex_maps_api_key': settings.YANDEX_MAPS_API_KEY,
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
        service_id = request.POST.get('service_id')
        if not service_id:
            return HttpResponseForbidden("Не указан ID услуги для возврата.")

        try:
            user = User.objects.get(pk=user_id)
            user.isTrusted = not user.isTrusted
            user.save()
            return redirect('service_detail', service_id=service_id)
        except User.DoesNotExist:
            return HttpResponseForbidden("Пользователь не найден.")
        except ValueError:
            return HttpResponseForbidden("Некорректный ID услуги для возврата.")
    else:
        return HttpResponseForbidden("Недопустимый метод запроса.")

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid(): # Если форма НЕ валидна, блок if не выполнится
            user = form.save()
            login(request, user)
            return redirect('index')
        # Если form.is_valid() == False, Django автоматически добавит ошибки в form.errors
        # и мы просто рендерим шаблон снова с этой же формой (которая теперь содержит ошибки)
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form}) # Передаем форму с ошибками (если они есть)

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

                holidays = Holiday.objects.all()
                start_date = order.created_at
                estimated_completion_date = calculate_estimated_completion_date(start_date, service.execution_time_days, holidays)
                order.estimated_completion_date = estimated_completion_date

                return render(request, 'main/order_success.html', {'order_id': order.id, 'seller': service.user, 'completion_date': estimated_completion_date})
            else:
                return HttpResponse("Извините, недостаточно товара на складе.")
    else:
        form = OrderServiceForm()
    return render(request, 'main/order_form.html', {'form': form, 'service': service})

def is_trusted_user(user):
    return user.is_authenticated and user.isTrusted

@user_passes_test(is_trusted_user)
def add_service_view(request):
    if request.method == 'POST':
        form = AddServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.user = request.user
            service.status = 'approved' 
            service.save()
            return redirect('service_detail', service_id=service.id)
    else:
        form = AddServiceForm()
    return render(request, 'main/add_service.html', {'form': form})

@login_required
def edit_service_view(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if service.user != request.user:
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


@login_required
def toggle_trusted_view(request):
    if request.user.is_staff or request.user.is_superuser:
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                user.isTrusted = not user.isTrusted
                user.save()
                return redirect('admin:main_user_change', object_id=user_id)
            except User.DoesNotExist:
                return HttpResponseForbidden("Пользователь не найден.")
        else:
            return HttpResponseForbidden("Не указан ID пользователя.")
    else:
        return HttpResponseForbidden("У вас нет прав для выполнения этого действия.")

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    errors = request.session.pop('cart_errors', []) if 'cart_errors' in request.session else [] # Получаем и удаляем ошибки из сессии

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
        'errors': errors, # Передаем список ошибок в шаблон
    }
    return render(request, 'main/cart.html', context)

def add_to_cart(request, service_id):
    quantity = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})

    if service_id in cart:
        cart[service_id] += quantity
    else:
        cart[service_id] = quantity

    request.session['cart'] = cart
    return redirect('view_cart')

def remove_from_cart(request, service_id):
    cart = request.session.get('cart', {})

    if service_id in cart:
        del cart[service_id]
        request.session['cart'] = cart

    return redirect('view_cart')

def update_cart_quantity(request, service_id):
    # ----- НАЧАЛО ОТЛАДКИ -----
    print(f"--- Обновление количества в КОРЗИНЕ: service_id={service_id} ---")
    print(f"Метод запроса: {request.method}")
    print(f"Данные POST: {request.POST}")
    # ----- КОНЕЦ ОТЛАДКИ -----

    if request.method == 'POST': # Обрабатываем только POST
        quantity_str = request.POST.get('quantity', '1') # Получаем новое количество из POST
        try:
            quantity = int(quantity_str)
            if quantity < 1: # Если количество < 1, удаляем товар
                print(f"Количество < 1 ({quantity}), вызываем remove_from_cart для service_id={service_id}")
                return remove_from_cart(request, service_id)
        except ValueError:
            print(f"Не удалось преобразовать quantity='{quantity_str}' в int, устанавливаем 1")
            quantity = 1 # Если не удалось преобразовать, ставим 1 (или можно вернуть ошибку/не менять)

        print(f"Обработанное количество для обновления: {quantity}") # Отладка

        cart = request.session.get('cart', {})
        print(f"Корзина ДО обновления количества: {cart}") # Отладка
        service_id_str = str(service_id)

        if service_id_str in cart:
            cart[service_id_str] = quantity # Обновляем количество услуги в корзине
            request.session['cart'] = cart
            request.session.modified = True # Явно помечаем сессию как измененную
            print(f"Корзина ПОСЛЕ обновления количества: {request.session.get('cart')}") # Отладка
        else:
            print(f"Ключ {service_id_str} не найден в корзине для обновления количества.")

    return redirect('view_cart') # Перенаправляем на страницу корзины в любом случае (или обрабатываем ошибки иначе)

def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('view_cart')

def checkout_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    errors = []

    if not cart:
        return render(request, 'main/cart.html', {'cart_items': [], 'total_price': 0, 'errors': ['Ничего нет.']})

    for service_id, quantity in list(cart.items()):
        try:
            service = Service.objects.get(pk=service_id)
            if not service.isAvaliable:
                errors.append(f"Услуга '{service.title}' больше недоступна.")
                del cart[service_id]
                continue

            if service.quantity < quantity:
                errors.append(f"Недостаточное количество для услуги '{service.title}'. Доступно: {service.quantity}, запрошено: {quantity}.")
                del cart[service_id]
                continue

            item_total_price = service.price * quantity
            cart_items.append({
                'service': service,
                'quantity': quantity,
                'total_price': item_total_price,
            })
            total_price += item_total_price

        except Service.DoesNotExist:
            errors.append(f"Услуга с ID {service_id} не найдена.")
            del cart[service_id]

    request.session['cart'] = cart

    if not cart_items and request.method != 'POST':
        request.session['cart_errors'] = errors
        return redirect('view_cart')

    if request.method == 'POST':
        if errors:
            context = {
                'cart_items': cart_items,
                'total_price': total_price,
                'errors': errors,
            }
            return render(request, 'main/checkout.html', context)

        for item in cart_items:
            service = item['service']
            quantity = item['quantity']

            service.refresh_from_db()
            if service.quantity < quantity or not service.isAvaliable:
                request.session['cart_errors'] = [f"К сожалению, количество товара '{service.title}' изменилось. Пожалуйста, проверьте наличие."]
                current_cart = request.session.get('cart', {})
                if str(service.id) in current_cart:
                    del current_cart[str(service.id)]
                    request.session['cart'] = current_cart
                return redirect('view_cart')

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

        del request.session['cart']

        return render(request, 'main/checkout_success.html', {'total_price': total_price})

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'errors': errors,
    }
    return render(request, 'main/checkout.html', context)

