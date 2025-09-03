from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Testimonial
from .serializers import TestimonialSerializer, TestimonialListSerializer, TestimonialCreateUpdateSerializer


# Views Públicas (API)
class TestimonialListView(generics.ListAPIView):
    """
    Lista depoimentos aprovados
    """
    queryset = Testimonial.objects.filter(status='approved')
    serializer_class = TestimonialListSerializer
    permission_classes = [AllowAny]  # Acesso público
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'year']
    search_fields = ['name', 'testimonial']
    ordering_fields = ['rating', 'year', 'created_at']
    ordering = ['-created_at']


# Views de Administração (API para /admin do frontend)
class AdminTestimonialViewSet(generics.ListCreateAPIView):
    """
    CRUD completo de depoimentos para o painel admin
    """
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'course', 'year']
    search_fields = ['name', 'testimonial']
    ordering_fields = ['created_at', 'rating', 'year']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TestimonialCreateUpdateSerializer
        return TestimonialSerializer


class AdminTestimonialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalhes, atualização e exclusão de depoimento para o painel admin
    """
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TestimonialCreateUpdateSerializer
        return TestimonialSerializer
