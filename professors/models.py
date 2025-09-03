from django.db import models


class Professor(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nome')
    bio = models.TextField(verbose_name='Biografia')
    image = models.ImageField(upload_to='professors/', blank=True, null=True, verbose_name='Imagem')
    specialties = models.TextField(verbose_name='Especialidades')
    experience = models.TextField(verbose_name='Experiência')
    
    approvals_count = models.IntegerField(default=0, verbose_name='Número de Aprovações')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name='Avaliação')
    achievements = models.TextField(blank=True, verbose_name='Conquistas')
    
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    linkedin = models.URLField(blank=True, null=True, verbose_name='LinkedIn')
    website = models.URLField(blank=True, null=True, verbose_name='Website')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
        ordering = ['name']
    
    def __str__(self):
        return self.name
