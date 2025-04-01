from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), # Главная страница
    path('service/<int:service_id>/', views.service_detail, name='service_detail'), # Детальная страница услуги
    path('register/', views.register_view, name='register'), # Регистрация
    path('login/', views.login_view, name='login'), # Вход
    path('logout/', views.logout_view, name='logout'), # Выход
    path('service/<int:service_id>/order/', views.order_service_view, name='order_service'), # Заказ услуги
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
]