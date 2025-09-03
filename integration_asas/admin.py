from django.contrib import admin
from .models import AsaasPayment, AsaasWebhookLog


@admin.register(AsaasPayment)
class AsaasPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'customer_name', 'asaas_id', 'payment_type', 'status', 
        'value', 'due_date', 'payment_date', 'webhook_received'
    ]
    list_filter = [
        'status', 'payment_type', 'webhook_received', 'created_at'
    ]
    search_fields = [
        'customer_name', 'customer_email', 'asaas_id', 'asaas_customer_id'
    ]
    readonly_fields = [
        'asaas_id', 'asaas_customer_id', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('sale', 'customer_name', 'customer_email', 'customer_cpf_cnpj')
        }),
        ('Dados do Pagamento', {
            'fields': ('asaas_id', 'asaas_customer_id', 'payment_type', 'status', 'value')
        }),
        ('Datas', {
            'fields': ('due_date', 'payment_date')
        }),
        ('Dados Específicos', {
            'fields': ('description', 'pix_qr_code', 'bank_slip_url'),
            'classes': ('collapse',)
        }),
        ('Webhook', {
            'fields': ('webhook_received', 'last_webhook_update'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AsaasWebhookLog)
class AsaasWebhookLogAdmin(admin.ModelAdmin):
    list_display = [
        'event_type', 'payment_id', 'webhook_id', 'processed', 
        'received_at', 'processed_at'
    ]
    list_filter = [
        'event_type', 'processed', 'received_at'
    ]
    search_fields = [
        'webhook_id', 'payment_id', 'event_type'
    ]
    readonly_fields = [
        'webhook_id', 'event_type', 'payment_id', 'raw_data', 'received_at'
    ]
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('webhook_id', 'event_type', 'payment_id')
        }),
        ('Dados Recebidos', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('processed', 'processed_at', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('received_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Webhooks são criados automaticamente, não devem ser criados manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Permite apenas marcar como processado"""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Não permite deletar logs de webhook"""
        return False
