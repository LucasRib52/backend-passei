from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.models import User
from .serializers import UserSerializer, EmailTokenObtainPairSerializer


class AdminAuthView(TokenObtainPairView):
    """
    Login para o painel admin - aceita username ou email
    """
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer


class AdminAuthRefreshView(TokenRefreshView):
    """
    Refresh token para o painel admin
    """
    permission_classes = [AllowAny]


class AdminProfileView(generics.RetrieveUpdateAPIView):
    """
    Perfil do admin logado
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class AdminDashboardView(generics.GenericAPIView):
    """
    Dashboard com estatísticas para o painel admin
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from courses.models import Course
        from sales.models import Sale
        from testimonials.models import Testimonial
        from news.models import News
        
        # Estatísticas básicas
        stats = {
            'total_courses': Course.objects.count(),
            'active_courses': Course.objects.filter(status='active').count(),
            'total_sales': Sale.objects.count(),
            'paid_sales': Sale.objects.filter(status='paid').count(),
            'total_testimonials': Testimonial.objects.count(),
            'approved_testimonials': Testimonial.objects.filter(status='approved').count(),
            'total_news': News.objects.count(),
            'published_news': News.objects.filter(status='published').count(),
        }
        
        return Response(stats)
