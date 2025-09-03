"""
Comando Django para deploy com sincronização automática
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import os
import sys

class Command(BaseCommand):
    help = 'Executa deploy completo com migrações e sincronização TheMembers'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Pula as migrações e executa apenas sincronização',
        )
        parser.add_argument(
            '--skip-sync',
            action='store_true',
            help='Pula a sincronização e executa apenas migrações',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força execução mesmo em ambiente de desenvolvimento',
        )
    
    def handle(self, *args, **options):
        from django.conf import settings
        
        # Verifica se está em produção ou se force foi especificado
        if settings.DEBUG and not options['force']:
            self.stdout.write(
                self.style.WARNING('⚠️ Executando em modo DEBUG. Use --force para continuar.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando deploy com sincronização automática...')
        )
        
        start_time = timezone.now()
        
        try:
            # PASSO 1: Executar migrações
            if not options['skip_migrations']:
                self.stdout.write('📦 Executando migrações...')
                call_command('migrate', verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✅ Migrações concluídas')
                )
            else:
                self.stdout.write('⏭️ Pulando migrações...')
            
            # PASSO 2: Coletar arquivos estáticos
            self.stdout.write('📁 Coletando arquivos estáticos...')
            call_command('collectstatic', '--noinput', verbosity=1)
            self.stdout.write(
                self.style.SUCCESS('✅ Arquivos estáticos coletados')
            )
            
            # PASSO 3: Sincronizar produtos TheMembers
            if not options['skip_sync']:
                self.stdout.write('🔄 Sincronizando produtos TheMembers...')
                call_command('sync_themembers_products', '--silent', verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✅ Sincronização TheMembers concluída')
                )
            else:
                self.stdout.write('⏭️ Pulando sincronização...')
            
            # PASSO 4: Verificar integridade
            self.stdout.write('🔍 Verificando integridade do sistema...')
            call_command('check', verbosity=1)
            self.stdout.write(
                self.style.SUCCESS('✅ Verificação de integridade concluída')
            )
            
            # Resumo final
            end_time = timezone.now()
            duration = end_time - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 Deploy concluído com sucesso em {duration.total_seconds():.1f} segundos!'
                )
            )
            
            # Informações adicionais
            self.stdout.write('\n📊 Informações do sistema:')
            self.stdout.write(f'   • Ambiente: {"Produção" if not settings.DEBUG else "Desenvolvimento"}')
            self.stdout.write(f'   • Tempo total: {duration.total_seconds():.1f}s')
            self.stdout.write(f'   • Data/Hora: {end_time.strftime("%d/%m/%Y %H:%M:%S")}')
            
            if not options['skip_sync']:
                # Mostrar produtos sincronizados
                try:
                    from themembers.models import TheMembersProduct
                    product_count = TheMembersProduct.objects.count()
                    self.stdout.write(f'   • Produtos TheMembers: {product_count}')
                except Exception:
                    pass
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro durante deploy: {str(e)}')
            )
            sys.exit(1)
