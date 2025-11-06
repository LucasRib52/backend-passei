from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F, CharField, Value
from django.db.models.functions import Coalesce, TruncDate
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
            # Otimizado: select_related para evitar N+1 queries
            sales_qs = Sale.objects.select_related('course').filter(
                status='paid'
            ).order_by('-created_at')[:50]
            
            groups = {}
            for s in sales_qs:
                key = s.asaas_payment_id or f"sale_{s.id}"
                if key not in groups:
                    title = s.course.title if getattr(s, 'course', None) else (s.course_title_snapshot or 'Curso removido')
                    groups[key] = {
                        'sales': [s],
                        'latest': s.created_at,
                        'max_price': float(s.price),  # valor total em carrinho será o maior
                        'course_titles': [title],
                        'main_sale': s,
                    }
                else:
                    g = groups[key]
                    g['sales'].append(s)
                    if s.created_at > g['latest']:
                        g['latest'] = s.created_at
                    title = s.course.title if getattr(s, 'course', None) else (s.course_title_snapshot or 'Curso removido')
                    g['course_titles'].append(title)
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
                    course_title = sale.course.title if getattr(sale, 'course', None) else (sale.course_title_snapshot or 'Curso removido')
                
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
            
            # Cursos mais vendidos - OTIMIZADO: queries agregadas em uma única passada
            from django.db.models import Case, When, IntegerField, Max
            
            top_courses_base = (
                Sale.objects.filter(status='paid')
                .annotate(course_title=Coalesce(F('course__title'), F('course_title_snapshot')))
                .values('course_title')
                .annotate(
                    total_sales=Count('id'),
                    total_revenue=Sum('price'),
                    last_sale_date=Max('created_at')
                )
                .order_by('-total_revenue')[:5]
            )
            
            # Pega títulos para calcular conversão de uma vez
            course_titles = [c['course_title'] for c in top_courses_base]
            
            # Query única para pegar attempts de todos os cursos
            conversion_data = {}
            if course_titles:
                conversion_query = (
                    Sale.objects.filter(
                        Q(course__title__in=course_titles) | Q(course_title_snapshot__in=course_titles)
                    )
                    .annotate(course_title=Coalesce(F('course__title'), F('course_title_snapshot')))
                    .values('course_title')
                    .annotate(
                        paid_count=Count('id', filter=Q(status='paid')),
                        total_attempts=Count('id')
                    )
                )
                
                for item in conversion_query:
                    title = item['course_title']
                    conversion_data[title] = {
                        'paid': item['paid_count'],
                        'attempts': item['total_attempts']
                    }
            
            top_courses_data = []
            for course in top_courses_base:
                title = course['course_title']
                conv_data = conversion_data.get(title, {'paid': 0, 'attempts': 0})
                course_conversion = (conv_data['paid'] / conv_data['attempts'] * 100) if conv_data['attempts'] > 0 else 0
                
                top_courses_data.append({
                    'course_title': title,
                    'total_sales': course['total_sales'],
                    'total_revenue': float(course['total_revenue']),
                    'conversion_rate': round(course_conversion, 2),
                    'last_sale_date': course['last_sale_date']
                })
            
            # Novos alunos no período
            new_students_period = Sale.objects.filter(
                status='paid',
                created_at__date__gte=period_start
            ).values('email').distinct().count()
            
            # Dados para gráficos - OTIMIZADO: adapta-se ao período selecionado
            # Define quantos dias mostrar baseado no período (com limite de performance)
            if period == 'today':
                days_for_chart = 1
                chart_start_date = today
            elif period == 'week':
                days_for_chart = 7
                chart_start_date = today - timedelta(days=6)
            elif period == 'month':
                days_for_chart = 30
                chart_start_date = today - timedelta(days=29)
            elif period == 'quarter':
                days_for_chart = 30  # Limita a 30 dias mais recentes para performance
                chart_start_date = today - timedelta(days=29)
            elif period == 'year':
                days_for_chart = 30  # Limita a 30 dias mais recentes para performance
                chart_start_date = today - timedelta(days=29)
            else:
                days_for_chart = 30
                chart_start_date = today - timedelta(days=29)
            
            # Query única com agregação por dia (muito mais rápida que N queries separadas)
            daily_data = (
                Sale.objects.filter(
                    status='paid',
                    created_at__date__gte=chart_start_date
                )
                .annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(
                    daily_revenue=Sum('price'),
                    daily_count=Count('id')
                )
                .order_by('day')
            )
            
            # Cria dicionário para lookup rápido
            daily_dict = {
                item['day']: {
                    'revenue': float(item['daily_revenue'] or 0),
                    'count': item['daily_count']
                }
                for item in daily_data
            }
            
            # Preenche todos os dias (incluindo dias sem vendas)
            revenue_chart_data = []
            sales_chart_data = []
            
            for i in range(days_for_chart):
                date = chart_start_date + timedelta(days=i)
                day_data = daily_dict.get(date, {'revenue': 0, 'count': 0})
                
                revenue_chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': day_data['revenue']
                })
                
                sales_chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': day_data['count']
                })
            
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
        return (
            Sale.objects.filter(status='paid')
            .annotate(course_title=Coalesce(F('course__title'), F('course_title_snapshot')))
            .values('course_title')
            .annotate(
                total_sales=Count('id'),
                total_revenue=Sum('price')
            )
            .order_by('-total_revenue')[:10]
        )


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
