# Generated migration to fix field sizes in ShopifyOrder

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bronz_app', '0013_shopify_orders'),
    ]

    operations = [
        # Aumentar tamaño de campos de provincia (50 -> 100)
        migrations.AlterField(
            model_name='shopifyorder',
            name='billing_province',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Provincia Facturación'),
        ),
        migrations.AlterField(
            model_name='shopifyorder',
            name='shipping_province',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Provincia Envío'),
        ),
    ]
