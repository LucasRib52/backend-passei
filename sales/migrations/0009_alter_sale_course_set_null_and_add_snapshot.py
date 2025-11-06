from django.db import migrations, models
import django.db.models.deletion


def populate_course_title_snapshot(apps, schema_editor):
    Sale = apps.get_model('sales', 'Sale')
    # Preenche snapshot para vendas que ainda têm curso vinculado
    for sale in Sale.objects.select_related('course').filter(course__isnull=False, course_title_snapshot__isnull=True):
        course = sale.course
        title = getattr(course, 'title', None)
        if title:
            sale.course_title_snapshot = title
            sale.save(update_fields=['course_title_snapshot'])


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0008_sale_bank_slip_installment_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='course_title_snapshot',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Título do Curso (snapshot)'),
        ),
        migrations.AlterField(
            model_name='sale',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.course', verbose_name='Curso'),
        ),
        migrations.RunPython(populate_course_title_snapshot, migrations.RunPython.noop),
    ]


