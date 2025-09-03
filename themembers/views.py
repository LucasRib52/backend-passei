"""
Views para integração com TheMembers
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .services import CourseSyncService, SubscriptionService
from .models import TheMembersProduct, TheMembersIntegration
from courses.models import Course


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_products(request):
    """
    Retorna lista de produtos TheMembers disponíveis para vinculação
    """
    try:
        sync_service = CourseSyncService()
        products = sync_service.get_available_products()
        
        # Serializa produtos
        products_data = []
        for product in products:
            products_data.append({
                'id': product.product_id,
                'title': product.title,
                'description': product.description,
                'price': str(product.price),
                'image_url': product.image_url,
                'status': product.status,
                'last_sync': product.last_sync.isoformat() if product.last_sync else None,
            })
        
        return Response({
            'success': True,
            'products': products_data,
            'total': len(products_data)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def link_course_to_product(request):
    """
    Vincula um curso a um produto TheMembers
    """
    try:
        course_id = request.data.get('course_id')
        product_id = request.data.get('product_id')
        
        if not course_id or not product_id:
            return Response({
                'success': False,
                'error': 'course_id e product_id são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica se curso existe
        course = get_object_or_404(Course, id=course_id)
        
        # Verifica se produto existe
        product = get_object_or_404(TheMembersProduct, product_id=product_id)
        
        # Vincula curso ao produto
        sync_service = CourseSyncService()
        success = sync_service.link_course_to_product(course_id, product_id)
        
        if success:
            # Cria ou atualiza integração
            integration, created = TheMembersIntegration.objects.update_or_create(
                course=course,
                product=product,
                defaults={
                    'status': 'active',
                    'last_sync': timezone.now(),
                }
            )
            
            return Response({
                'success': True,
                'message': f'Curso "{course.title}" vinculado ao produto "{product.title}"',
                'integration_id': integration.id,
                'created': created
            })
        else:
            return Response({
                'success': False,
                'error': 'Falha ao vincular curso ao produto'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Curso não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except TheMembersProduct.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Produto TheMembers não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def sync_products(request):
    """
    Executa sincronização manual de produtos TheMembers
    """
    try:
        sync_service = CourseSyncService()
        result = sync_service.sync_all_products()
        
        return Response({
            'success': result['success'],
            'message': 'Sincronização executada com sucesso' if result['success'] else 'Falha na sincronização',
            'data': result
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_integration(request, course_id):
    """
    Retorna informações de integração de um curso específico
    """
    try:
        course = get_object_or_404(Course, id=course_id)
        
        # Busca integração ativa
        integration = TheMembersIntegration.objects.filter(
            course=course, 
            status='active'
        ).first()
        
        if integration:
            return Response({
                'success': True,
                'integration': {
                    'id': integration.id,
                    'status': integration.status,
                    'product': {
                        'id': integration.product.product_id,
                        'title': integration.product.title,
                        'price': str(integration.product.price),
                    },
                    'integration_date': integration.integration_date.isoformat(),
                    'last_sync': integration.last_sync.isoformat() if integration.last_sync else None,
                }
            })
        else:
            return Response({
                'success': True,
                'integration': None,
                'message': 'Curso não possui integração ativa com TheMembers'
            })
            
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Curso não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_subscription_for_sale(request):
    """
    Cria assinatura TheMembers para uma venda confirmada
    """
    try:
        sale_id = request.data.get('sale_id')
        
        if not sale_id:
            return Response({
                'success': False,
                'error': 'sale_id é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Busca a venda
        from sales.models import Sale
        sale = get_object_or_404(Sale, id=sale_id)
        
        # Verifica se a venda está paga
        if sale.status != 'paid':
            return Response({
                'success': False,
                'error': 'Venda deve estar com status "pago" para criar assinatura'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica se curso tem integração TheMembers
        if not sale.course.themembers_product_id:
            return Response({
                'success': False,
                'error': 'Curso não possui integração com TheMembers'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Dados para criação da assinatura
        sale_data = {
            'student_name': sale.student_name,
            'email': sale.email,
            'themembers_product_id': sale.course.themembers_product_id,
            'themembers_link': sale.course.themembers_link,
        }
        
        # Cria assinatura
        subscription_service = SubscriptionService()
        result = subscription_service.create_user_subscription(sale_data)
        
        if result['success']:
            # Atualiza a venda com informações da assinatura
            sale.themembers_subscription_id = result['subscription_id']
            sale.themembers_access_granted = True
            sale.save()
            
            return Response({
                'success': True,
                'message': 'Assinatura criada com sucesso',
                'data': {
                    'subscription_id': result['subscription_id'],
                    'user_id': result['user_id'],
                    'access_url': result['access_url'],
                }
            })
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Sale.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Venda não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
