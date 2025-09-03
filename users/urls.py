from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # URLs de Autenticação
    path('auth/login/', views.AdminAuthView.as_view(), name='admin-login'),
    path('auth/refresh/', views.AdminAuthRefreshView.as_view(), name='admin-refresh'),
    path('auth/profile/', views.AdminProfileView.as_view(), name='admin-profile'),
    path('auth/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
] 