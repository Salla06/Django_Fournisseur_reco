from django.contrib import admin
from .models import Supplier, SupplierProduct


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('company_name', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'product', 'added_at')
    list_filter = ('supplier',)
    search_fields = ('supplier__company_name', 'product__name')
    readonly_fields = ('added_at',)
