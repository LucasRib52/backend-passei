from django.db import models
from courses.models import Course


class Sale(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('credit_card', 'Cartão de Crédito'),
        ('bank_slip', 'Boleto'),
        ('bank_slip_installments', 'Boleto Parcelado'),
    ]
    
    student_name = models.CharField(max_length=200, verbose_name='Nome do Aluno')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Telefone')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Curso')
    
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, verbose_name='Método de Pagamento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    
    # Dados pessoais para Asaas
    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name='CPF/CNPJ')
    
    # Endereço para Asaas
    address = models.TextField(blank=True, null=True, verbose_name='Endereço')
    address_number = models.CharField(max_length=10, blank=True, null=True, verbose_name='Número')
    address_complement = models.CharField(max_length=100, blank=True, null=True, verbose_name='Complemento')
    neighborhood = models.CharField(max_length=100, blank=True, null=True, verbose_name='Bairro')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade')
    state = models.CharField(max_length=2, blank=True, null=True, verbose_name='Estado')
    postal_code = models.CharField(max_length=10, blank=True, null=True, verbose_name='CEP')
    
    # Integração externa
    asaas_payment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID Pagamento ASAAS')
    # Parcelamento por boleto
    bank_slip_installment_count = models.IntegerField(blank=True, null=True, verbose_name='Nº de parcelas no boleto')
    bank_slip_installment_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Valor da parcela (boleto)')
    themembers_subscription_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID Assinatura TheMembers')
    themembers_access_granted = models.BooleanField(default=False, verbose_name='Acesso TheMembers Concedido')
    themembers_temp_password = models.CharField(max_length=100, blank=True, null=True, verbose_name='Senha Temporária TheMembers')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student_name} - {self.course.title}"
    
    @property
    def full_address(self):
        """Retorna endereço completo formatado"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.address_number:
            parts.append(self.address_number)
        if self.address_complement:
            parts.append(self.address_complement)
        if self.neighborhood:
            parts.append(self.neighborhood)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        
        return ', '.join(parts) if parts else ''
