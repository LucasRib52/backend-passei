from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from courses.models import Course

class CourseReview(models.Model):
    """Modelo para avaliações dos clientes nos cursos"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', verbose_name='Curso')
    user_name = models.CharField(max_length=200, verbose_name='Nome do Cliente', help_text="Nome do cliente")
    user_email = models.EmailField(verbose_name='Email do Cliente', help_text="Email do cliente")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Avaliação',
        help_text="Avaliação de 1 a 5 estrelas"
    )
    title = models.CharField(max_length=200, verbose_name='Título da Avaliação', help_text="Título da avaliação")
    comment = models.TextField(verbose_name='Comentário', help_text="Comentário detalhado")
    is_approved = models.BooleanField(default=False, verbose_name='Aprovado', help_text="Avaliação aprovada para exibição")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Avaliação de Curso"
        verbose_name_plural = "Avaliações de Cursos"

    def __str__(self):
        return f"{self.user_name} - {self.course.title} ({self.rating}★)"

    def get_rating_display(self):
        """Retorna a representação visual da avaliação"""
        return "★" * self.rating + "☆" * (5 - self.rating)

    @property
    def rating_stars(self):
        """Retorna as estrelas para exibição no frontend"""
        return {
            'filled': self.rating,
            'empty': 5 - self.rating,
            'total': 5
        }
