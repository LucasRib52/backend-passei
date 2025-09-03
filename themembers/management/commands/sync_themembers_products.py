"""
Comando Django para sincronizar produtos TheMembers
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from themembers.services import CourseSyncService
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza produtos da plataforma TheMembers com o banco local'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força sincronização mesmo se houver erros',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe informações detalhadas',
        )
        parser.add_argument(
            '--silent',
            action='store_true',
            help='Executa silenciosamente (para cron jobs)',
        )
        parser.add_argument(
            '--log-file',
            type=str,
            help='Arquivo de log para salvar resultados',
        )
    
    def handle(self, *args, **options):
        start_time = timezone.now()
        
        # Configurar logging se especificado
        if options['log_file']:
            logging.basicConfig(
                filename=options['log_file'],
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        
        if not options['silent']:
            self.stdout.write(
                self.style.SUCCESS('🚀 Iniciando sincronização de produtos TheMembers...')
            )
        
        try:
            # Inicializa serviço de sincronização
            sync_service = CourseSyncService()
            
            # Executa sincronização
            result = sync_service.sync_all_products()
            
            if result['success']:
                # Sincronização bem-sucedida
                success_message = (
                    f"✅ Sincronização concluída com sucesso!\n"
                    f"   📊 Total processado: {result['total_processed']}\n"
                    f"   ➕ Produtos criados: {result['created']}\n"
                    f"   🔄 Produtos atualizados: {result['updated']}\n"
                    f"   ❌ Erros: {result['errors']}"
                )
                
                if not options['silent']:
                    self.stdout.write(self.style.SUCCESS(success_message))
                
                # Log para arquivo se especificado
                if options['log_file']:
                    logger.info(f"Sincronização TheMembers: {result['total_processed']} processados, "
                              f"{result['created']} criados, {result['updated']} atualizados, {result['errors']} erros")
                
                if options['verbose'] and not options['silent']:
                    # Exibe produtos disponíveis
                    products = sync_service.get_available_products()
                    self.stdout.write(
                        self.style.WARNING(f"\n📋 Produtos disponíveis ({products.count()}):")
                    )
                    
                    for product in products:
                        self.stdout.write(
                            f"   • {product.title} (ID: {product.product_id}) - R$ {product.price}"
                        )
                
            else:
                # Sincronização falhou
                error_message = f"❌ Falha na sincronização: {result.get('error', 'Erro desconhecido')}"
                
                if not options['silent']:
                    self.stdout.write(self.style.ERROR(error_message))
                
                if options['log_file']:
                    logger.error(f"Falha na sincronização TheMembers: {result.get('error', 'Erro desconhecido')}")
                
                if not options['force']:
                    return
                
        except Exception as e:
            error_message = f"❌ Erro crítico na sincronização: {str(e)}"
            
            if not options['silent']:
                self.stdout.write(self.style.ERROR(error_message))
            
            if options['log_file']:
                logger.error(f"Erro crítico na sincronização TheMembers: {str(e)}")
            
            if not options['force']:
                return
        
        # Calcula duração
        duration = timezone.now() - start_time
        
        if not options['silent']:
            self.stdout.write(
                self.style.SUCCESS(f"\n⏱️  Sincronização concluída em {duration.total_seconds():.2f} segundos")
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    "\n💡 Dica: Use este comando regularmente para manter os produtos sincronizados.\n"
                    "   Para forçar sincronização mesmo com erros: python manage.py sync_themembers_products --force\n"
                    "   Para informações detalhadas: python manage.py sync_themembers_products --verbose\n"
                    "   Para execução silenciosa (cron): python manage.py sync_themembers_products --silent\n"
                    "   Para salvar logs: python manage.py sync_themembers_products --log-file /path/to/log.txt"
                )
            )
