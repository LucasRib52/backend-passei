from django.db import models
from sales.models import Sale


class AsaasPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('RECEIVED', 'Recebido'),
        ('CONFIRMED', 'Confirmado'),
        ('OVERDUE', 'Vencido'),
        ('REFUNDED', 'Reembolsado'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('BOLETO', 'Boleto'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('PIX', 'PIX'),
        
    ]
    
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='asaas_payment')
    asaas_id = models.CharField(max_length=100, unique=True, verbose_name='ID Asaas')
    asaas_customer_id = models.CharField(max_length=100, verbose_name='ID Cliente Asaas')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, verbose_name='Tipo de Pagamento')
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='PENDING', verbose_name='Status')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    due_date = models.DateField(verbose_name='Data de Vencimento')
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name='Data do Pagamento')
    description = models.TextField(blank=True, verbose_name='Descrição')
    customer_name = models.CharField(max_length=200, verbose_name='Nome do Cliente')
    customer_email = models.EmailField(verbose_name='Email do Cliente')
    customer_cpf_cnpj = models.CharField(max_length=20, blank=True, verbose_name='CPF/CNPJ')
    pix_qr_code = models.TextField(blank=True, verbose_name='QR Code PIX')
    bank_slip_url = models.URLField(blank=True, verbose_name='URL do Boleto')
    invoice_url = models.URLField(blank=True, verbose_name='URL da Fatura')
    payment_link_url = models.URLField(blank=True, verbose_name='URL do Link de Pagamento')
    # Parcelamento de boleto
    installment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID do Parcelamento')
    installment_count = models.IntegerField(blank=True, null=True, verbose_name='Número de Parcelas')
    installment_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Valor por Parcela')
    webhook_received = models.BooleanField(default=False, verbose_name='Webhook Recebido')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Pagamento Asaas'
        verbose_name_plural = 'Pagamentos Asaas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.asaas_id} - {self.get_status_display()}"
    
    @property
    def is_paid(self):
        return self.status in ['RECEIVED', 'CONFIRMED']
    
    @property
    def is_overdue(self):
        return self.status == 'OVERDUE'
    
    @property
    def is_pending(self):
        return self.status == 'PENDING'


class AsaasWebhookLog(models.Model):
    webhook_id = models.CharField(max_length=100, unique=True, verbose_name='ID do Webhook')
    event_type = models.CharField(max_length=100, verbose_name='Tipo do Evento')
    payment_id = models.CharField(max_length=100, verbose_name='ID do Pagamento')
    raw_data = models.JSONField(verbose_name='Dados Recebidos')
    processed = models.BooleanField(default=False, verbose_name='Processado')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Processado em')
    error_message = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    received_at = models.DateTimeField(auto_now_add=True, verbose_name='Recebido em')
    
    class Meta:
        verbose_name = 'Log de Webhook Asaas'
        verbose_name_plural = 'Logs de Webhook Asaas'
        ordering = ['-received_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.payment_id} - {self.received_at}"
