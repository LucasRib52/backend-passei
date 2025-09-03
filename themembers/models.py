from django.db import models
from django.utils import timezone


class TheMembersProduct(models.Model):
    """
    Modelo para rastrear produtos sincronizados com TheMembers
    """
    product_id = models.CharField(max_length=100, unique=True, verbose_name='ID do Produto TheMembers')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    image_url = models.URLField(blank=True, null=True, verbose_name='URL da Imagem')
    status = models.CharField(max_length=20, default='active', verbose_name='Status')
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    last_sync = models.DateTimeField(blank=True, null=True, verbose_name='Última Sincronização')
    
    class Meta:
        verbose_name = 'Produto TheMembers'
        verbose_name_plural = 'Produtos TheMembers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (ID: {self.product_id})"


class TheMembersIntegration(models.Model):
    """
    Modelo para rastrear integrações entre cursos e produtos TheMembers
    """
    INTEGRATION_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('active', 'Ativa'),
        ('failed', 'Falhou'),
        ('disabled', 'Desabilitada'),
    ]
    
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, verbose_name='Curso')
    product = models.ForeignKey(TheMembersProduct, on_delete=models.CASCADE, verbose_name='Produto TheMembers')
    status = models.CharField(max_length=20, choices=INTEGRATION_STATUS_CHOICES, default='pending', verbose_name='Status')
    
    # Metadados da integração
    integration_date = models.DateTimeField(auto_now_add=True, verbose_name='Data da Integração')
    last_sync = models.DateTimeField(blank=True, null=True, verbose_name='Última Sincronização')
    sync_errors = models.TextField(blank=True, null=True, verbose_name='Erros de Sincronização')
    
    class Meta:
        verbose_name = 'Integração TheMembers'
        verbose_name_plural = 'Integrações TheMembers'
        unique_together = ['course', 'product']
        ordering = ['-integration_date']
    
    def __str__(self):
        return f"{self.course.title} ↔ {self.product.title}"


class TheMembersWebhookLog(models.Model):
    """
    Modelo para rastrear webhooks recebidos da TheMembers
    """
    WEBHOOK_TYPES = [
        ('subscription_created', 'Assinatura Criada'),
        ('subscription_cancelled', 'Assinatura Cancelada'),
        ('payment_confirmed', 'Pagamento Confirmado'),
        ('user_created', 'Usuário Criado'),
        ('other', 'Outro'),
    ]
    
    webhook_type = models.CharField(max_length=50, choices=WEBHOOK_TYPES, verbose_name='Tipo do Webhook')
    payload = models.JSONField(verbose_name='Payload do Webhook')
    headers = models.JSONField(blank=True, null=True, verbose_name='Headers do Webhook')
    
    # Status do processamento
    processed = models.BooleanField(default=False, verbose_name='Processado')
    processing_errors = models.TextField(blank=True, null=True, verbose_name='Erros de Processamento')
    
    # Metadados
    received_at = models.DateTimeField(auto_now_add=True, verbose_name='Recebido em')
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name='Processado em')
    
    class Meta:
        verbose_name = 'Log de Webhook TheMembers'
        verbose_name_plural = 'Logs de Webhook TheMembers'
        ordering = ['-received_at']
    
    def __str__(self):
        return f"{self.webhook_type} - {self.received_at}"


class TheMembersSyncLog(models.Model):
    """
    Modelo para rastrear logs de sincronização
    """
    SYNC_TYPES = [
        ('products', 'Produtos'),
        ('users', 'Usuários'),
        ('subscriptions', 'Assinaturas'),
        ('full', 'Sincronização Completa'),
    ]
    
    SYNC_STATUS_CHOICES = [
        ('success', 'Sucesso'),
        ('partial', 'Parcial'),
        ('failed', 'Falhou'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES, verbose_name='Tipo de Sincronização')
    status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, verbose_name='Status')
    
    # Detalhes da sincronização
    items_processed = models.IntegerField(default=0, verbose_name='Itens Processados')
    items_success = models.IntegerField(default=0, verbose_name='Itens com Sucesso')
    items_failed = models.IntegerField(default=0, verbose_name='Itens com Falha')
    
    # Metadados
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Iniciado em')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='Concluído em')
    duration_seconds = models.FloatField(blank=True, null=True, verbose_name='Duração (segundos)')
    
    # Logs detalhados
    details = models.TextField(blank=True, null=True, verbose_name='Detalhes da Sincronização')
    errors = models.TextField(blank=True, null=True, verbose_name='Erros Encontrados')
    
    class Meta:
        verbose_name = 'Log de Sincronização TheMembers'
        verbose_name_plural = 'Logs de Sincronização TheMembers'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.sync_type} - {self.status} - {self.started_at}"
