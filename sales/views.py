from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Sale
from .serializers import SaleSerializer, SaleListSerializer

from .models import Sale
from .serializers import SaleSerializer
from courses.models import Course
from integration_asas.services import AsaasService
from themembers.services import SubscriptionService


# Create your views here.

# Paginação customizada
class SalesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# Views de Administração (API para /admin do frontend)
class AdminSaleViewSet(generics.ListCreateAPIView):
    """
    CRUD completo de vendas para o painel admin
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'course']
    search_fields = ['student_name', 'email']
    ordering_fields = ['created_at', 'price', 'status']
    ordering = ['-created_at']


class AdminSaleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalhes, atualização e exclusão de venda para o painel admin
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


class AdminSaleListView(generics.ListAPIView):
    """
    Lista de vendas para o painel admin (versão simplificada) com paginação
    """
    queryset = Sale.objects.all()
    serializer_class = SaleListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SalesPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'course']
    search_fields = ['student_name', 'email']
    ordering_fields = ['created_at', 'price', 'status']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        """Lista vendas. Com group_by_payment=true, agrupa por pagamento (checkout)."""
        try:
            group_by_payment = str(request.query_params.get('group_by_payment', '')).lower() in ['1', 'true', 'yes']
            queryset = self.filter_queryset(self.get_queryset())

            if not group_by_payment:
                return super().list(request, *args, **kwargs)

            # Constrói grupos por asaas_payment_id (ou id individual)
            sales = queryset.order_by('-created_at')
            groups = {}
            for s in sales:
                key = s.asaas_payment_id or f"sale_{s.id}"
                group = groups.get(key)
                if group is None:
                    groups[key] = {
                        'sales': [s],
                        'latest': s.created_at,
                        'max_price': float(s.price),
                        'course_titles': [s.course.title],
                        'main_sale': s,
                    }
                else:
                    group['sales'].append(s)
                    if s.created_at > group['latest']:
                        group['latest'] = s.created_at
                    group['course_titles'].append(s.course.title)
                    price_val = float(s.price)
                    if price_val > group['max_price']:
                        group['max_price'] = price_val
                        group['main_sale'] = s

            # Converte grupos em itens agregados
            items = []
            for group in groups.values():
                s = group['main_sale']
                if len(group['course_titles']) > 1:
                    course_title = f"Carrinho: {group['course_titles'][0]} + {len(group['course_titles']) - 1} outros"
                else:
                    course_title = s.course.title

                items.append({
                    'id': s.id,
                    'student_name': s.student_name,
                    'email': s.email,
                    'phone': s.phone,
                    'course_title': course_title,
                    'price': group['max_price'],
                    'payment_method': s.payment_method,
                    'status': s.status,
                    'created_at': group['latest'],
                })

            # Ordena por data do checkout
            items.sort(key=lambda x: x['created_at'], reverse=True)

            page = self.paginate_queryset(items)
            if page is not None:
                return self.get_paginated_response(page)
            return Response(items)
        except Exception as e:
            return Response({'error': f'Erro ao listar vendas: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_statistics(request):
    """
    Retorna estatísticas agregadas de vendas para o dashboard admin
    """
    try:
        # Filtros de data (opcional)
        days_filter = request.query_params.get('days', '30')
        try:
            days = int(days_filter)
            start_date = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            start_date = timezone.now() - timedelta(days=days)
        
        # Base queryset com filtro de data - APENAS VENDAS PAGAS
        base_queryset = Sale.objects.filter(
            created_at__gte=start_date,
            status='paid'  # ← CORREÇÃO: Só vendas pagas
        )
        
        # Estatísticas gerais
        total_sales = base_queryset.aggregate(
            total=Sum('price'),
            count=Count('id')
        )
        
        # Vendas por status (apenas para referência, mas base_queryset já é só 'paid')
        status_stats = base_queryset.values('status').annotate(
            count=Count('id'),
            total=Sum('price')
        )
        
        # Vendas por método de pagamento
        payment_stats = base_queryset.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('price')
        )
        
        # Vendas por curso
        course_stats = base_queryset.values(
            'course__title'
        ).annotate(
            count=Count('id'),
            total=Sum('price')
        ).order_by('-total')[:5]  # Top 5 cursos
        
        # Vendas por dia (últimos 7 dias) - APENAS PAGAS
        daily_stats = []
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            day_sales = base_queryset.filter(
                created_at__date=date.date()
            ).aggregate(
                count=Count('id'),
                total=Sum('price')
            )
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': day_sales['count'] or 0,
                'total': float(day_sales['total'] or 0)
            })
        daily_stats.reverse()
        
        # Cálculos derivados
        total_revenue = float(total_sales['total'] or 0)
        total_count = total_sales['count'] or 0
        average_ticket = total_revenue / total_count if total_count > 0 else 0
        
        # Status específicos - APENAS PAGAS
        paid_sales = base_queryset.count()  # base_queryset já é só 'paid'
        pending_sales = Sale.objects.filter(
            created_at__gte=start_date,
            status='pending'
        ).count()
        cancelled_sales = Sale.objects.filter(
            created_at__gte=start_date,
            status='cancelled'
        ).count()
        
        # Total de vendas no período (para comparação)
        total_sales_period = Sale.objects.filter(created_at__gte=start_date).count()
        
        # Novos alunos (vendas únicas por email) - APENAS PAGOS
        new_students = base_queryset.values('email').distinct().count()
        
        response_data = {
            'period': {
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat()
            },
            'overview': {
                'total_revenue': total_revenue,
                'total_sales': total_count,
                'average_ticket': round(average_ticket, 2),
                'new_students': new_students
            },
            'status_breakdown': {
                'paid': paid_sales,
                'pending': pending_sales,
                'cancelled': cancelled_sales,
                'total': total_sales_period
            },
            'payment_methods': list(payment_stats),
            'top_courses': list(course_stats),
            'daily_trend': daily_stats,
            'status_details': list(status_stats)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Erro ao calcular estatísticas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_sale_and_redirect(request):
    """Cria uma venda e redireciona para checkout Asaas"""
    try:
        # Dados recebidos do frontend
        course_id = request.data.get('course_id')
        student_name = request.data.get('student_name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        cpf_cnpj = request.data.get('cpf_cnpj', '')
        payment_method = request.data.get('payment_method', 'pix')
        installment_count = request.data.get('installment_count')
        installment_count = request.data.get('installment_count')
        
        # Validações básicas
        if not all([course_id, student_name, email, phone]):
            return Response({
                'error': 'Todos os campos obrigatórios devem ser preenchidos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Busca o curso
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({
                'error': 'Curso não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Valida método de pagamento por curso
        allowed = {
            'pix': getattr(course, 'allow_pix', True),
            'credit_card': getattr(course, 'allow_credit_card', True),
            'bank_slip': getattr(course, 'allow_bank_slip', True),
            'bank_slip_installments': getattr(course, 'allow_boleto_installments', False),
        }
        if payment_method not in allowed or not allowed[payment_method]:
            return Response({'error': 'Forma de pagamento não permitida para este curso'}, status=status.HTTP_400_BAD_REQUEST)

        # Cria a venda
        sale = Sale.objects.create(
            course=course,
            student_name=student_name,
            email=email,
            phone=phone,
            cpf_cnpj=cpf_cnpj,
            price=course.price,
            payment_method=payment_method,
            status='pending'
        )

        # Salva dados de parcelas se boleto parcelado
        if payment_method == 'bank_slip_installments':
            try:
                installments = int(installment_count or getattr(course, 'max_boleto_installments', 12))
                sale.bank_slip_installment_count = installments
                try:
                    sale.bank_slip_installment_value = float(sale.price) / installments
                except Exception:
                    pass
                sale.save()
            except Exception:
                pass
        
        # Cria pagamento no Asaas
        asaas_service = AsaasService()
        print(f"DEBUG: Criando pagamento para venda {sale.id} com método {payment_method}")
        asaas_payment = asaas_service.create_payment(sale, payment_method, installment_count=installment_count)
        
        if not asaas_payment:
            # Se falhar, deleta a venda e retorna erro
            print(f"DEBUG: Falha ao criar pagamento, deletando venda {sale.id}")
            sale.delete()
            return Response({
                'error': 'Erro ao criar pagamento no Asaas'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        print(f"DEBUG: Pagamento criado com sucesso: {asaas_payment.asaas_id}")
        # Vincula o pagamento ASAAS à venda para futuras consultas
        sale.asaas_payment_id = asaas_payment.asaas_id
        sale.save()
        
        # Retorna dados para redirecionamento
        response_data = {
            'success': True,
            'sale_id': sale.id,
            'asaas_payment_id': asaas_payment.asaas_id,
            'payment_type': asaas_payment.payment_type,
            'status': asaas_payment.status,
            'value': float(asaas_payment.value),
            'due_date': str(asaas_payment.due_date),
            'redirect_url': None  # Será preenchido abaixo
        }
        
        # Gera URL de redirecionamento baseada no método de pagamento
        print(f"DEBUG: Gerando resposta para método de pagamento: {payment_method}")
        
        if payment_method == 'pix':
            # Para PIX, retorna QR Code e dados
            print(f"DEBUG: Configurando resposta PIX, QR Code length: {len(asaas_payment.pix_qr_code) if asaas_payment.pix_qr_code else 0}")
            response_data.update({
                'pix_qr_code': asaas_payment.pix_qr_code,
                'message': 'Pagamento PIX criado. Escaneie o QR Code para pagar.'
            })
        elif payment_method == 'credit_card':
            # Para cartão, usa invoiceUrl pública do Asaas
            response_data.update({
                'redirect_url': asaas_payment.invoice_url or asaas_payment.payment_link_url,
                'message': 'Redirecionando para checkout do cartão de crédito.'
            })
        elif payment_method in ('bank_slip', 'bank_slip_installments'):
            # Para boleto, retorna URL do boleto; para parcelado, tenta o carnê
            redirect = asaas_payment.bank_slip_url or asaas_payment.invoice_url or asaas_payment.payment_link_url
            if payment_method == 'bank_slip_installments':
                try:
                    book = asaas_service.get_installment_book_url(getattr(asaas_payment, 'installment_id', None))
                    if book:
                        redirect = book
                except Exception:
                    pass
            response_data.update({
                'redirect_url': redirect,
                'message': 'Boleto gerado. Clique para imprimir e pagar.' if payment_method == 'bank_slip' else 'Carnê gerado no Asaas. Acesse o link para os boletos.'
            })
        
        
        print(f"DEBUG: Resposta final configurada: {response_data}")
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Erro interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_cart_sale_and_redirect(request):
    """Cria uma venda unificada para múltiplos cursos do carrinho e redireciona para checkout Asaas"""
    try:
        # Dados recebidos do frontend
        courses_data = request.data.get('courses', [])  # Array de cursos
        student_name = request.data.get('student_name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        cpf_cnpj = request.data.get('cpf_cnpj', '')
        payment_method = request.data.get('payment_method', 'pix')
        installment_count = request.data.get('installment_count')
        
        # Validações básicas
        if not all([courses_data, student_name, email, phone]):
            return Response({
                'error': 'Todos os campos obrigatórios devem ser preenchidos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(courses_data, list) or len(courses_data) == 0:
            return Response({
                'error': 'Lista de cursos inválida'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcula valor total do carrinho
        total_amount = 0
        courses_to_process = []
        
        for course_data in courses_data:
            course_id = course_data.get('id')
            course_price = course_data.get('price')
            
            if not course_id or not course_price:
                return Response({
                    'error': 'Dados do curso inválidos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                course = Course.objects.get(id=course_id)
                courses_to_process.append(course)
                total_amount += float(course_price)
            except Course.DoesNotExist:
                return Response({
                    'error': f'Curso com ID {course_id} não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Se alguma forma de pagamento não for permitida em algum curso, bloqueia
        for c in courses_to_process:
            allowed = {
                'pix': getattr(c, 'allow_pix', True),
                'credit_card': getattr(c, 'allow_credit_card', True),
                'bank_slip': getattr(c, 'allow_bank_slip', True),
                'bank_slip_installments': getattr(c, 'allow_boleto_installments', False),
            }
            if payment_method not in allowed or not allowed[payment_method]:
                return Response({'error': f'Forma de pagamento não permitida para o curso {c.title}'}, status=status.HTTP_400_BAD_REQUEST)

        # Cria uma venda principal para o carrinho
        main_sale = Sale.objects.create(
            course=courses_to_process[0],  # Curso principal para referência
            student_name=student_name,
            email=email,
            phone=phone,
            cpf_cnpj=cpf_cnpj,
            price=total_amount,  # Valor total do carrinho
            payment_method=payment_method,
            status='pending'
        )

        if payment_method == 'bank_slip_installments':
            try:
                # Usa o menor máximo entre os cursos
                max_allowed = min([getattr(c, 'max_boleto_installments', 12) or 12 for c in courses_to_process])
                installments = int(installment_count or max_allowed)
                main_sale.bank_slip_installment_count = installments
                main_sale.bank_slip_installment_value = float(main_sale.price) / installments
                main_sale.save()
            except Exception:
                pass
        
        # Cria vendas relacionadas para cada curso (para rastreamento)
        related_sales = []
        # ✅ Evita duplicar o primeiro curso (que já está na venda principal)
        for course in courses_to_process[1:]:
            related_sale = Sale.objects.create(
                course=course,
                student_name=student_name,
                email=email,
                phone=phone,
                cpf_cnpj=cpf_cnpj,
                price=course.price,  # Preço individual do curso
                payment_method=payment_method,
                status='pending',
                # ✅ Todas as vendas relacionadas compartilham o mesmo asaas_payment_id
                asaas_payment_id=f"cart_{main_sale.id}"
            )
            related_sales.append(related_sale)
        
        # Cria pagamento no Asaas com valor total
        asaas_service = AsaasService()
        print(f"DEBUG: Criando pagamento de carrinho para venda {main_sale.id} com valor total {total_amount}")
        asaas_payment = asaas_service.create_payment(main_sale, payment_method, installment_count=installment_count)
        
        if not asaas_payment:
            # Se falhar, deleta todas as vendas e retorna erro
            print(f"DEBUG: Falha ao criar pagamento, deletando vendas do carrinho")
            main_sale.delete()
            for sale in related_sales:
                sale.delete()
            return Response({
                'error': 'Erro ao criar pagamento no Asaas'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        print(f"DEBUG: Pagamento de carrinho criado com sucesso: {asaas_payment.asaas_id}")
        
        # Vincula o pagamento ASAAS à venda principal
        main_sale.asaas_payment_id = asaas_payment.asaas_id
        main_sale.save()
        
        # Atualiza as vendas relacionadas com o ID do pagamento principal
        for sale in related_sales:
            sale.asaas_payment_id = asaas_payment.asaas_id
            sale.save()
        
        # Retorna dados para redirecionamento
        response_data = {
            'success': True,
            'cart_sale_id': main_sale.id,
            'related_sales': [sale.id for sale in related_sales],
            'asaas_payment_id': asaas_payment.asaas_id,
            'payment_type': asaas_payment.payment_type,
            'status': asaas_payment.status,
            'value': float(asaas_payment.value),
            'due_date': str(asaas_payment.due_date),
            'courses_count': len(courses_to_process),
            'redirect_url': None
        }
        
        # Gera URL de redirecionamento baseada no método de pagamento
        print(f"DEBUG: Gerando resposta para método de pagamento: {payment_method}")
        
        if payment_method == 'pix':
            # Para PIX, retorna QR Code e dados
            print(f"DEBUG: Configurando resposta PIX para carrinho")
            response_data.update({
                'pix_qr_code': asaas_payment.pix_qr_code,
                'message': f'Pagamento PIX criado para {len(courses_to_process)} cursos. Escaneie o QR Code para pagar.'
            })
        elif payment_method == 'credit_card':
            # Para cartão, usa invoiceUrl pública do Asaas
            response_data.update({
                'redirect_url': asaas_payment.invoice_url or asaas_payment.payment_link_url,
                'message': f'Redirecionando para checkout do cartão de crédito para {len(courses_to_process)} cursos.'
            })
        elif payment_method in ('bank_slip', 'bank_slip_installments'):
            # Para boleto, retorna URL do boleto; para parcelado, tenta o carnê
            redirect = asaas_payment.bank_slip_url or asaas_payment.invoice_url or asaas_payment.payment_link_url
            if payment_method == 'bank_slip_installments':
                try:
                    book = asaas_service.get_installment_book_url(getattr(asaas_payment, 'installment_id', None))
                    if book:
                        redirect = book
                except Exception:
                    pass
            response_data.update({
                'redirect_url': redirect,
                'message': (f'Boleto gerado para {len(courses_to_process)} cursos. Clique para imprimir e pagar.' if payment_method == 'bank_slip' else f'Carnê do parcelamento gerado para {len(courses_to_process)} cursos.')
            })
        
        print(f"DEBUG: Resposta final do carrinho configurada: {response_data}")
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        print(f"ERROR in create_cart_sale_and_redirect: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return Response({
            'error': f'Erro interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_payment_status(request, sale_id):
    """Consulta status de pagamento de uma venda"""
    try:
        sale = get_object_or_404(Sale, id=sale_id)
        
        if not sale.asaas_payment_id:
            # Tenta recuperar a partir do registro de pagamento local
            try:
                from integration_asas.models import AsaasPayment
                payment_obj = AsaasPayment.objects.filter(sale=sale).order_by('-created_at').first()
                if payment_obj:
                    sale.asaas_payment_id = payment_obj.asaas_id
                    sale.save()
                else:
                    return Response({'error': 'Venda não possui pagamento Asaas'}, status=status.HTTP_404_NOT_FOUND)
            except Exception:
                return Response({'error': 'Venda não possui pagamento Asaas'}, status=status.HTTP_404_NOT_FOUND)
        
        # Consulta status no Asaas
        asaas_service = AsaasService()
        payment_status = asaas_service.get_payment_status(sale.asaas_payment_id)
        
        if payment_status:
            status_str = payment_status.get('status', sale.status)

            # Se o Asaas indicar pago e ainda não marcamos/entregamos acesso, faça agora
            if status_str in ('RECEIVED', 'CONFIRMED'):
                updated = False
                if sale.status != 'paid':
                    sale.status = 'paid'
                    updated = True
                if updated:
                    sale.save()

                # Concede acesso TheMembers para todos os produtos vinculados (curso + carrinho)
                try:
                    asaas_service_local = AsaasService()
                    asaas_service_local._grant_themembers_access_if_needed(sale)
                except Exception as e:
                    print(f"❌ Erro ao conceder acesso TheMembers via get_payment_status: {e}")

            # Dados do comprador para mostrar no sucesso
            buyer = {
                'name': sale.student_name,
                'email': sale.email,
                'phone': sale.phone,
                'cpf_cnpj': sale.cpf_cnpj or ''
            }

            # Buscar links do WhatsApp dos cursos comprados
            whatsapp_links = []
            if sale.course:
                # Venda individual
                if sale.course.whatsapp_group_link:
                    whatsapp_links.append({
                        'course_title': sale.course.title,
                        'whatsapp_link': sale.course.whatsapp_group_link
                    })
            else:
                # Venda de carrinho - buscar todos os cursos
                from courses.models import Course
                cart_courses = Course.objects.filter(
                    themembers_product_id__in=sale.cart_courses.split(',') if sale.cart_courses else []
                )
                for course in cart_courses:
                    if course.whatsapp_group_link:
                        whatsapp_links.append({
                            'course_title': course.title,
                            'whatsapp_link': course.whatsapp_group_link
                        })

            return Response({
                'sale_id': sale.id,
                'asaas_payment_id': sale.asaas_payment_id,
                'status': status_str,
                'payment_method': sale.payment_method,
                'value': float(sale.price),
                'is_paid': sale.status == 'paid' or status_str in ('RECEIVED', 'CONFIRMED'),
                'buyer': buyer,
                'whatsapp_groups': whatsapp_links,
                'themembers': {
                    'access_granted': sale.themembers_access_granted,
                    'subscription_id': sale.themembers_subscription_id,
                    'access_url': 'https://curso-passei.themembers.com.br/login',
                    'password': sale.themembers_temp_password or ''
                }
            })
        else:
            return Response({
                'error': 'Erro ao consultar status no Asaas'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'Erro interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
