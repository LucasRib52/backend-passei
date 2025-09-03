from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .serializers import (
    DashboardOverviewSerializer, 
    RecentSaleSerializer, 
    TopCourseSerializer,
    DashboardMetricSerializer
)
from .models import DashboardMetric, StudentActivity, CoursePerformance
import logging

logger = logging.getLogger(__name__)


class DashboardOverviewView(generics.GenericAPIView):
    """
    Visão geral do dashboard com todas as métricas principais
    """
    permission_classes = []  # Temporariamente sem autenticação para desenvolvimento
    
    def get(self, request):
        try:
            # Importa modelos necessários
            from sales.models import Sale
            from courses.models import Course
            
            # Obtém período do query parameter
            period = request.query_params.get('period', 'month')
            
            # Data atual e período - usando timezone.now() para evitar problemas de timezone
            now = timezone.now()
            today = now.date()
            
            # Define período baseado no filtro
            if period == 'today':
                period_start = today
                period_label = 'hoje'
            elif period == 'week':
                # Calcula início da semana (segunda-feira)
                days_since_monday = now.weekday()
                period_start = today - timedelta(days=days_since_monday)
                period_label = 'esta semana'
            elif period == 'month':
                period_start = today.replace(day=1)
                period_label = 'este mês'
            elif period == 'quarter':
                quarter_month = ((now.month - 1) // 3) * 3 + 1
                period_start = today.replace(month=quarter_month, day=1)
                period_label = 'este trimestre'
            elif period == 'year':
                period_start = today.replace(month=1, day=1)
                period_label = 'este ano'
            else:
                period_start = today.replace(day=1)
                period_label = 'este mês'
            
            # Métricas gerais (sempre totais)
            total_revenue = Sale.objects.filter(status='paid').aggregate(
                total=Sum('price')
            )['total'] or 0
            
            total_sales = Sale.objects.filter(status='paid').count()
            total_students = Sale.objects.filter(status='paid').values('email').distinct().count()
            total_courses = Course.objects.filter(status='active').count()
            
            # Métricas do período selecionado - usando __date para comparação segura
            period_revenue = Sale.objects.filter(
                status='paid',
                created_at__date__gte=period_start
            ).aggregate(total=Sum('price'))['total'] or 0
            
            period_sales = Sale.objects.filter(
                status='paid',
                created_at__date__gte=period_start
            ).count()
            
            # Taxa de conversão (vendas pagas / total de vendas)
            total_attempts = Sale.objects.count()
            conversion_rate = (total_sales / total_attempts * 100) if total_attempts > 0 else 0
            
            # Vendas recentes agrupadas por pagamento (últimas 5 checkouts)
            sales_qs = Sale.objects.select_related('course').filter(
                status='paid'
            ).order_by('-created_at')[:50]
            
            groups = {}
            for s in sales_qs:
                key = s.asaas_payment_id or f"sale_{s.id}"
                if key not in groups:
                    groups[key] = {
                        'sales': [s],
                        'latest': s.created_at,
                        'max_price': float(s.price),  # valor total em carrinho será o maior
                        'course_titles': [s.course.title],
                        'main_sale': s,
                    }
                else:
                    g = groups[key]
                    g['sales'].append(s)
                    if s.created_at > g['latest']:
                        g['latest'] = s.created_at
                    g['course_titles'].append(s.course.title)
                    if float(s.price) > g['max_price']:
                        g['max_price'] = float(s.price)
                        g['main_sale'] = s
            
            # Ordena grupos pelo checkout mais recente e limita a 5
            sorted_groups = sorted(groups.values(), key=lambda g: g['latest'], reverse=True)[:5]
            
            recent_sales_data = []
            for g in sorted_groups:
                sale = g['main_sale']
                # Se houver mais de um curso, rotula como carrinho
                if len(g['course_titles']) > 1:
                    course_title = f"Carrinho: {g['course_titles'][0]} + {len(g['course_titles']) - 1} outros"
                else:
                    course_title = sale.course.title
                
                recent_sales_data.append({
                    'id': sale.id,
                    'student_name': sale.student_name,
                    'course_title': course_title,
                    'price': float(g['max_price']),  # usa o total (main sale)
                    'payment_method': sale.payment_method,
                    'status': sale.status,
                    'created_at': g['latest'],
                    'payment_method_display': sale.get_payment_method_display()
                })
            
            # Cursos mais vendidos
            top_courses = Sale.objects.filter(
                status='paid'
            ).values('course__title').annotate(
                total_sales=Count('id'),
                total_revenue=Sum('price')
            ).order_by('-total_revenue')[:5]
            
            top_courses_data = []
            for course in top_courses:
                # Calcula taxa de conversão por curso
                course_sales = Sale.objects.filter(
                    course__title=course['course__title'],
                    status='paid'
                ).count()
                course_attempts = Sale.objects.filter(
                    course__title=course['course__title']
                ).count()
                course_conversion = (course_sales / course_attempts * 100) if course_attempts > 0 else 0
                
                # Última venda do curso
                last_sale = Sale.objects.filter(
                    course__title=course['course__title'],
                    status='paid'
                ).order_by('-created_at').first()
                
                top_courses_data.append({
                    'course_title': course['course__title'],
                    'total_sales': course['total_sales'],
                    'total_revenue': float(course['total_revenue']),
                    'conversion_rate': round(course_conversion, 2),
                    'last_sale_date': last_sale.created_at if last_sale else None
                })
            
            # Novos alunos no período
            new_students_period = Sale.objects.filter(
                status='paid',
                created_at__date__gte=period_start
            ).values('email').distinct().count()
            
            # Dados para gráficos (últimos 30 dias)
            revenue_chart_data = []
            sales_chart_data = []
            
            for i in range(30):
                date = today - timedelta(days=i)
                day_revenue = Sale.objects.filter(
                    status='paid',
                    created_at__date=date
                ).aggregate(total=Sum('price'))['total'] or 0
                
                day_sales = Sale.objects.filter(
                    status='paid',
                    created_at__date=date
                ).count()
                
                revenue_chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': float(day_revenue)
                })
                
                sales_chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': day_sales
                })
            
            # Inverte para ordem cronológica
            revenue_chart_data.reverse()
            sales_chart_data.reverse()
            
            # Prepara dados para o serializer
            dashboard_data = {
                'total_revenue': total_revenue,
                'total_sales': total_sales,
                'total_students': total_students,
                'total_courses': total_courses,
                'period_revenue': period_revenue,
                'period_sales': period_sales,
                'period_label': period_label,
                'conversion_rate': round(conversion_rate, 2),
                'recent_sales': recent_sales_data,
                'top_courses': top_courses_data,
                'new_students_period': new_students_period,
                'revenue_chart_data': revenue_chart_data,
                'sales_chart_data': sales_chart_data
            }
            
            serializer = DashboardOverviewSerializer(dashboard_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': f'Erro ao carregar dashboard: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecentSalesView(generics.ListAPIView):
    """
    Lista vendas recentes para o dashboard
    """
    permission_classes = []  # Temporariamente sem autenticação para desenvolvimento
    serializer_class = RecentSaleSerializer
    
    def get_queryset(self):
        from sales.models import Sale
        return Sale.objects.select_related('course').filter(
            status='paid'
        ).order_by('-created_at')[:20]


class TopCoursesView(generics.ListAPIView):
    """
    Lista cursos mais vendidos para o dashboard
    """
    permission_classes = []  # Temporariamente sem autenticação para desenvolvimento
    serializer_class = TopCourseSerializer
    
    def get_queryset(self):
        from sales.models import Sale
        return Sale.objects.filter(
            status='paid'
        ).values('course__title').annotate(
            total_sales=Count('id'),
            total_revenue=Sum('price')
        ).order_by('-total_revenue')[:10]


class DashboardMetricsView(generics.ListAPIView):
    """
    Lista métricas do dashboard
    """
    permission_classes = []  # Temporariamente sem autenticação para desenvolvimento
    serializer_class = DashboardMetricSerializer
    queryset = DashboardMetric.objects.all()


@api_view(['POST'])
@permission_classes([])  # Temporariamente sem autenticação para desenvolvimento
def track_student_activity(request):
    """
    Registra atividade de um aluno (para tracking de engajamento)
    """
    try:
        email = request.data.get('email')
        student_name = request.data.get('student_name')
        course_title = request.data.get('course_title')
        
        if not all([email, student_name, course_title]):
            return Response({
                'error': 'Todos os campos são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Atualiza ou cria registro de atividade
        activity, created = StudentActivity.objects.update_or_create(
            email=email,
            course_title=course_title,
            defaults={
                'student_name': student_name,
                'last_access': timezone.now(),
                'access_count': models.F('access_count') + 1
            }
        )
        
        return Response({
            'success': True,
            'message': 'Atividade registrada com sucesso'
        })
        
    except Exception as e:
        return Response({
            'error': f'Erro ao registrar atividade: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])  # Temporariamente sem autenticação para desenvolvimento
def get_period_comparison(request):
    """
    Compara métricas entre períodos (útil para gráficos)
    """
    try:
        period = request.query_params.get('period', 'month')
        
        if period == 'month':
            current_start = timezone.now().replace(day=1)
            previous_start = (current_start - timedelta(days=1)).replace(day=1)
        elif period == 'week':
            current_start = timezone.now() - timedelta(days=timezone.now().weekday())
            previous_start = current_start - timedelta(weeks=1)
        else:
            current_start = timezone.now().replace(day=1)
            previous_start = (current_start - timedelta(days=1)).replace(day=1)
        
        from sales.models import Sale
        
        # Métricas do período atual
        current_revenue = Sale.objects.filter(
            status='paid',
            created_at__gte=current_start
        ).aggregate(total=Sum('price'))['total'] or 0
        
        current_sales = Sale.objects.filter(
            status='paid',
            created_at__gte=current_start
        ).count()
        
        # Métricas do período anterior
        previous_revenue = Sale.objects.filter(
            status='paid',
            created_at__gte=previous_start,
            created_at__lt=current_start
        ).aggregate(total=Sum('price'))['total'] or 0
        
        previous_sales = Sale.objects.filter(
            status='paid',
            created_at__gte=previous_start,
            created_at__lt=current_start
        ).count()
        
        # Calcula variações
        revenue_change = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        sales_change = ((current_sales - previous_sales) / previous_sales * 100) if previous_sales > 0 else 0
        
        return Response({
            'current_period': {
                'revenue': float(current_revenue),
                'sales': current_sales
            },
            'previous_period': {
                'revenue': float(previous_revenue),
                'sales': previous_sales
            },
            'changes': {
                'revenue_change': round(revenue_change, 2),
                'sales_change': round(sales_change, 2)
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Erro ao calcular comparação: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
