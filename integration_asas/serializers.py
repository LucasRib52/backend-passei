from rest_framework import serializers
from .models import AsaasPayment, AsaasWebhookLog
from sales.serializers import SaleSerializer


class AsaasPaymentSerializer(serializers.ModelSerializer):
    sale = SaleSerializer(read_only=True)
    sale_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AsaasPayment
        fields = [
            'id', 'sale', 'sale_id', 'asaas_id', 'asaas_customer_id',
            'payment_type', 'status', 'value', 'due_date', 'payment_date',
            'description', 'customer_name', 'customer_email', 'customer_cpf_cnpj',
            'pix_qr_code', 'pix_code', 'bank_slip_url', 'webhook_received',
            'last_webhook_update', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'asaas_id', 'asaas_customer_id', 'status',
            'payment_date', 'webhook_received', 'last_webhook_update',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        sale_id = validated_data.pop('sale_id')
        from sales.models import Sale
        sale = Sale.objects.get(id=sale_id)
        validated_data['sale'] = sale
        return super().create(validated_data)


class AsaasWebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsaasWebhookLog
        fields = [
            'id', 'webhook_id', 'event_type', 'payment_id',
            'raw_data', 'processed', 'processed_at', 'error_message',
            'received_at'
        ]
        read_only_fields = [
            'id', 'webhook_id', 'event_type', 'payment_id',
            'raw_data', 'received_at'
        ]


class CreatePaymentRequestSerializer(serializers.Serializer):
    sale_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=[
        ('pix', 'PIX'),
        ('credit_card', 'Cartão de Crédito'),
        ('bank_slip', 'Boleto'),
        ('bank_slip_installments', 'Boleto Parcelado'),
    ])
    cpf_cnpj = serializers.CharField(max_length=20, required=False, allow_blank=True)
    installment_count = serializers.IntegerField(required=False, min_value=2, max_value=48)
    
    def validate_sale_id(self, value):
        from sales.models import Sale
        try:
            Sale.objects.get(id=value)
        except Sale.DoesNotExist:
            raise serializers.ValidationError("Venda não encontrada")
        return value


class PaymentStatusResponseSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    status = serializers.CharField()
    payment_type = serializers.CharField()
    value = serializers.DecimalField(max_digits=10, decimal_places=2)
    due_date = serializers.DateField()
    payment_date = serializers.DateTimeField(allow_null=True)
    pix_qr_code = serializers.CharField(allow_blank=True)
    pix_code = serializers.CharField(allow_blank=True)
    bank_slip_url = serializers.URLField(allow_blank=True)
    is_paid = serializers.BooleanField()
    is_overdue = serializers.BooleanField()
    is_pending = serializers.BooleanField()


class WebhookDataSerializer(serializers.Serializer):
    id = serializers.CharField()
    event = serializers.CharField()
    payment = serializers.DictField()
    
    def validate_event(self, value):
        valid_events = [
            'PAYMENT_RECEIVED', 'PAYMENT_OVERDUE', 'PAYMENT_DELETED',
            'PAYMENT_UPDATED', 'PAYMENT_CONFIRMED'
        ]
        if value not in valid_events:
            raise serializers.ValidationError(f"Evento inválido: {value}")
        return value
