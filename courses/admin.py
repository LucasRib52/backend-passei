from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html
from .models import Course, Module, Lesson, Category
from themembers.services import CourseSyncService

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'professor', 'category', 'price', 'status', 'themembers_status', 'created_at']
    list_filter = ['status', 'category', 'professor', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    
    fields = (
        'title', 'description', 'detailed_description', 'content',
        'professor', 'category', 'price', 'original_price', 'duration',
        'benefits', 'requirements', 'course_image', 'course_video', 'video_url', 'whatsapp_group_link',
        'themembers_link', 'themembers_product_id', 'asaas_product_id',
        # Pagamentos
        'allow_pix', 'allow_credit_card', 'allow_bank_slip', 'allow_boleto_installments', 'max_boleto_installments',
        'status', 'is_bestseller', 'is_complete', 'is_new', 'is_featured',
        'professors', 'categories'
    )
    
    readonly_fields = ('created_at', 'updated_at', 'students_count', 'rating', 'reviews_count')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'sync-themembers/',
                self.admin_site.admin_view(self.sync_themembers_view),
                name='courses_course_sync_themembers',
            ),
        ]
        return custom_urls + urls
    
    def themembers_status(self, obj):
        """Mostra status da integração TheMembers"""
        if obj.themembers_product_id:
            return format_html(
                '<span style="color: green;">✅ Vinculado</span><br>'
                '<small>ID: {}</small>',
                obj.themembers_product_id
            )
        else:
            return format_html(
                '<span style="color: orange;">⚠️ Não vinculado</span>'
            )
    themembers_status.short_description = 'TheMembers'
    
    def sync_themembers_view(self, request):
        """Executa sincronização TheMembers"""
        try:
            sync_service = CourseSyncService()
            result = sync_service.sync_all_products()
            
            if result['success']:
                messages.success(
                    request,
                    f"✅ Sincronização TheMembers concluída! "
                    f"{result['total_processed']} produtos processados "
                    f"({result['created']} novos, {result['updated']} atualizados)"
                )
            else:
                messages.error(
                    request,
                    f"❌ Erro na sincronização: {result.get('error', 'Erro desconhecido')}"
                )
        except Exception as e:
            messages.error(request, f"❌ Erro na sincronização: {str(e)}")
        
        return redirect('admin:courses_course_changelist')
    
    def changelist_view(self, request, extra_context=None):
        """Adiciona botão de sincronização na listagem"""
        extra_context = extra_context or {}
        extra_context['show_sync_button'] = True
        return super().changelist_view(request, extra_context)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'lessons_count', 'duration', 'order']
    list_filter = ['course', 'order']
    search_fields = ['title', 'description']
    ordering = ['course', 'order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'duration', 'is_free', 'order']
    list_filter = ['module', 'is_free', 'order']
    search_fields = ['title', 'description']
    ordering = ['module', 'order']
