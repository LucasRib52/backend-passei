from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    # URLs Públicas para Categorias
    path('', views.CategoryListView.as_view(), name='category-list'),
    
    # URLs de Administração para Categorias
    path('admin/', views.AdminCategoryViewSet.as_view(), name='admin-category-list'),
    path('admin/<int:id>/', views.AdminCategoryDetailView.as_view(), name='admin-category-detail'),
] 