"""
Tarefas Celery para sincronização automática com TheMembers
"""
from celery import shared_task
from django.utils import timezone
from .services import CourseSyncService
from .models import TheMembersSyncLog
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def sync_themembers_products_task(self):
    """
    Tarefa Celery para sincronizar produtos TheMembers
    """
    try:
        logger.info("Iniciando sincronização automática de produtos TheMembers")
        
        # Inicializa serviço de sincronização
        sync_service = CourseSyncService()
        
        # Executa sincronização
        result = sync_service.sync_all_products()
        
        if result['success']:
            logger.info(f"Sincronização TheMembers concluída: {result['total_processed']} processados, "
                       f"{result['created']} criados, {result['updated']} atualizados")
            
            # Registra log de sucesso
            TheMembersSyncLog.objects.create(
                sync_type='products',
                status='success',
                items_processed=result['total_processed'],
                items_success=result['created'] + result['updated'],
                items_failed=result['errors'],
                completed_at=timezone.now(),
                details=f"Sincronização automática: {result['created']} criados, {result['updated']} atualizados"
            )
            
            return {
                'success': True,
                'message': 'Sincronização concluída com sucesso',
                'data': result
            }
        else:
            logger.error(f"Falha na sincronização TheMembers: {result.get('error', 'Erro desconhecido')}")
            
            # Registra log de falha
            TheMembersSyncLog.objects.create(
                sync_type='products',
                status='failed',
                items_processed=0,
                items_success=0,
                items_failed=1,
                completed_at=timezone.now(),
                errors=result.get('error', 'Erro desconhecido')
            )
            
            # Retry se ainda não excedeu o limite
            if self.request.retries < self.max_retries:
                raise self.retry(countdown=60 * (self.request.retries + 1))  # Retry em 1min, 2min, 3min
            
            return {
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            }
            
    except Exception as e:
        logger.error(f"Erro crítico na sincronização TheMembers: {str(e)}")
        
        # Registra log de erro
        TheMembersSyncLog.objects.create(
            sync_type='products',
            status='failed',
            items_processed=0,
            items_success=0,
            items_failed=1,
            completed_at=timezone.now(),
            errors=str(e)
        )
        
        # Retry se ainda não excedeu o limite
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def check_new_products_task():
    """
    Tarefa para verificar se há novos produtos (executada com menos frequência)
    """
    try:
        logger.info("Verificando novos produtos TheMembers")
        
        sync_service = CourseSyncService()
        result = sync_service.sync_all_products()
        
        if result['success'] and result['created'] > 0:
            logger.info(f"Novos produtos encontrados: {result['created']}")
            # Aqui você pode adicionar notificações (email, webhook, etc.)
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao verificar novos produtos: {str(e)}")
        return {'success': False, 'error': str(e)}
