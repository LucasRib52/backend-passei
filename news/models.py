from django.db import models


class News(models.Model):
    STATUS_CHOICES = [
        ('published', 'Publicado'),
        ('draft', 'Rascunho'),
        ('archived', 'Arquivado'),
    ]
    
    CATEGORY_CHOICES = [
        ('edital', 'Edital'),
        ('noticia', 'Notícia'),
        ('dica', 'Dica'),
        ('evento', 'Evento'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Título')
    excerpt = models.TextField(verbose_name='Resumo')
    content = models.TextField(blank=True, null=True, verbose_name='Conteúdo')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Categoria')
    
    date = models.DateField(verbose_name='Data')
    read_time = models.IntegerField(verbose_name='Tempo de Leitura (minutos)')
    source = models.CharField(max_length=200, blank=True, verbose_name='Fonte')
    link = models.TextField(blank=True, null=True, verbose_name='Link')
    
    urgent = models.BooleanField(default=False, verbose_name='Urgente')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Status')
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name='Imagem')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Notícia'
        verbose_name_plural = 'Notícias'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return self.title
