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
    # Preserva vendas quando o curso é excluído
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Curso')
    # Snapshot do título do curso para manter referência mesmo após exclusão
    course_title_snapshot = models.CharField(max_length=200, blank=True, null=True, verbose_name='Título do Curso (snapshot)')
    
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
        course_title = None
        if getattr(self, 'course', None):
            course_title = getattr(self.course, 'title', None)
        if not course_title:
            course_title = self.course_title_snapshot or 'Curso removido'
        return f"{self.student_name} - {course_title}"
    
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

    def save(self, *args, **kwargs):
        # Garante snapshot do título do curso
        if self.course and not self.course_title_snapshot:
            self.course_title_snapshot = self.course.title
        super().save(*args, **kwargs)
