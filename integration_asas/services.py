import requests
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.db import IntegrityError, transaction
from .models import AsaasPayment, AsaasWebhookLog
from themembers.services import SubscriptionService
from sales.models import Sale


class AsaasService:
    """Serviço para integração com a API do Asaas"""
    
    def __init__(self):
        # Configurações do Asaas
        self.api_key = getattr(settings, 'ASAAS_API_KEY', 'sua_chave_aqui')
        self.environment = getattr(settings, 'ASAAS_ENVIRONMENT', 'production')
        
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.asaas.com/api/v3'
        else:
            self.base_url = 'https://www.asaas.com/api/v3'
        
        # A chave deve incluir o $ inicial
        self.headers = {
            'access_token': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Faz requisição para a API do Asaas"""
        url = f"{self.base_url}/{endpoint}"
        
        # Debug: mostra os headers sendo enviados
        print(f"DEBUG: URL: {url}")
        print(f"DEBUG: Headers: {self.headers}")
        print(f"DEBUG: Method: {method}")
        if data:
            print(f"DEBUG: Data: {data}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            print(f"DEBUG: Response Status: {response.status_code}")
            print(f"DEBUG: Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para Asaas: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"DEBUG: Error Response: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar resposta do Asaas: {e}")
            return None
    
    def create_customer(self, sale):
        """Cria ou atualiza cliente no Asaas"""
        customer_data = {
            'name': sale.student_name,
            'email': sale.email,
            'cpfCnpj': getattr(sale, 'cpf_cnpj', ''),
            'externalReference': str(sale.id)
        }
        
        # Verifica se já existe um cliente com este email
        existing_customer = self._make_request('GET', 'customers', params={'email': sale.email})
        
        if existing_customer and existing_customer.get('data'):
            customer_id = existing_customer['data'][0]['id']
            # Atualiza cliente existente
            return self._make_request('POST', f'customers/{customer_id}', customer_data)
        else:
            # Cria novo cliente
            return self._make_request('POST', 'customers', customer_data)
    
    def create_payment(self, sale, payment_method, installment_count: int | None = None):
        """Cria pagamento no Asaas. Suporta boleto parcelado via installmentCount/installmentValue.

        Args:
            sale: Venda local
            payment_method: 'pix' | 'credit_card' | 'bank_slip' | 'bank_slip_installments'
            installment_count: opcional, quando boleto parcelado
        """
        # Primeiro cria/atualiza o cliente
        customer_response = self.create_customer(sale)
        if not customer_response:
            return None
        
        customer_id = customer_response['id']
        
        # Calcula data de vencimento (7 dias a partir de hoje)
        due_date = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Dados base do pagamento
        payment_data = {
            'customer': customer_id,
            'billingType': payment_method.upper(),
            'value': float(sale.price),
            'dueDate': due_date,
            'description': f'Curso: {sale.course.title}',
            'externalReference': str(sale.id),
            'notificationEnabled': True
        }
        
        # Configurações específicas por método de pagamento
        if payment_method == 'pix':
            payment_data['billingType'] = 'PIX'
            payment_data['paymentLink'] = True  # Pagamento transparente para PIX
        elif payment_method == 'credit_card':
            payment_data['billingType'] = 'CREDIT_CARD'
            payment_data['paymentLink'] = True  # Cria um link de pagamento público
        elif payment_method == 'bank_slip':
            payment_data['billingType'] = 'BOLETO'
            payment_data['paymentLink'] = True  # Pagamento transparente para boleto
        elif payment_method == 'bank_slip_installments':
            payment_data['billingType'] = 'BOLETO'
            payment_data['paymentLink'] = True  # Pagamento transparente para boleto parcelado
            # Parcelamento de boleto
            # Se não vier installments, tenta usar da venda
            installments = installment_count or getattr(sale, 'bank_slip_installment_count', None)
            if not installments:
                installments = 2
            try:
                installments = int(installments)
            except Exception:
                installments = 2
            try:
                value_float = float(sale.price)
                installment_value = round(value_float / float(installments), 2)
            except Exception:
                installment_value = float(sale.price)
            payment_data['installmentCount'] = int(installments)
            payment_data['installmentValue'] = float(installment_value)

        
        # Cria o pagamento
        payment_response = self._make_request('POST', 'payments', payment_data)
        
        if payment_response:
            # Para pagamentos PIX, busca o QR Code e o código PIX
            pix_qr_code = ''
            pix_code = ''
            if payment_method == 'pix':
                # Consulta o pagamento para obter o QR Code e o código PIX
                pix_response = self._make_request('GET', f'payments/{payment_response["id"]}/pixQrCode')
                if pix_response:
                    # encodedImage é a imagem base64 do QR Code
                    pix_qr_code = pix_response.get('encodedImage', '') or ''
                    # payload é o código PIX copiável (string alfanumérica)
                    pix_code = pix_response.get('payload', '') or ''
            
            # Para cartão e boleto, use a URL pública invoiceUrl retornada pelo pagamento
            invoice_url = payment_response.get('invoiceUrl', '') or ''
            payment_link_url = payment_response.get('paymentLink', '') or ''
            
            # Cria registro local do pagamento
            # Prepara dados básicos
            payment_data_dict = {
                'sale': sale,
                'asaas_id': payment_response['id'],
                'asaas_customer_id': customer_id,
                'payment_type': payment_response['billingType'],
                'status': payment_response['status'],
                'value': sale.price,
                'due_date': due_date,
                'description': payment_data['description'],
                'customer_name': sale.student_name,
                'customer_email': sale.email,
                'customer_cpf_cnpj': getattr(sale, 'cpf_cnpj', ''),
                'pix_qr_code': pix_qr_code,
                'bank_slip_url': payment_response.get('bankSlipUrl', '') or '',
                'invoice_url': invoice_url,
                'payment_link_url': payment_link_url
            }
            
            # Tenta criar com pix_code, se falhar cria sem (compatibilidade com banco antigo)
            try:
                payment_data_dict['pix_code'] = pix_code
                asaas_payment = AsaasPayment.objects.create(**payment_data_dict)
            except Exception as e:
                # Se falhar (campo não existe no banco), cria sem pix_code
                payment_data_dict.pop('pix_code', None)
                asaas_payment = AsaasPayment.objects.create(**payment_data_dict)
                # Tenta atualizar o campo se existir (para quando migration for aplicada depois)
                try:
                    if pix_code:
                        asaas_payment.pix_code = pix_code
                        asaas_payment.save(update_fields=['pix_code'])
                except Exception:
                    pass

            # Se for parcelamento de boleto, tentar capturar dados do parcelamento
            try:
                if payment_method == 'bank_slip_installments':
                    installment_id = payment_response.get('installment', None)
                    if installment_id:
                        asaas_payment.installment_id = installment_id
                    if 'installmentCount' in payment_data:
                        asaas_payment.installment_count = int(payment_data['installmentCount'])
                    if 'installmentValue' in payment_data:
                        asaas_payment.installment_value = float(payment_data['installmentValue'])
                    asaas_payment.save()
            except Exception:
                pass
            
            return asaas_payment
        
        return None
    
    def get_payment_status(self, payment_id):
        """Consulta status de um pagamento"""
        return self._make_request('GET', f'payments/{payment_id}')
    
    def cancel_payment(self, payment_id):
        """Cancela um pagamento"""
        return self._make_request('POST', f'payments/{payment_id}/cancel')
    
    def refund_payment(self, payment_id, value=None, description=None):
        """Reembolsa um pagamento"""
        refund_data = {}
        if value:
            refund_data['value'] = value
        if description:
            refund_data['description'] = description
        
        return self._make_request('POST', f'payments/{payment_id}/refund', refund_data)
    
    def process_webhook(self, webhook_data):
        """Processa webhook recebido do Asaas"""
        try:
            # Extrai informações do webhook
            webhook_id = webhook_data.get('id')
            event_type = webhook_data.get('event')
            payment_data = webhook_data.get('payment', {})
            payment_id = payment_data.get('id')
            
            # Cria log do webhook de forma idempotente
            with transaction.atomic():
                webhook_log, created = AsaasWebhookLog.objects.get_or_create(
                    webhook_id=webhook_id,
                    defaults={
                        'event_type': event_type,
                        'payment_id': payment_id,
                        'raw_data': webhook_data
                    }
                )
            if not created and webhook_log.processed:
                # Webhook já processado anteriormente
                return True
            
            # Busca pagamento local
            try:
                asaas_payment = AsaasPayment.objects.get(asaas_id=payment_id)
            except AsaasPayment.DoesNotExist:
                webhook_log.error_message = f"Pagamento {payment_id} não encontrado localmente"
                webhook_log.processed = True
                webhook_log.processed_at = timezone.now()
                webhook_log.save()
                return False
            
            # Atualiza status do pagamento baseado no evento
            if event_type == 'PAYMENT_RECEIVED':
                asaas_payment.status = 'RECEIVED'
                asaas_payment.payment_date = timezone.now()
                asaas_payment.webhook_received = True
                asaas_payment.last_webhook_update = timezone.now()
                
                # Atualiza status da venda
                sale = asaas_payment.sale
                sale.status = 'paid'
                sale.asaas_payment_id = payment_id
                sale.save()

                # Concede acesso na TheMembers (se ainda não concedido)
                self._grant_themembers_access_if_needed(sale)
                
            elif event_type == 'PAYMENT_CONFIRMED':
                asaas_payment.status = 'CONFIRMED'
                asaas_payment.payment_date = timezone.now()
                asaas_payment.webhook_received = True
                asaas_payment.last_webhook_update = timezone.now()
                
                # Garante que a venda esteja como paga e concede acesso
                sale = asaas_payment.sale
                if sale.status != 'paid':
                    sale.status = 'paid'
                sale.asaas_payment_id = payment_id
                sale.save()

                self._grant_themembers_access_if_needed(sale)
                
            elif event_type == 'PAYMENT_OVERDUE':
                asaas_payment.status = 'OVERDUE'
                asaas_payment.webhook_received = True
                asaas_payment.last_webhook_update = timezone.now()
                
            elif event_type == 'PAYMENT_DELETED':
                asaas_payment.status = 'REFUNDED'
                asaas_payment.webhook_received = True
                asaas_payment.last_webhook_update = timezone.now()
                
            elif event_type == 'PAYMENT_UPDATED':
                # Atualiza dados do pagamento
                asaas_payment.status = payment_data.get('status', asaas_payment.status)
                asaas_payment.value = payment_data.get('value', asaas_payment.value)
                asaas_payment.webhook_received = True
                asaas_payment.last_webhook_update = timezone.now()
            
            # Salva alterações
            asaas_payment.save()
            
            # Marca webhook como processado
            webhook_log.processed = True
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            
            return True
            
        except IntegrityError:
            # Duplicidade concorrente do mesmo webhook_id: considera idempotente
            return True
        except Exception as e:
            if 'webhook_log' in locals():
                webhook_log.error_message = str(e)
                webhook_log.processed = True
                webhook_log.processed_at = timezone.now()
                webhook_log.save()
            
            print(f"Erro ao processar webhook: {e}")
            return False

    def _grant_themembers_access_if_needed(self, sale):
        """Concede acesso na TheMembers para 1 curso com múltiplos produtos ou combos (carrinho)."""
        try:
            # Se já concedido para a venda principal, ainda assim pode haver cursos relacionados
            # Vamos sempre calcular o conjunto de produtos a liberar e sincronizar status dos relacionados

            # Coleta product_ids do curso desta venda
            course = sale.course
            try:
                product_ids = course.get_themembers_product_ids()
            except Exception:
                # Compatibilidade com legado
                pid = getattr(course, 'themembers_product_id', None)
                product_ids = [pid] if pid else []

            # Se pagamento do carrinho, agrega produtos de todos os cursos relacionados
            if sale.asaas_payment_id:
                try:
                    from sales.models import Sale as SaleModel
                    related_sales = SaleModel.objects.filter(asaas_payment_id=sale.asaas_payment_id)
                    for rs in related_sales:
                        try:
                            pids = rs.course.get_themembers_product_ids()
                        except Exception:
                            rp = getattr(rs.course, 'themembers_product_id', None)
                            pids = [rp] if rp else []
                        product_ids.extend(pids)
                except Exception:
                    pass

            # Normaliza e remove duplicados
            product_ids = [p for p in product_ids if p]
            dedup = []
            seen = set()
            for p in product_ids:
                if p not in seen:
                    seen.add(p)
                    dedup.append(p)
            product_ids = dedup

            if not product_ids:
                # Nada para conceder
                return

            subscription_service = SubscriptionService()
            pre_password = sale.themembers_temp_password or ''

            # Concede em lote todos os produtos coletados
            result = subscription_service.create_user_subscriptions_bulk({
                'student_name': sale.student_name,
                'email': sale.email,
                'phone': sale.phone,
                'cpf_cnpj': sale.cpf_cnpj or '',
                'sale_id': sale.id,
                'password': pre_password
            }, product_ids)

            if result.get('success'):
                final_password = pre_password or result.get('password') or ''

                # Marca venda principal
                if not sale.themembers_access_granted:
                    sale.themembers_access_granted = True
                if final_password and sale.themembers_temp_password != final_password:
                    sale.themembers_temp_password = final_password
                sale.save()

                # Marca vendas relacionadas (se houver)
                if sale.asaas_payment_id:
                    try:
                        from sales.models import Sale as SaleModel
                        related_sales = SaleModel.objects.filter(asaas_payment_id=sale.asaas_payment_id)
                        for rs in related_sales:
                            if not rs.themembers_access_granted:
                                rs.themembers_access_granted = True
                                rs.status = 'paid'
                                if final_password:
                                    rs.themembers_temp_password = final_password
                                rs.save()
                    except Exception:
                        pass

                # Envia e-mail de acesso (uma vez, com contexto do curso principal)
                try:
                    # ✅ NOVO: Verifica se é usuário novo ou existente
                    is_new_user = themembers_result.get('new_user', True)
                    
                    if is_new_user:
                        # Usuário novo - envia email com senha
                        self._send_access_email(
                            to_email=sale.email,
                            student_name=sale.student_name,
                            course_title=course.title if len(product_ids) == 1 else f"Combo de {len(product_ids)} cursos",
                            access_url='https://curso-passei.themembers.com.br/login',
                            password=final_password
                        )
                    else:
                        # Usuário existente - envia email sem senha
                        self._send_access_email_existing_user(
                            to_email=sale.email,
                            student_name=sale.student_name,
                            course_title=course.title if len(product_ids) == 1 else f"Combo de {len(product_ids)} cursos",
                            access_url='https://curso-passei.themembers.com.br/login'
                        )
                except Exception:
                    pass
        except Exception as e:
            print(f"Erro ao conceder acesso TheMembers: {e}")

    def _send_access_email(self, to_email: str, student_name: str, course_title: str, access_url: str, password: str):
        """Envia um e-mail HTML simples com os dados de acesso ao curso."""
        try:
            subject = f"Acesso liberado: {course_title}"
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Cursos Passei <no-reply@cursopassei.com>')
            text_content = (
                f"Olá {student_name},\n\n"
                f"Seu acesso ao curso '{course_title}' foi liberado.\n"
                f"Acesse: {access_url}\n"
                f"Usuário: {to_email}\n"
                f"Senha: {password}\n\n"
                "Bons estudos!"
            )
            html_content = f"""
                <div style="font-family:Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width:640px; margin:0 auto; padding:24px; color:#0f172a;">
                  <div style="text-align:center; margin-bottom:24px;">
                    <div style="display:inline-block; padding:12px 16px; border-radius:9999px; background:#16a34a10; color:#166534; font-weight:600;">Pagamento aprovado</div>
                    <h1 style="margin:16px 0 8px; font-size:24px;">Seu acesso ao curso foi liberado!</h1>
                    <p style="margin:0; color:#475569;">{course_title}</p>
                  </div>
                  <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:20px;">
                    <p style="margin:0 0 12px;">Olá <strong>{student_name}</strong>,</p>
                    <p style="margin:0 0 12px;">Enviamos seus dados de acesso por e-mail. Você também pode acessar pela plataforma agora:</p>
                    <p style="margin:16px 0;"><a href="{access_url}" style="display:inline-block; background:#2563eb; color:#fff; padding:10px 16px; border-radius:8px; text-decoration:none;">Acessar plataforma</a></p>
                    <div style="margin-top:16px; font-size:14px; color:#334155;">
                      <div><strong>Usuário:</strong> {to_email}</div>
                      {f'<div><strong>Senha:</strong> {password}</div>' if password else ''}
                    </div>
                  </div>
                  <p style="color:#64748b; font-size:12px; margin-top:16px;">Se não realizou esta compra, entre em contato com nosso suporte.</p>
                </div>
            """
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
        except Exception as e:
            print(f"Erro ao enviar e-mail de acesso: {e}")
    
    def _send_access_email_existing_user(self, to_email: str, student_name: str, course_title: str, access_url: str):
        """Envia um e-mail HTML para usuários que já existem no TheMembers."""
        try:
            subject = f"Novo curso liberado: {course_title}"
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Cursos Passei <no-reply@cursopassei.com>')
            text_content = (
                f"Olá {student_name},\n\n"
                f"Seu novo curso '{course_title}' foi liberado na sua conta.\n"
                f"Acesse: {access_url}\n"
                f"Use suas credenciais habituais para fazer login.\n\n"
                "Bons estudos!"
            )
            html_content = f"""
                <div style="font-family:Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width:640px; margin:0 auto; padding:24px; color:#0f172a;">
                  <div style="text-align:center; margin-bottom:24px;">
                    <div style="display:inline-block; padding:12px 16px; border-radius:9999px; background:#16a34a10; color:#166534; font-weight:600;">Novo curso liberado</div>
                    <h1 style="margin:16px 0 8px; font-size:24px;">Seu novo curso foi liberado!</h1>
                    <p style="margin:0; color:#475569;">{course_title}</p>
                  </div>
                  <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:20px;">
                    <p style="margin:0 0 12px;">Olá <strong>{student_name}</strong>,</p>
                    <p style="margin:0 0 12px;">Seu novo curso foi liberado na sua conta existente. Acesse agora:</p>
                    <p style="margin:16px 0;"><a href="{access_url}" style="display:inline-block; background:#2563eb; color:#fff; padding:10px 16px; border-radius:8px; text-decoration:none;">Acessar plataforma</a></p>
                    <div style="margin-top:16px; font-size:14px; color:#334155;">
                      <div><strong>Usuário:</strong> {to_email}</div>
                      <div><strong>Senha:</strong> Use sua senha atual</div>
                    </div>
                  </div>
                  <p style="color:#64748b; font-size:12px; margin-top:16px;">Se não realizou esta compra, entre em contato com nosso suporte.</p>
                </div>
            """
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
        except Exception as e:
            print(f"Erro ao enviar e-mail de acesso para usuário existente: {e}")
    
    def get_pix_qr_code(self, payment_id):
        """Obtém QR Code PIX de um pagamento"""
        payment = self._make_request('GET', f'payments/{payment_id}')
        if payment and payment.get('pix'):
            return payment['pix'].get('qrCode'), payment['pix'].get('encodedImage')
        return None, None
    
    def get_bank_slip_url(self, payment_id):
        """Obtém URL do boleto de um pagamento"""
        payment = self._make_request('GET', f'payments/{payment_id}')
        if payment:
            return payment.get('bankSlipUrl')
        return None

    def get_installment_book_url(self, installment_id: str | None):
        """Retorna o link do carnê (paymentBook) de um parcelamento de boleto, se existir."""
        if not installment_id:
            return None
        try:
            data = self._make_request('GET', f'installments/{installment_id}/paymentBook')
            # Alguns ambientes retornam um arquivo; se vier URL, retorna
            if isinstance(data, dict):
                return data.get('url') or data.get('link')
        except Exception:
            return None
        return None
