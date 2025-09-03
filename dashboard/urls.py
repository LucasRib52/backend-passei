from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard principal
    path('overview/', views.DashboardOverviewView.as_view(), name='overview'),
    
    # Vendas recentes
    path('recent-sales/', views.RecentSalesView.as_view(), name='recent-sales'),
    
    # Cursos mais vendidos
    path('top-courses/', views.TopCoursesView.as_view(), name='top-courses'),
    
    # Métricas do dashboard
    path('metrics/', views.DashboardMetricsView.as_view(), name='metrics'),
    
    # Tracking de atividade dos alunos
    path('track-activity/', views.track_student_activity, name='track-activity'),
    
    # Comparação entre períodos
    path('period-comparison/', views.get_period_comparison, name='period-comparison'),
]
