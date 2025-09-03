from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class DashboardMetric(models.Model):
    """
    Métricas do dashboard para análise de performance
    """
    METRIC_TYPE_CHOICES = [
        ('sales', 'Vendas'),
        ('revenue', 'Receita'),
        ('students', 'Alunos'),
        ('courses', 'Cursos'),
        ('conversion', 'Taxa de Conversão'),
    ]
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES, verbose_name='Tipo de Métrica')
    value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor')
    date = models.DateField(verbose_name='Data')
    period = models.CharField(max_length=20, default='daily', verbose_name='Período')  # daily, weekly, monthly
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        verbose_name = 'Métrica do Dashboard'
        verbose_name_plural = 'Métricas do Dashboard'
        ordering = ['-date', '-created_at']
        unique_together = ['metric_type', 'date', 'period']
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.date}"


class StudentActivity(models.Model):
    """
    Atividade dos alunos para tracking de engajamento
    """
    email = models.EmailField(verbose_name='Email do Aluno')
    student_name = models.CharField(max_length=200, verbose_name='Nome do Aluno')
    course_title = models.CharField(max_length=200, verbose_name='Título do Curso')
    last_access = models.DateTimeField(verbose_name='Último Acesso')
    access_count = models.IntegerField(default=1, verbose_name='Contador de Acessos')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Atividade do Aluno'
        verbose_name_plural = 'Atividades dos Alunos'
        ordering = ['-last_access']
    
    def __str__(self):
        return f"{self.student_name} - {self.course_title}"


class CoursePerformance(models.Model):
    """
    Performance dos cursos para análise de vendas
    """
    course_title = models.CharField(max_length=200, verbose_name='Título do Curso')
    total_sales = models.IntegerField(default=0, verbose_name='Total de Vendas')
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Receita Total')
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Taxa de Conversão (%)')
    last_sale_date = models.DateTimeField(null=True, blank=True, verbose_name='Data da Última Venda')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Performance do Curso'
        verbose_name_plural = 'Performance dos Cursos'
        ordering = ['-total_revenue']
    
    def __str__(self):
        return f"{self.course_title} - R$ {self.total_revenue}"
