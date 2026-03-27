from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='supplier_register'),
    path('login/', views.login_view, name='supplier_login'),
    path('logout/', views.logout_view, name='supplier_logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='supplier_dashboard'),

    # Produits
    path('products/', views.products_view, name='supplier_products'),
    path('products/add/', views.product_add_view, name='supplier_product_add'),
    path('products/<int:pk>/', views.product_detail_view, name='supplier_product_detail'),
    path('products/<int:pk>/edit/', views.product_edit_view, name='supplier_product_edit'),
    path('products/<int:pk>/delete/', views.product_delete_view, name='supplier_product_delete'),
    path('products/<int:pk>/delete/confirm/', views.product_delete_confirm_view, name='supplier_product_delete_confirm'),

    # Profil
    path('profile/', views.profile_view, name='supplier_profile'),
]
