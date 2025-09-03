from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Professor
from .serializers import ProfessorSerializer, ProfessorListSerializer, ProfessorDetailSerializer


# Create your views here.

# Views Públicas (API)
class ProfessorListView(generics.ListAPIView):
    """
    Lista todos os professores
    """
    queryset = Professor.objects.all()
    serializer_class = ProfessorDetailSerializer  # Mudança: usar DetailSerializer para retornar todos os campos
    permission_classes = [AllowAny]  # Acesso público
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'specialties']
    ordering_fields = ['name', 'rating', 'approvals_count']
    ordering = ['name']


class ProfessorDetailView(generics.RetrieveAPIView):
    """
    Detalhes de um professor específico
    """
    queryset = Professor.objects.all()
    serializer_class = ProfessorDetailSerializer
    permission_classes = [AllowAny]  # Acesso público
    lookup_field = 'id'


# Views de Administração (API para /admin do frontend)
class AdminProfessorViewSet(generics.ListCreateAPIView):
    """
    CRUD completo de professores para o painel admin
    """
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'specialties']
    ordering_fields = ['name', 'rating', 'created_at']
    ordering = ['name']


class AdminProfessorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalhes, atualização e exclusão de professor para o painel admin
    """
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
