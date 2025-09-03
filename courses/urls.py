from django.urls import path
from . import views
from .views import AdminModuleListCreateView, AdminModuleDetailView

app_name = 'courses'

urlpatterns = [
    # URLs Públicas
    path('', views.CourseListView.as_view(), name='course-list'),
    path('<int:id>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('<int:course_id>/modules/', views.ModuleListView.as_view(), name='module-list'),
    path('modules/<int:id>/', views.ModuleDetailView.as_view(), name='module-detail'),
    path('modules/<int:module_id>/lessons/', views.LessonListView.as_view(), name='lesson-list'),
    path('lessons/<int:id>/', views.LessonDetailView.as_view(), name='lesson-detail'),
    
    # URLs de Administração
    path('admin/', views.AdminCourseViewSet.as_view(), name='admin-course-list'),
    path('admin/<int:id>/', views.AdminCourseDetailView.as_view(), name='admin-course-detail'),
    # URLs de Administração módulos
    path('admin/<int:course_id>/modules/', AdminModuleListCreateView.as_view(), name='admin-module-list'),
    path('admin/modules/<int:id>/', AdminModuleDetailView.as_view(), name='admin-module-detail'),
] 