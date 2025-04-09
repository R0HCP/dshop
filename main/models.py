from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager # <--- Импортируем AbstractBaseUser, PermissionsMixin и UserManager

class User(AbstractBaseUser, PermissionsMixin): 

    
    username = models.CharField(max_length=250, unique=True) 
    password = models.CharField(max_length=250) 
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    first_name = models.CharField(max_length=250, null=True, blank=True)
    last_name = models.CharField(max_length=250, null=True, blank=True)
    dateregister = models.DateTimeField(auto_now_add=True)
    isTrusted = models.BooleanField(default=True)
    pfp = models.ImageField(upload_to='pfp/', null=True, blank=True)

    USERNAME_FIELD = 'username' # 
    REQUIRED_FIELDS = [] 

    objects = UserManager() 

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username

class Category(models.Model): 
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Holiday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.name} ({self.date})"



class Service(models.Model):
    
    STATUS_CHOICES = [ # <--- Определяем варианты статусов модерации
        ('pending', 'На модерации'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    images = models.ImageField(upload_to='images/', null=True, blank=True)
    title = models.CharField(max_length=250)
    description = models.TextField()
    category = models.ForeignKey( 
    Category,
        on_delete=models.SET_NULL, 
        null=True,
        blank=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    isAvaliable = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=1)
    execution_time_days = models.PositiveIntegerField(default=1, help_text="Время выполнения услуги в рабочих днях") 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_services') 
    moderated_at = models.DateTimeField(null=True, blank=True) 
    
    def __str__(self):
        return self.title
    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    estimated_completion_date = models.DateField(null=True, blank=True) 
     
    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    isComplete = models.BooleanField(default=False)
    lastCardDigits = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Транзакция #{self.id} от {self.user.username} {'завершена' if self.isComplete else 'сосите'}"
