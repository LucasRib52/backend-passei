from django.urls import path
from . import views

app_name = 'integration_asas'

urlpatterns = [
    # Endpoints de pagamento
    path('create-payment/', views.create_payment, name='create_payment'),
    path('payment/<str:payment_id>/status/', views.get_payment_status, name='get_payment_status'),
    path('payment/<str:payment_id>/cancel/', views.cancel_payment, name='cancel_payment'),
    
    # Listagens
    path('payments/', views.list_payments, name='list_payments'),
    path('webhook-logs/', views.list_webhook_logs, name='list_webhook_logs'),
    
    # Webhook (sem autenticação)
    path('webhook/', views.AsaasWebhookView.as_view(), name='webhook'),
]
