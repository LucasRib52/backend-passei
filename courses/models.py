from django.db import models
from django.contrib.auth.models import User
from professors.models import Professor


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='Slug')
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name='Cor')
    icon = models.CharField(max_length=50, default='BookOpen', verbose_name='Ícone')
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizada em')
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Course(models.Model):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('draft', 'Rascunho'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição')
    detailed_description = models.TextField(blank=True, null=True, verbose_name='Descrição Detalhada')
    content = models.TextField(blank=True, null=True, verbose_name='Conteúdo do Curso')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Original')
    
    # Imagem do curso
    course_image = models.ImageField(upload_to='courses/images/', blank=True, null=True, verbose_name='Imagem do Curso')
    
    # Vídeo do curso (para detalhes)
    course_video = models.FileField(upload_to='courses/videos/', blank=True, null=True, verbose_name='Vídeo do Curso', help_text='Vídeo para mostrar nos detalhes do curso')
    
    # URL do vídeo (alternativa para vídeos externos)
    video_url = models.URLField(blank=True, null=True, verbose_name='URL do Vídeo', help_text='URL do YouTube, Vimeo ou outro serviço')
    
    duration = models.CharField(max_length=50, verbose_name='Duração')
    students_count = models.IntegerField(default=0, verbose_name='Número de Alunos')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name='Avaliação')
    reviews_count = models.IntegerField(default=0, verbose_name='Número de Avaliações')
    
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, verbose_name='Professor')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoria', null=True, blank=True)
    # Novos relacionamentos M2M (mantém os campos principais para compatibilidade)
    professors = models.ManyToManyField(Professor, related_name='courses', blank=True, verbose_name='Professores')
    categories = models.ManyToManyField(Category, related_name='courses', blank=True, verbose_name='Categorias')
    benefits = models.TextField(blank=True, null=True, verbose_name='Benefícios')
    requirements = models.TextField(blank=True, null=True, verbose_name='Requisitos')
    
    # Link do grupo do WhatsApp
    whatsapp_group_link = models.URLField(blank=True, null=True, verbose_name='Link do Grupo WhatsApp', help_text='Link para o grupo do WhatsApp do curso')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    # Integração externa
    themembers_link = models.URLField(blank=True, null=True, verbose_name='Link TheMembers')
    themembers_product_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID Produto TheMembers')
    asaas_product_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID Produto ASAAS')
    
    # Formas de pagamento por curso
    allow_pix = models.BooleanField(default=True, verbose_name='Habilitar PIX')
    allow_credit_card = models.BooleanField(default=True, verbose_name='Habilitar Cartão de Crédito')
    allow_bank_slip = models.BooleanField(default=True, verbose_name='Habilitar Boleto')
    allow_boleto_installments = models.BooleanField(default=False, verbose_name='Habilitar Boleto Parcelado')
    max_boleto_installments = models.IntegerField(default=12, verbose_name='Parcelas máx. no boleto')
    
    # Badges/Tags do curso
    is_bestseller = models.BooleanField(default=False, verbose_name='Mais Vendido')
    is_complete = models.BooleanField(default=False, verbose_name='Completo')
    is_new = models.BooleanField(default=False, verbose_name='Novo')
    is_featured = models.BooleanField(default=False, verbose_name='Destaque')
    
    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

    def get_themembers_product_ids(self):
        """Retorna a lista de product_ids vinculados ao curso (via integrações + legado)."""
        try:
            from themembers.models import TheMembersIntegration
            ids = list(
                TheMembersIntegration.objects.filter(course=self).values_list(
                    'product__product_id', flat=True
                )
            )
        except Exception:
            ids = []
        if not ids and self.themembers_product_id:
            ids = [self.themembers_product_id]
        return ids


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name='Curso')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição')
    lessons_count = models.IntegerField(default=0, verbose_name='Número de Aulas')
    duration = models.CharField(max_length=50, verbose_name='Duração')
    order = models.IntegerField(default=0, verbose_name='Ordem')
    topics = models.TextField(blank=True, verbose_name='Tópicos')
    
    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name='Módulo')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição')
    video_url = models.URLField(verbose_name='URL do Vídeo')
    duration = models.CharField(max_length=50, verbose_name='Duração')
    order = models.IntegerField(default=0, verbose_name='Ordem')
    is_free = models.BooleanField(default=False, verbose_name='É Gratuita')
    
    class Meta:
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
