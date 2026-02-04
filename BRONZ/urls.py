from django.contrib import admin
from django.urls import path, include
from bronz_app import views
from bronz_app.chatbot import chat_api, clear_chat_api
from bronz_app.ventas_dashboard import (
    api_dashboard_stats,
    api_ventas_por_dia,
    api_top_productos,
    api_ventas_por_ciudad,
    api_ventas_por_region,
    api_ventas_por_metodo_pago,
    api_pedidos_recientes,
    api_ventas_chat,
    api_ventas_chat_clear,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('consultas/', include('bronz_app.urls')),
    path("", views.home, name="home"),  # Página de inicio
    path('panel/year/', views.set_panel_year, name='set_panel_year'),
    path('consult/', include('consult_app.urls')),
    
    # Chatbot de productos
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('api/chat/', chat_api, name='chat_api'),
    path('api/chat/clear/', clear_chat_api, name='clear_chat_api'),
    
    # Dashboard de Ventas Shopify
    path('ventas-dashboard/', views.ventas_dashboard_view, name='ventas_dashboard'),
    path('api/ventas/stats/', api_dashboard_stats, name='api_ventas_stats'),
    path('api/ventas/por-dia/', api_ventas_por_dia, name='api_ventas_por_dia'),
    path('api/ventas/top-productos/', api_top_productos, name='api_top_productos'),
    path('api/ventas/por-ciudad/', api_ventas_por_ciudad, name='api_ventas_por_ciudad'),
    path('api/ventas/por-region/', api_ventas_por_region, name='api_ventas_por_region'),
    path('api/ventas/por-metodo-pago/', api_ventas_por_metodo_pago, name='api_ventas_por_metodo_pago'),
    path('api/ventas/pedidos-recientes/', api_pedidos_recientes, name='api_pedidos_recientes'),
    path('api/ventas/chat/', api_ventas_chat, name='api_ventas_chat'),
    path('api/ventas/chat/clear/', api_ventas_chat_clear, name='api_ventas_chat_clear'),
]