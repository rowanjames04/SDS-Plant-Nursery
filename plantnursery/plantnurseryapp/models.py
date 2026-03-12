from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    # Everything is inherited from 'AbstractUser': first_name, last_name, email, password, and is_staff.
    
    def __str__(self):
        return f"{self.get_full_name()} - {'Employee' if self.is_staff else 'Customer'}"
