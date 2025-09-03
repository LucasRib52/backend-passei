from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import News
from .serializers import NewsSerializer, NewsListSerializer, NewsDetailSerializer


# Views Públicas (API)
class NewsListView(generics.ListAPIView):
    """
    Lista notícias publicadas
    """
    queryset = News.objects.filter(status='published')
    serializer_class = NewsListSerializer
    permission_classes = [AllowAny]  # Acesso público
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'urgent']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['date', 'created_at', 'urgent']
    ordering = ['-date', '-created_at']


class NewsDetailView(generics.RetrieveAPIView):
    """
    Detalhes de uma notícia específica
    """
    queryset = News.objects.filter(status='published')
    serializer_class = NewsDetailSerializer
    permission_classes = [AllowAny]  # Acesso público
    lookup_field = 'id'


# Views de Administração (API para /admin do frontend)
class AdminNewsViewSet(generics.ListCreateAPIView):
    """
    CRUD completo de notícias para o painel admin
    """
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'category', 'urgent']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['date', 'created_at', 'urgent']
    ordering = ['-date', '-created_at']


class AdminNewsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalhes, atualização e exclusão de notícia para o painel admin
    """
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
