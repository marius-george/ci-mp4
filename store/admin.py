from django.contrib import admin
from .models import Category, Product

# Register your models here.

admin.site.register(Category)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'available', 'created', 'updated']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 10

    
admin.site.register(Product)