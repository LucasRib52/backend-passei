from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import CourseReview
from .serializers import (
    CourseReviewSerializer, 
    CourseReviewCreateSerializer, 
    CourseReviewAdminSerializer
)
from django.db import models

# Create your views here.

class CourseReviewListCreateView(generics.ListCreateAPIView):
    """View para listar e criar avaliações de um curso específico"""
    serializer_class = CourseReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'rating', 'is_approved']
    
    def get_queryset(self):
        """Retorna apenas avaliações aprovadas para visualização pública"""
        return CourseReview.objects.filter(is_approved=True)
    
    def get_serializer_class(self):
        """Retorna serializer diferente para criação e listagem"""
        if self.request.method == 'POST':
            return CourseReviewCreateSerializer
        return CourseReviewSerializer
    
    def create(self, request, *args, **kwargs):
        """Cria uma nova avaliação"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Avaliação enviada com sucesso! Ela será revisada antes de ser publicada.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View para visualizar, editar e excluir uma avaliação específica"""
    queryset = CourseReview.objects.all()
    serializer_class = CourseReviewSerializer
    permission_classes = [AllowAny]

class CourseReviewAdminListView(generics.ListAPIView):
    """View para administradores listarem todas as avaliações"""
    queryset = CourseReview.objects.all()
    serializer_class = CourseReviewAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'rating', 'is_approved', 'created_at']
    search_fields = ['user_name', 'user_email', 'title', 'comment', 'course__title']
    ordering_fields = ['created_at', 'rating', 'user_name']
    ordering = ['-created_at']

class CourseReviewAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View para administradores gerenciarem avaliações específicas"""
    queryset = CourseReview.objects.all()
    serializer_class = CourseReviewAdminSerializer
    permission_classes = [IsAdminUser]

class CourseReviewStatsView(generics.ListAPIView):
    """View para estatísticas das avaliações de um curso"""
    serializer_class = CourseReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Retorna avaliações aprovadas de um curso específico"""
        course_id = self.kwargs.get('course_id')
        return CourseReview.objects.filter(course_id=course_id, is_approved=True)
    
    def list(self, request, *args, **kwargs):
        """Retorna estatísticas das avaliações"""
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'reviews': []
            })
        
        # Estatísticas gerais
        total_reviews = queryset.count()
        average_rating = round(queryset.aggregate(
            models.Avg('rating')
        )['rating__avg'], 1)
        
        # Distribuição das avaliações
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[f'{i}_star'] = queryset.filter(rating=i).count()
        
        # Serializa as avaliações
        reviews_serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'total_reviews': total_reviews,
            'average_rating': average_rating,
            'rating_distribution': rating_distribution,
            'reviews': reviews_serializer.data
        })
