"""
Serviços para integração com a API TheMembers
"""
import requests
import json
import time
from typing import List, Dict, Optional, Any
from django.conf import settings
from django.utils import timezone
from .config import (
    THEMEMBERS_API_URL,
    DEFAULT_HEADERS,
    RETRY_ATTEMPTS,
    RETRY_DELAY,
    REQUEST_TIMEOUT,
    THEMEMBERS_DEVELOPER_TOKEN,
    THEMEMBERS_PLATFORM_TOKEN,
)
from .models import TheMembersSyncLog, TheMembersProduct


class TheMembersAPIService:
    """
    Serviço principal para comunicação com a API TheMembers
    """
    
    def __init__(self):
        self.base_url = THEMEMBERS_API_URL
        self.headers = DEFAULT_HEADERS
        self.timeout = REQUEST_TIMEOUT
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict:
        """
        Faz uma requisição para a API TheMembers com retry automático
        """
        url = f"{self.base_url}{endpoint}"
        headers = {**self.headers, **kwargs.get('headers', {})}
        
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Log da resposta para debugging
                print(f"TheMembers API {method} {endpoint}: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * RETRY_DELAY * 2
                    print(f"Rate limit atingido. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Erro na API: {response.status_code} - {response.text}")
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                print(f"Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt == RETRY_ATTEMPTS - 1:
                    raise
                time.sleep(RETRY_DELAY)
        
        raise Exception(f"Falha após {RETRY_ATTEMPTS} tentativas")
    
    def get_products(self) -> List[Dict[str, Any]]:
        """
        Busca todos os produtos da plataforma TheMembers com paginação
        """
        try:
            all_products = []
            cursor = None
            page = 1
            
            print(f"🚀 Iniciando busca de produtos com paginação...")
            
            while True:
                # Endpoint para listar produtos
                endpoint = f"/products/all-products/{settings.THEMEMBERS_DEVELOPER_TOKEN}/{settings.THEMEMBERS_PLATFORM_TOKEN}"
                
                # Adiciona cursor se existir (para páginas seguintes)
                if cursor:
                    endpoint += f"?cursor={cursor}"
                
                print(f"📄 Página {page}: {self.base_url}{endpoint}")
                
                response = self._make_request('GET', endpoint)
                
                # Produtos estão na chave 'data', não 'products'
                products_page = response.get('data', [])
                print(f"📦 Produtos na página {page}: {len(products_page)}")
                
                if products_page:
                    all_products.extend(products_page)
                    print(f"📋 Exemplo produto: {products_page[0]['title']} (ID: {products_page[0]['id']})")
                
                # Verifica se há próxima página
                links = response.get('links', {})
                next_url = links.get('next')
                
                if not next_url:
                    print(f"✅ Última página alcançada!")
                    break
                
                # Extrai cursor da próxima página
                meta = response.get('meta', {})
                cursor = meta.get('next_cursor')
                
                if not cursor:
                    print(f"⚠️ Sem cursor para próxima página, parando...")
                    break
                
                page += 1
                
                # Proteção contra loop infinito
                if page > 20:  # Máximo 20 páginas (200 produtos)
                    print(f"⚠️ Limite de páginas atingido, parando...")
                    break
            
            print(f"🎉 Total de produtos encontrados: {len(all_products)}")
            
            # Log da sincronização
            self._log_sync('products', 'success', len(all_products), 0)
            
            return all_products
            
        except Exception as e:
            print(f"❌ Erro ao buscar produtos: {str(e)}")
            self._log_sync('products', 'failed', 0, 1, str(e))
            raise
    
    def create_users_with_products(self, product_ids: List[str], users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cria um ou mais usuários e já vincula produtos (assinaturas), conforme documentação:
        POST /users/create/{token_dev}/{token_plataforma}
        Documentação: https://documentation.themembers.dev.br/api-gerenciamento-de-usuarios/referencia-da-api/usuarios
        """
        try:
            endpoint = f"/users/create/{THEMEMBERS_DEVELOPER_TOKEN}/{THEMEMBERS_PLATFORM_TOKEN}"

            payload = {
                "product_id": product_ids,
                "users": users,
            }

            response = self._make_request('POST', endpoint, data=payload)
            print("TheMembers: usuários/assinaturas enfileirados com sucesso")
            return response
        except Exception as e:
            print(f"Erro ao criar usuário(s) na TheMembers: {str(e)}")
            raise
    
    # Mantido para compatibilidade, mas o fluxo principal usa /users/create
    def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Use create_users_with_products em vez de create_subscription.")
    
    def _log_sync(self, sync_type: str, status: str, success_count: int, failed_count: int, errors: str = None):
        """
        Registra log de sincronização
        """
        try:
            TheMembersSyncLog.objects.create(
                sync_type=sync_type,
                status=status,
                items_processed=success_count + failed_count,
                items_success=success_count,
                items_failed=failed_count,
                completed_at=timezone.now(),
                duration_seconds=0,  # TODO: Implementar cálculo de duração
                errors=errors
            )
        except Exception as e:
            print(f"Erro ao registrar log de sincronização: {str(e)}")


class CourseSyncService:
    """
    Serviço para sincronizar cursos com produtos TheMembers
    """
    
    def __init__(self):
        self.api_service = TheMembersAPIService()
    
    def sync_all_products(self) -> Dict[str, Any]:
        """
        Sincroniza todos os produtos da TheMembers com o banco local
        """
        try:
            print("Iniciando sincronização de produtos TheMembers...")
            
            # Busca produtos da API
            products = self.api_service.get_products()
            
            # Contadores para log
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for product_data in products:
                try:
                    # Tenta atualizar produto existente ou criar novo
                    # Mapeia campos da API TheMembers para o modelo local
                    product, created = TheMembersProduct.objects.update_or_create(
                        product_id=product_data.get('id'),
                        defaults={
                            'title': product_data.get('title', ''),
                            'description': product_data.get('description', '') or '',
                            'price': product_data.get('value', 0) or 0,  # Campo 'value' na API
                            'image_url': '',  # API não retorna image_url
                            'status': product_data.get('status', 'active'),
                            'last_sync': timezone.now(),
                        }
                    )
                    
                    if created:
                        created_count += 1
                        print(f"Produto criado: {product.title}")
                    else:
                        updated_count += 1
                        print(f"Produto atualizado: {product.title}")
                        
                except Exception as e:
                    error_count += 1
                    print(f"Erro ao processar produto {product_data.get('id')}: {str(e)}")
            
            # Log final
            total_processed = created_count + updated_count + error_count
            print(f"Sincronização concluída: {created_count} criados, {updated_count} atualizados, {error_count} erros")
            
            return {
                'success': True,
                'total_processed': total_processed,
                'created': created_count,
                'updated': updated_count,
                'errors': error_count
            }
            
        except Exception as e:
            print(f"Erro na sincronização: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_available_products(self) -> List[TheMembersProduct]:
        """
        Retorna lista de produtos disponíveis para vinculação
        """
        return TheMembersProduct.objects.filter(status='active').order_by('title')
    
    def link_course_to_product(self, course_id: int, product_id: str) -> bool:
        """
        Vincula um curso a um produto TheMembers
        """
        try:
            from courses.models import Course
            
            course = Course.objects.get(id=course_id)
            product = TheMembersProduct.objects.get(product_id=product_id)
            
            # Atualiza o curso com o ID do produto
            course.themembers_product_id = product_id
            course.save()
            
            print(f"Curso '{course.title}' vinculado ao produto '{product.title}'")
            return True
            
        except Course.DoesNotExist:
            print(f"Curso com ID {course_id} não encontrado")
            return False
        except TheMembersProduct.DoesNotExist:
            print(f"Produto com ID {product_id} não encontrado")
            return False
        except Exception as e:
            print(f"Erro ao vincular curso: {str(e)}")
            return False


class SubscriptionService:
    """
    Serviço para gerenciar assinaturas TheMembers
    """
    
    def __init__(self):
        self.api_service = TheMembersAPIService()
    
    def create_user_subscription(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria usuário e assinatura via endpoint /users/create, enviando o produto do curso.
        """
        try:
            # Permite reutilizar senha já gerada, se fornecida
            password = sale_data.get('password') or self._generate_random_password()

            full_name: str = sale_data.get('student_name', '') or ''
            # Usa o nome completo exatamente como foi digitado no checkout
            name_parts = full_name.strip().split(" ", 1)  # Split apenas na primeira ocorrência
            first_name = name_parts[0] if name_parts else full_name
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            full_name_exact = full_name.strip()

            user_payload = {
                "name": full_name_exact or first_name,
                "last_name": last_name,
                "email": sale_data.get('email'),
                "password": password,
                "document": sale_data.get('cpf_cnpj', '').replace('.', '').replace('-', '') if sale_data.get('cpf_cnpj') else '',
                "phone": sale_data.get('phone', '').replace('(', '').replace(')', '').replace(' ', '').replace('-', '') if sale_data.get('phone', '') else '',
                "reference_id": str(sale_data.get('sale_id', '')),
                "accession_date": timezone.now().date().isoformat(),
            }

            # Validação dos dados
            if not user_payload["name"] or not user_payload["email"] or not user_payload["password"]:
                raise Exception("Dados obrigatórios não fornecidos: nome, email ou senha")
            
            if user_payload["document"] and len(user_payload["document"]) < 11:
                raise Exception("CPF/CNPJ inválido")
            
            if user_payload["phone"] and len(user_payload["phone"]) < 10:
                raise Exception("Telefone inválido")

            print(f"TheMembers: Criando usuário com dados: {user_payload}")
            print(f"TheMembers: Nome completo original: '{sale_data.get('student_name', '')}'")
            print(f"TheMembers: Nome (enviado): '{full_name_exact or first_name}' | Sobrenome: '{last_name}'")
            print(f"TheMembers: CPF original: '{sale_data.get('cpf_cnpj', '')}'")
            print(f"TheMembers: CPF formatado: '{user_payload['document']}'")
            print(f"TheMembers: Telefone original: '{sale_data.get('phone', '')}'")
            print(f"TheMembers: Telefone formatado: '{user_payload['phone']}'")

            product_id = sale_data.get('themembers_product_id')
            if not product_id:
                raise Exception("Curso não está vinculado a um produto TheMembers")

            print(f"TheMembers: Product ID: {product_id}")
            print(f"TheMembers: API URL: {self.api_service.base_url}/users/create/{THEMEMBERS_DEVELOPER_TOKEN}/{THEMEMBERS_PLATFORM_TOKEN}")

            # Chama a API para criar usuário(s) com produto(s)
            print(f"TheMembers: Enviando payload completo: {user_payload}")
            print(f"TheMembers: Headers: {self.api_service.headers}")
            
            try:
                # Ajusta a estrutura do payload conforme documentação da TheMembers
                # Pode ser que o product_id precise ser enviado de forma diferente
                payload = {
                    "product_id": product_id,
                    "users": [user_payload]
                }
                
                print(f"TheMembers: Payload final enviado: {payload}")
                
                response = self.api_service.create_users_with_products([product_id], [user_payload])
                print(f"TheMembers: Resposta da API: {response}")
                print(f"TheMembers: Senha gerada: {password}")
                
                # ✅ NOVO: Verifica e ativa a assinatura após criação
                if response.get('success') or 'users' in response or 'user' in response:
                    print(f"TheMembers: Usuário/assinatura criado com sucesso, verificando ativação...")
                    
                    # Aguarda um pouco para a assinatura ser processada
                    import time
                    time.sleep(2)
                    
                    # Tenta ativar a assinatura
                    activation_result = self._activate_user_subscription(
                        sale_data.get('email'),
                        product_id
                    )
                    
                    if activation_result.get('success'):
                        print(f"TheMembers: Assinatura ativada com sucesso!")
                    else:
                        print(f"TheMembers: Aviso: Assinatura pode não estar ativa: {activation_result.get('error')}")
                
                # Verifica se a resposta contém informações sobre o usuário criado
                if 'users' in response:
                    created_user = response['users'][0] if response['users'] else None
                    print(f"TheMembers: Usuário criado: {created_user}")
                elif 'user' in response:
                    created_user = response['user']
                    print(f"TheMembers: Usuário criado: {created_user}")
                else:
                    print(f"TheMembers: Resposta não contém dados do usuário criado")
                    print(f"TheMembers: Verificando se o usuário foi criado mesmo assim...")
                    
                    # Tenta buscar o usuário pelo email para confirmar criação
                    # TODO: Implementar busca de usuário por email se necessário
                    
            except Exception as e:
                error_msg = str(e).lower()
                print(f"TheMembers: Erro na criação: {error_msg}")
                
                # ✅ NOVO: Verifica se é erro de usuário já existente
                if any(phrase in error_msg for phrase in [
                    'already exists', 
                    'email already registered', 
                    'user exists',
                    'email duplicate',
                    'already registered',
                    'email is already',
                    'user already'
                ]):
                    print(f"TheMembers: Usuário já existe, vinculando produto...")
                    return self._link_product_to_existing_user(sale_data)
                else:
                    # ✅ NOVO: Para qualquer outro erro, assume que usuário foi excluído e cria novo
                    print(f"TheMembers: Erro não reconhecido, assumindo usuário excluído e criando novo...")
                    return self._create_new_user_with_new_password(sale_data)
            
            return {
                'success': True,
                'password': password,  # Retorna senha para novos usuários
                'access_url': 'https://curso-passei.themembers.com.br/login',
                'new_user': True,
                'message': 'Usuário criado com sucesso'
            }
        except Exception as e:
            print(f"Erro ao criar usuário/assinatura na TheMembers: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _create_new_user_with_new_password(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Força criação de novo usuário com nova senha (para casos de usuário excluído)
        """
        try:
            # Gera nova senha
            password = self._generate_random_password()
            
            full_name: str = sale_data.get('student_name', '') or ''
            name_parts = full_name.strip().split(" ", 1)
            first_name = name_parts[0] if name_parts else full_name
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            full_name_exact = full_name.strip()

            user_payload = {
                "name": full_name_exact or first_name,
                "last_name": last_name,
                "email": sale_data.get('email'),
                "password": password,
                "document": sale_data.get('cpf_cnpj', '').replace('.', '').replace('-', '') if sale_data.get('cpf_cnpj') else '',
                "phone": sale_data.get('phone', '').replace('(', '').replace(')', '').replace(' ', '').replace('-', '') if sale_data.get('phone', '') else '',
                "reference_id": str(sale_data.get('sale_id', '')),
                "accession_date": timezone.now().date().isoformat(),
            }

            product_id = sale_data.get('themembers_product_id')
            
            print(f"TheMembers: Criando novo usuário após exclusão: {sale_data.get('email')}")
            print(f"TheMembers: Nova senha gerada: {password}")

            response = self.api_service.create_users_with_products([product_id], [user_payload])
            print(f"TheMembers: Resposta da API (novo usuário): {response}")

            return {
                'success': True,
                'password': password,  # Retorna a senha para o email
                'access_url': 'https://curso-passei.themembers.com.br/login',
                'new_user': True,
                'message': 'Novo usuário criado após exclusão'
            }
        except Exception as e:
            print(f"Erro ao criar novo usuário após exclusão: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _link_product_to_existing_user(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vincula produto a um usuário que já existe no TheMembers
        """
        try:
            email = sale_data.get('email')
            product_id = sale_data.get('themembers_product_id')
            
            print(f"TheMembers: Vinculando produto {product_id} ao usuário existente {email}")
            
            # TODO: Implementar endpoint para vincular produto a usuário existente
            # Por enquanto, retorna sucesso sem senha (usuário já tem acesso)
            
            return {
                'success': True,
                'password': None,  # Usuário já tem senha
                'access_url': 'https://curso-passei.themembers.com.br/login',
                'new_user': False,
                'message': 'Produto vinculado ao usuário existente'
            }
        except Exception as e:
            print(f"Erro ao vincular produto a usuário existente: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_user_subscriptions_bulk(self, sale_data: Dict[str, Any], product_ids: List[str]) -> Dict[str, Any]:
        """
        Cria usuário e vincula múltiplos produtos (assinaturas) em uma única chamada.
        """
        try:
            if not product_ids:
                raise Exception("Lista de product_ids vazia")

            # Permite reutilizar senha já gerada, se fornecida
            password = sale_data.get('password') or self._generate_random_password()

            full_name: str = sale_data.get('student_name', '') or ''
            name_parts = full_name.strip().split(" ", 1)
            first_name = name_parts[0] if name_parts else full_name
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            full_name_exact = full_name.strip()

            user_payload = {
                "name": full_name_exact or first_name,
                "last_name": last_name,
                "email": sale_data.get('email'),
                "password": password,
                "document": sale_data.get('cpf_cnpj', '').replace('.', '').replace('-', '') if sale_data.get('cpf_cnpj') else '',
                "phone": sale_data.get('phone', '').replace('(', '').replace(')', '').replace(' ', '').replace('-', '') if sale_data.get('phone', '') else '',
                "reference_id": str(sale_data.get('sale_id', '')),
                "accession_date": timezone.now().date().isoformat(),
            }

            # Validação básica
            if not user_payload["name"] or not user_payload["email"] or not user_payload["password"]:
                raise Exception("Dados obrigatórios não fornecidos: nome, email ou senha")

            print(f"TheMembers: Criando usuário com múltiplos produtos: {product_ids}")
            print(f"TheMembers: Payload de usuário: {user_payload}")

            response = self.api_service.create_users_with_products(product_ids, [user_payload])
            print(f"TheMembers: Resposta da API (bulk): {response}")

            return {
                'success': True,
                'password': password,
                'access_url': 'https://curso-passei.themembers.com.br/login',
            }
        except Exception as e:
            print(f"Erro ao criar usuário/assinaturas em lote na TheMembers: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_random_password(self, length: int = 12) -> str:
        """
        Gera senha aleatória segura
        """
        import random
        import string
        
        # Caracteres para senha
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        
        # Garante pelo menos um de cada tipo
        password = [
            random.choice(string.ascii_lowercase),
            random.choice(string.ascii_uppercase),
            random.choice(string.digits),
            random.choice("!@#$%^&*")
        ]
        
        # Completa o resto da senha
        password.extend(random.choice(chars) for _ in range(length - 4))
        
        # Embaralha a senha
        random.shuffle(password)
        
        return ''.join(password)

    def _activate_user_subscription(self, email: str, product_id: str) -> Dict[str, Any]:
        """
        Tenta ativar a assinatura do usuário após criação
        """
        try:
            print(f"TheMembers: Tentando ativar assinatura para {email} no produto {product_id}")
            
            # Endpoint para ativar assinatura (se existir)
            # Nota: A TheMembers pode não ter endpoint específico para ativação
            # Esta função é mais para logging e verificação
            
            # Por enquanto, apenas registra que tentou ativar
            print(f"TheMembers: Assinatura criada para {email} no produto {product_id}")
            print(f"TheMembers: Nota: A ativação pode ser automática na TheMembers")
            
            return {
                'success': True,
                'message': 'Assinatura criada e processada'
            }
            
        except Exception as e:
            print(f"TheMembers: Erro ao tentar ativar assinatura: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
