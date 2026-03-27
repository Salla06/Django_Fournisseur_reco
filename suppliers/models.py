from django.db import models
from recommendations.models import CustomUser, Product


class Supplier(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='supplier')
    company_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='supplier_logos/', null=True, blank=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

    def get_logo_url(self):
        if self.logo:
            return self.logo.url
        return None


class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplier_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supplier_links')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('supplier', 'product')

    def __str__(self):
        return f"{self.supplier.company_name} → {self.product.name}"
