from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # URLs Públicas
    path('', views.NewsListView.as_view(), name='news-list'),
    path('<int:id>/', views.NewsDetailView.as_view(), name='news-detail'),
    
    # URLs de Administração
    path('admin/', views.AdminNewsViewSet.as_view(), name='admin-news-list'),
    path('admin/<int:id>/', views.AdminNewsDetailView.as_view(), name='admin-news-detail'),
] 