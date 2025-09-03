from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TheMembersProduct, 
    TheMembersIntegration, 
    TheMembersWebhookLog, 
    TheMembersSyncLog
)


@admin.register(TheMembersProduct)
class TheMembersProductAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'product_id', 
        'price', 
        'status', 
        'last_sync', 
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'last_sync']
    search_fields = ['title', 'product_id', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_sync']
    
    fieldsets = (
        ('Informações do Produto', {
            'fields': ('product_id', 'title', 'description', 'price', 'image_url', 'status')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def has_add_permission(self, request):
        # Produtos são criados via sincronização, não manualmente
        return False


@admin.register(TheMembersIntegration)
class TheMembersIntegrationAdmin(admin.ModelAdmin):
    list_display = [
        'course_title', 
        'product_title', 
        'status', 
        'integration_date', 
        'last_sync'
    ]
    list_filter = ['status', 'integration_date', 'last_sync']
    search_fields = ['course__title', 'product__title']
    readonly_fields = ['integration_date', 'last_sync']
    
    fieldsets = (
        ('Integração', {
            'fields': ('course', 'product', 'status')
        }),
        ('Sincronização', {
            'fields': ('integration_date', 'last_sync', 'sync_errors'),
            'classes': ('collapse',)
        }),
    )
    
    def course_title(self, obj):
        if obj.course:
            url = reverse('admin:courses_course_change', args=[obj.course.id])
            return format_html('<a href="{}">{}</a>', url, obj.course.title)
        return '-'
    course_title.short_description = 'Curso'
    course_title.admin_order_field = 'course__title'
    
    def product_title(self, obj):
        if obj.product:
            return obj.product.title
        return '-'
    product_title.short_description = 'Produto TheMembers'
    product_title.admin_order_field = 'product__title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course', 'product')


@admin.register(TheMembersWebhookLog)
class TheMembersWebhookLogAdmin(admin.ModelAdmin):
    list_display = [
        'webhook_type', 
        'processed', 
        'received_at', 
        'processed_at'
    ]
    list_filter = ['webhook_type', 'processed', 'received_at']
    search_fields = ['webhook_type', 'payload']
    readonly_fields = ['received_at', 'processed_at']
    
    fieldsets = (
        ('Webhook', {
            'fields': ('webhook_type', 'processed')
        }),
        ('Dados', {
            'fields': ('payload', 'headers'),
            'classes': ('collapse',)
        }),
        ('Processamento', {
            'fields': ('received_at', 'processed_at', 'processing_errors'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Webhooks são criados automaticamente, não manualmente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Permite apenas marcar como processado
        return True


@admin.register(TheMembersSyncLog)
class TheMembersSyncLogAdmin(admin.ModelAdmin):
    list_display = [
        'sync_type', 
        'status', 
        'items_processed', 
        'items_success', 
        'items_failed', 
        'started_at', 
        'duration_display'
    ]
    list_filter = ['sync_type', 'status', 'started_at']
    search_fields = ['sync_type', 'details', 'errors']
    readonly_fields = ['started_at', 'completed_at', 'duration_seconds']
    
    fieldsets = (
        ('Sincronização', {
            'fields': ('sync_type', 'status')
        }),
        ('Resultados', {
            'fields': ('items_processed', 'items_success', 'items_failed')
        }),
        ('Tempo', {
            'fields': ('started_at', 'completed_at', 'duration_seconds'),
            'classes': ('collapse',)
        }),
        ('Detalhes', {
            'fields': ('details', 'errors'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_display(self, obj):
        if obj.duration_seconds:
            return f"{obj.duration_seconds:.2f}s"
        return '-'
    duration_display.short_description = 'Duração'
    
    def has_add_permission(self, request):
        # Logs são criados automaticamente, não manualmente
        return False


# Customização do admin de cursos para incluir campos TheMembers
try:
    from courses.admin import CourseAdmin
    from courses.models import Course
    
    # Verifica se CourseAdmin existe e tem os atributos necessários
    if hasattr(CourseAdmin, 'fieldsets') and CourseAdmin.fieldsets:
        # Adiciona campos TheMembers ao admin de cursos
        CourseAdmin.fieldsets += (
            ('Integração TheMembers', {
                'fields': ('themembers_product_id', 'themembers_link'),
                'classes': ('collapse',)
            }),
        )
    
    if hasattr(CourseAdmin, 'list_filter') and CourseAdmin.list_filter:
        # Adiciona filtros para campos TheMembers
        CourseAdmin.list_filter += ('themembers_product_id',)
    
    if hasattr(CourseAdmin, 'search_fields') and CourseAdmin.search_fields:
        # Adiciona campos de busca
        CourseAdmin.search_fields += ('themembers_product_id',)
    
    if hasattr(CourseAdmin, 'list_display') and CourseAdmin.list_display:
        # Adiciona campos na listagem
        CourseAdmin.list_display += ('themembers_product_id', 'themembers_link_display')
    
    def themembers_link_display(self, obj):
        if obj.themembers_link:
            return format_html('<a href="{}" target="_blank">🔗 Acessar</a>', obj.themembers_link)
        return '-'
    themembers_link_display.short_description = 'Link TheMembers'
    themembers_link_display.admin_order_field = 'themembers_link'
    
    CourseAdmin.themembers_link_display = themembers_link_display
    
except ImportError:
    # Se não conseguir importar, ignora silenciosamente
    pass
