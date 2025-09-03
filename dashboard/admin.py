from django.contrib import admin
from .models import DashboardMetric, StudentActivity, CoursePerformance


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'date', 'period', 'created_at']
    list_filter = ['metric_type', 'period', 'date']
    search_fields = ['metric_type']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('metric_type', 'value', 'date', 'period')
        }),
        ('Metadados', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentActivity)
class StudentActivityAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'email', 'course_title', 'last_access', 'access_count', 'created_at']
    list_filter = ['course_title', 'last_access', 'created_at']
    search_fields = ['student_name', 'email', 'course_title']
    ordering = ['-last_access']
    date_hierarchy = 'last_access'
    
    fieldsets = (
        ('Informações do Aluno', {
            'fields': ('student_name', 'email', 'course_title')
        }),
        ('Atividade', {
            'fields': ('last_access', 'access_count')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CoursePerformance)
class CoursePerformanceAdmin(admin.ModelAdmin):
    list_display = ['course_title', 'total_sales', 'total_revenue', 'conversion_rate', 'last_sale_date', 'updated_at']
    list_filter = ['last_sale_date', 'updated_at']
    search_fields = ['course_title']
    ordering = ['-total_revenue']
    date_hierarchy = 'last_sale_date'
    
    fieldsets = (
        ('Informações do Curso', {
            'fields': ('course_title',)
        }),
        ('Performance', {
            'fields': ('total_sales', 'total_revenue', 'conversion_rate')
        }),
        ('Última Atividade', {
            'fields': ('last_sale_date',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
