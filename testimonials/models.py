from django.db import models
from courses.models import Course


class Testimonial(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Aprovado'),
        ('pending', 'Pendente'),
        ('rejected', 'Rejeitado'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nome')
    position = models.CharField(max_length=200, verbose_name='Cargo')
    location = models.CharField(max_length=200, verbose_name='Localização')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Curso')
    
    result = models.CharField(max_length=200, verbose_name='Resultado')
    rating = models.IntegerField(verbose_name='Avaliação')
    testimonial = models.TextField(verbose_name='Depoimento')
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True, verbose_name='Imagem')
    
    # Vídeo do depoimento
    video = models.FileField(upload_to='testimonials/videos/', blank=True, null=True, verbose_name='Vídeo do Depoimento', help_text='Vídeo do depoimento')
    
    # URL do vídeo (alternativa para vídeos externos)
    video_url = models.URLField(blank=True, null=True, verbose_name='URL do Vídeo', help_text='URL do YouTube, Vimeo ou outro serviço')
    
    year = models.IntegerField(verbose_name='Ano')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Depoimento'
        verbose_name_plural = 'Depoimentos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.course.title}"
