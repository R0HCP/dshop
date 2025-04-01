from django.contrib import admin
from .models import User, Service, Order, Transaction, Holiday 

def toggle_is_trusted_action(modeladmin, request, queryset):
    for user in queryset:
        user.isTrusted = not user.isTrusted
        user.save()
    if user.isTrusted:
        message = "Доверие снято"
    else:
        message = "Доверие выдано"
    modeladmin.message_user(request, f"{message} для выбранных пользователей.")
toggle_is_trusted_action.short_description = "Переключить статус 'Доверенный'" 

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'isTrusted', 'is_staff', 'is_superuser') 
    list_filter = ('isTrusted', 'is_staff', 'is_superuser') 
    actions = [toggle_is_trusted_action]
 

class ServiceAdmin(admin.ModelAdmin): 
    list_display = ('title', 'price', 'isAvaliable', 'execution_time_days') 
    list_editable = ('isAvaliable', 'execution_time_days') #  прямо в списке

admin.site.register(User, UserAdmin) # для админки
admin.site.register(Service, ServiceAdmin) # да, и что теперь? 
admin.site.register(Order)
admin.site.register(Transaction)
admin.site.register(Holiday) 
