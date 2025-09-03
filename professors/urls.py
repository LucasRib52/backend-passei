from django.urls import path
from . import views

app_name = 'professors'

urlpatterns = [
    # URLs Públicas
    path('', views.ProfessorListView.as_view(), name='professor-list'),
    path('<int:id>/', views.ProfessorDetailView.as_view(), name='professor-detail'),
    
    # URLs de Administração
    path('admin/', views.AdminProfessorViewSet.as_view(), name='admin-professor-list'),
    path('admin/<int:id>/', views.AdminProfessorDetailView.as_view(), name='admin-professor-detail'),
] 