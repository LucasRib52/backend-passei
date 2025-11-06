# Generated manually for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0009_alter_sale_course_set_null_and_add_snapshot'),
    ]

    operations = [
        # Adiciona índices para melhorar performance das queries
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['created_at'], name='sales_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['status'], name='sales_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['email'], name='sales_email_idx'),
        ),
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['course_id'], name='sales_course_id_idx'),
        ),
        # Índice composto para queries filtradas por status e ordenadas por data
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['status', '-created_at'], name='sales_status_created_idx'),
        ),
        # Índice para queries que buscam por método de pagamento
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['payment_method'], name='sales_payment_method_idx'),
        ),
    ]

