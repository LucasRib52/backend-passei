from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # URLs de Administração
    path('admin/', views.AdminSaleViewSet.as_view(), name='admin-sale-list'),
    path('admin/<int:id>/', views.AdminSaleDetailView.as_view(), name='admin-sale-detail'),
    path('admin/list/', views.AdminSaleListView.as_view(), name='admin-sale-list-simple'),
    path('admin/statistics/', views.sales_statistics, name='admin-sales-statistics'),
    
    # URLs de Integração Asaas
    path('create-and-redirect/', views.create_sale_and_redirect, name='create-sale-and-redirect'),
    path('create-cart-and-redirect/', views.create_cart_sale_and_redirect, name='create-cart-sale-and-redirect'),
    path('<int:sale_id>/payment-status/', views.get_payment_status, name='get-payment-status'),
] 