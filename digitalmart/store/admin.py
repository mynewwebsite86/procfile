# from django.contrib import admin
# from .models import Product

# admin.site.register(Product)

# from django.contrib import admin
# from .models import Product, CartItem

# admin.site.register(Product)
# admin.site.register(CartItem)

from django.contrib import admin
from .models import Product, CartItem, Order, OrderItem

class ProductAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.seller:
            obj.seller = request.user
        obj.save()

admin.site.register(Product, ProductAdmin)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)

from .models import Review
admin.site.register(Review)

from .models import Notification
admin.site.register(Notification)

from .models import Withdrawal
admin.site.register(Withdrawal)

# Register your models here.
