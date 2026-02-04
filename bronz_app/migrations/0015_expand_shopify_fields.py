# Generated migration to expand ShopifyOrder field sizes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bronz_app', '0014_fix_shopify_field_sizes'),
    ]

    operations = [
        # Expandir campos de texto que pueden ser largos
        migrations.AlterField(
            model_name='shopifyorder',
            name='billing_street',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Calle Facturación'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='billing_address1',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Dirección 1 Facturación'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='billing_address2',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Dirección 2 Facturación'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='shipping_street',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Calle Envío'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='shipping_address1',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Dirección 1 Envío'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='shipping_address2',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Dirección 2 Envío'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='lineitem_name',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Nombre Producto'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='shipping_method',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Método de Envío'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='billing_name',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Nombre Facturación'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='shipping_name',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Nombre Envío'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='billing_company',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Empresa Facturación'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='shipping_company',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Empresa Envío'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='customer_name',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Nombre Cliente'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=200, verbose_name='Email'),
        ),
    ]
