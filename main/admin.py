from django.contrib import admin
from .models import User, Service, Order, Transaction, Holiday, Category, ConsultationBooking, ConsultationSlot
import datetime

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
 
def approve_services(modeladmin, request, queryset):
    for service in queryset:
        service.status = 'approved'
        service.moderated_by = request.user 
        service.moderated_at = datetime.datetime.now()
        service.save()
approve_services.short_description = "Одобрить выбранные услуги"

def reject_services(modeladmin, request, queryset): 
    for service in queryset:
        service.status = 'rejected'
        service.moderated_by = request.user 
        service.moderated_at = datetime.datetime.now()
        service.save()
reject_services.short_description = "Отклонить выбранные услуги"

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'isAvaliable', 'execution_time_days', 'category', 'status', 'moderated_by', 'moderated_at') 
    list_editable = ('isAvaliable', 'execution_time_days', 'category', 'status') 
    list_filter = ('status', 'category', 'moderated_by', 'moderated_at') 
    actions = [approve_services, reject_services] 


admin.site.register(User, UserAdmin) # для админки
admin.site.register(Service, ServiceAdmin) # да, и что теперь? 
admin.site.register(Order)
admin.site.register(Transaction)
admin.site.register(Holiday) 
admin.site.register(Category) 
admin.site.register(ConsultationSlot) 
admin.site.register(ConsultationBooking) 
