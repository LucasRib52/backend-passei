from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse
import json

from .services import AsaasService
from themembers.services import SubscriptionService
from .serializers import (
    AsaasPaymentSerializer, AsaasWebhookLogSerializer,
    CreatePaymentRequestSerializer, PaymentStatusResponseSerializer,
    WebhookDataSerializer
)
from .models import AsaasPayment, AsaasWebhookLog


@api_view(['POST'])
def create_payment(request):
    """Cria um novo pagamento no Asaas"""
    serializer = CreatePaymentRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Obtém dados validados
        sale_id = serializer.validated_data['sale_id']
        payment_method = serializer.validated_data['payment_method']
        cpf_cnpj = serializer.validated_data.get('cpf_cnpj', '')
        installment_count = serializer.validated_data.get('installment_count')
        
        # Busca a venda
        from sales.models import Sale
        sale = Sale.objects.get(id=sale_id)
        
        # Atualiza CPF/CNPJ se fornecido
        if cpf_cnpj:
            sale.cpf_cnpj = cpf_cnpj
            sale.save()
        
        # Cria o pagamento no Asaas
        asaas_service = AsaasService()
        asaas_payment = asaas_service.create_payment(sale, payment_method, installment_count=installment_count)
        
        if not asaas_payment:
            return Response(
                {'error': 'Erro ao criar pagamento no Asaas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Retorna dados do pagamento criado
        payment_data = {
            'payment_id': asaas_payment.asaas_id,
            'status': asaas_payment.status,
            'payment_type': asaas_payment.payment_type,
            'value': asaas_payment.value,
            'due_date': asaas_payment.due_date,
            'payment_date': asaas_payment.payment_date,
            'pix_qr_code': asaas_payment.pix_qr_code,
            'bank_slip_url': asaas_payment.bank_slip_url,
            'is_paid': asaas_payment.is_paid,
            'is_overdue': asaas_payment.is_overdue,
            'is_pending': asaas_payment.is_pending
        }
        if getattr(asaas_payment, 'installment_id', None):
            payment_data['installment_id'] = asaas_payment.installment_id
        
        return Response(payment_data, status=status.HTTP_201_CREATED)
        
    except Sale.DoesNotExist:
        return Response(
            {'error': 'Venda não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erro interno: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_payment_status(request, payment_id):
    """Consulta status de um pagamento"""
    try:
        # Busca pagamento local
        asaas_payment = AsaasPayment.objects.get(asaas_id=payment_id)
        
        # Atualiza status do Asaas
        asaas_service = AsaasService()
        asaas_status = asaas_service.get_payment_status(payment_id)
        
        if asaas_status:
            # Atualiza status local se diferente
            if asaas_status.get('status') != asaas_payment.status:
                asaas_payment.status = asaas_status.get('status', asaas_payment.status)
                asaas_payment.save()
        
        # Retorna dados do pagamento
        payment_data = {
            'payment_id': asaas_payment.asaas_id,
            'status': asaas_payment.status,
            'payment_type': asaas_payment.payment_type,
            'value': asaas_payment.value,
            'due_date': asaas_payment.due_date,
            'payment_date': asaas_payment.payment_date,
            'pix_qr_code': asaas_payment.pix_qr_code,
            'bank_slip_url': asaas_payment.bank_slip_url,
            'is_paid': asaas_payment.is_paid,
            'is_overdue': asaas_payment.is_overdue,
            'is_pending': asaas_payment.is_pending
        }
        
        return Response(payment_data)
        
    except AsaasPayment.DoesNotExist:
        return Response(
            {'error': 'Pagamento não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erro interno: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def cancel_payment(request, payment_id):
    """Cancela um pagamento"""
    try:
        asaas_service = AsaasService()
        result = asaas_service.cancel_payment(payment_id)
        
        if result:
            # Atualiza status local
            asaas_payment = AsaasPayment.objects.get(asaas_id=payment_id)
            asaas_payment.status = 'REFUNDED'
            asaas_payment.save()
            
            return Response({'message': 'Pagamento cancelado com sucesso'})
        else:
            return Response(
                {'error': 'Erro ao cancelar pagamento'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except AsaasPayment.DoesNotExist:
        return Response(
            {'error': 'Pagamento não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erro interno: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_payments(request):
    """Lista todos os pagamentos Asaas"""
    payments = AsaasPayment.objects.all().order_by('-created_at')
    serializer = AsaasPaymentSerializer(payments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def list_webhook_logs(request):
    """Lista logs de webhooks"""
    logs = AsaasWebhookLog.objects.all().order_by('-received_at')
    serializer = AsaasWebhookLogSerializer(logs, many=True)
    return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class AsaasWebhookView(View):
    """View para receber webhooks do Asaas"""
    
    def post(self, request, *args, **kwargs):
        try:
            # Verifica se é um webhook válido do Asaas (tolerante ao formato)
            ua = request.headers.get('User-Agent', '')
            if not ua or ('asaas' not in ua.lower()):
                return HttpResponse('Unauthorized', status=401)
            
            # Processa dados do webhook
            webhook_data = json.loads(request.body)
            
            # Valida dados do webhook
            serializer = WebhookDataSerializer(data=webhook_data)
            if not serializer.is_valid():
                return HttpResponse('Invalid webhook data', status=400)
            
            # Processa webhook
            asaas_service = AsaasService()
            success = asaas_service.process_webhook(webhook_data)

            # Se pago/confirmado, cria acesso na TheMembers de forma síncrona
            try:
                event = webhook_data.get('event')
                payment = webhook_data.get('payment', {})
                if event in ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']:
                    ap = AsaasPayment.objects.filter(asaas_id=payment.get('id')).select_related('sale', 'sale__course').first()
                    if ap and not ap.sale.themembers_access_granted:
                        course = ap.sale.course
                        product_id = getattr(course, 'themembers_product_id', None)
                        if product_id:
                            sub_service = SubscriptionService()
                            sub_service.create_user_subscription({
                                'student_name': ap.sale.student_name,
                                'email': ap.sale.email,
                                'phone': ap.sale.phone,
                                'cpf_cnpj': ap.sale.cpf_cnpj,
                                'sale_id': ap.sale.id,
                                'themembers_product_id': product_id,
                                'themembers_link': getattr(course, 'themembers_link', '') or '',
                            })
            except Exception as e:
                print(f"Webhook grant TheMembers error: {e}")
            
            if success:
                return HttpResponse('OK', status=200)
            else:
                # Idempotência: já existe log do mesmo webhook_id ou erro conhecido
                return HttpResponse('OK', status=200)
                
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON', status=400)
        except Exception as e:
            print(f"Erro no webhook: {e}")
            return HttpResponse('Internal Server Error', status=500)
    
    def get(self, request, *args, **kwargs):
        """Método GET para teste do webhook"""
        return HttpResponse('Asaas Webhook endpoint is working', status=200)
