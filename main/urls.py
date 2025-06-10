from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), # Главная страница
    path('service/<int:service_id>/', views.service_detail, name='service_detail'), # Детальная страница услуги
    path('register/', views.register_view, name='register'), # Регистрация
    path('login/', views.login_view, name='login'), # Вход
    path('logout/', views.logout_view, name='logout'), # Выход
    path('service/<int:service_id>/order/', views.order_service_view, name='order_service'), # Заявка услуги
    path('service/add/', views.add_service_view, name='add_service'), # Добавление услуги (для доверенных)
    path('profile/', views.profile_view, name='profile'), # Личный кабинет
    path('profile/toggle_trusted/', views.toggle_trusted_view, name='toggle_trusted'), # URL для переключения isTrusted
    path('service/<int:service_id>/edit/', views.edit_service_view, name='edit_service'), # Редактирование услуги
    path('service/<int:service_id>/delete/', views.delete_service_view, name='delete_service'), # URL для удаления услуги
    path('user/<int:user_id>/toggle_trusted_from_service/', views.toggle_trusted_from_service_view, name='toggle_trusted_from_service'), # URL для переключения isTrusted из страницы услуги
    path('cart/', views.view_cart, name='view_cart'), # Страница корзины
    path('cart/add/<int:service_id>/', views.add_to_cart, name='add_to_cart'), # Добавление в корзину
    path('cart/remove/<int:service_id>/', views.remove_from_cart, name='remove_from_cart'), # Удаление из корзины
    path('cart/update/<int:service_id>/', views.update_cart_quantity, name='update_cart_quantity'), # Обновление количества
    path('cart/clear/', views.clear_cart, name='clear_cart'), # Очистка корзины
    path('cart/checkout/', views.checkout_view, name='checkout'), # URL для оформления заказа
    path('seller/<int:seller_id>/', views.seller_detail_view, name='seller_detail'), # страница продавца
    path('service/approve_from_index/<int:service_id>/', views.approve_service_from_index_view, name='approve_service_from_index'), # URL для одобрения с главной
    path('service/reject_from_index/<int:service_id>/', views.reject_service_from_index_view, name='reject_service_from_index'), # URL для отклонения с главной
    path('seller/slots/', views.seller_slots_view, name='seller_slots'), # Страница продавца для управления слотами
    path('service/<int:service_id>/consultation/', views.service_consultation_view, name='service_consultation'), # Страница консультации для услуги
    path('booking/<int:booking_id>/client_profile/', views.client_profile_view, name='client_profile'), # Страница профиля клиента
    path('profile/download_report/', views.download_purchase_report_pdf, name='download_purchase_report'),
    path('profile/sales_report/', views.admin_sales_report_view, name='admin_sales_report'),
    path('order/<int:order_id>/agreement/', views.view_agreement_details, name='view_agreement'),
    path('price-list/', views.price_list_view, name='price_list'), # URL для прейскуранта
]