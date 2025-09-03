from django.apps import AppConfig


class ThemembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'themembers'

    def ready(self):
        """
        Executa sincronização automática quando o Django inicia
        """
        import os
        from django.conf import settings
        
        # Só executa em produção e se não for um comando de migração
        if (not settings.DEBUG and 
            'runserver' not in os.sys.argv and 
            'migrate' not in os.sys.argv and
            'collectstatic' not in os.sys.argv):
            
            try:
                from .services import CourseSyncService
                from django.utils import timezone
                
                print("🔄 Iniciando sincronização automática de produtos TheMembers...")
                
                sync_service = CourseSyncService()
                result = sync_service.sync_all_products()
                
                if result['success']:
                    print(f"✅ Sincronização automática concluída: {result['total_processed']} produtos processados")
                else:
                    print(f"⚠️ Sincronização automática falhou: {result.get('error', 'Erro desconhecido')}")
                    
            except Exception as e:
                print(f"❌ Erro na sincronização automática: {str(e)}")
                # Não falha a inicialização do Django por causa da sincronização
