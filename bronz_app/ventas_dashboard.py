"""
Módulo del Dashboard de Ventas Shopify
Incluye procesamiento de datos, APIs y chatbot
"""
import json
import unicodedata

import pandas as pd
from datetime import date, datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

# Ruta al archivo Excel
VENTAS_FILE = settings.BASE_DIR / 'data' / 'ventas_shopify.xlsx'

# Cache de datos
_ventas_df = None
PANEL_YEAR_CHOICES = (2025, 2026)


def _format_number(value: float | int) -> str:
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _format_currency(value: float | int) -> str:
    return f"${_format_number(value)} CLP"


def _normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _most_common(series: pd.Series, default: str) -> str:
    if series is None or series.empty:
        return default
    mode = series.mode()
    if not mode.empty:
        return str(mode.iloc[0])
    return str(series.iloc[0]) if not series.empty else default


def _normalize_year(year_value) -> int:
    try:
        year_int = int(year_value)
    except (TypeError, ValueError):
        year_int = None
    if year_int not in PANEL_YEAR_CHOICES:
        today_year = date.today().year
        year_int = today_year if today_year in PANEL_YEAR_CHOICES else PANEL_YEAR_CHOICES[0]
    return year_int


def get_year_range_for_request(request) -> tuple[int, pd.Timestamp, pd.Timestamp]:
    year = _normalize_year(request.session.get('panel_year'))
    request.session['panel_year'] = year
    start = pd.Timestamp(year=year, month=1, day=1)
    today = pd.Timestamp(date.today())
    if year == today.year:
        end = today
    else:
        end = pd.Timestamp(year=year, month=12, day=31)
    return year, start, end


def _filter_dataframe_by_range(df: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp | None) -> pd.DataFrame:
    filtered = df
    if start is not None:
        filtered = filtered[filtered['Created at'] >= start]
    if end is not None:
        end_ts = end.normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        filtered = filtered[filtered['Created at'] <= end_ts]
    return filtered.copy()


def get_clientes_dataframe(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None) -> pd.DataFrame:
    df = get_ventas_data()
    df = _filter_dataframe_by_range(df, start_date, end_date)
    paid_orders = df[df['Financial Status'] == 'paid'].drop_duplicates(subset=['Name']).copy()

    if paid_orders.empty:
        return pd.DataFrame(columns=['cliente', 'total', 'pedidos', 'email', 'ciudad', 'region', 'ticket_promedio'])

    paid_orders['cliente'] = paid_orders['Billing Name'].fillna(paid_orders['Shipping Name'])
    paid_orders['cliente'] = paid_orders['cliente'].fillna('Cliente sin nombre')
    paid_orders['email_cliente'] = paid_orders['Email'].fillna('Sin email')
    paid_orders['ciudad_cliente'] = paid_orders['Shipping City'].fillna('Sin ciudad')
    paid_orders['region_cliente'] = paid_orders['Shipping Province Name'].fillna('Sin región')

    resumen = paid_orders.groupby('cliente').agg(
        total=('Total', 'sum'),
        pedidos=('Name', 'count'),
        email=('email_cliente', lambda x: _most_common(x, 'Sin email')),
        ciudad=('ciudad_cliente', lambda x: _most_common(x, 'Sin ciudad')),
        region=('region_cliente', lambda x: _most_common(x, 'Sin región')),
    ).reset_index()

    resumen['total'] = resumen['total'].astype(float)
    resumen['pedidos'] = resumen['pedidos'].astype(int)
    resumen['ticket_promedio'] = (resumen['total'] / resumen['pedidos']).fillna(0)

    resumen['total'] = resumen['total'].round(0).astype(int)
    resumen['ticket_promedio'] = resumen['ticket_promedio'].round(0).astype(int)

    return resumen


def get_top_clientes_por_total(limit: int = 10, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None) -> list[dict]:
    resumen = get_clientes_dataframe(start_date, end_date)
    if resumen.empty:
        return []
    top = resumen.sort_values(['total', 'pedidos'], ascending=False).head(limit)
    return top.to_dict('records')


def get_top_clientes_por_pedidos(limit: int = 10, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None) -> list[dict]:
    resumen = get_clientes_dataframe(start_date, end_date)
    if resumen.empty:
        return []
    top = resumen.sort_values(['pedidos', 'total'], ascending=False).head(limit)
    return top.to_dict('records')


def get_ventas_data():
    """Carga y cachea los datos de ventas."""
    global _ventas_df
    if _ventas_df is None:
        _ventas_df = pd.read_excel(VENTAS_FILE)
        # Limpiar y preparar datos
        _ventas_df['Created at'] = pd.to_datetime(_ventas_df['Created at'])
        _ventas_df['Total'] = pd.to_numeric(_ventas_df['Total'], errors='coerce').fillna(0)
        _ventas_df['Subtotal'] = pd.to_numeric(_ventas_df['Subtotal'], errors='coerce').fillna(0)
        _ventas_df['Lineitem quantity'] = pd.to_numeric(_ventas_df['Lineitem quantity'], errors='coerce').fillna(0)
        _ventas_df['Lineitem price'] = pd.to_numeric(_ventas_df['Lineitem price'], errors='coerce').fillna(0)
        _ventas_df['Discount Amount'] = pd.to_numeric(_ventas_df['Discount Amount'], errors='coerce').fillna(0)
    return _ventas_df

def reload_ventas_data():
    """Recarga los datos del Excel."""
    global _ventas_df
    _ventas_df = None
    return get_ventas_data()

def get_dashboard_stats(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Obtiene estadísticas principales para el dashboard."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    
    # Solo pedidos pagados
    paid_df = df[df['Financial Status'] == 'paid']
    
    # Pedidos únicos (por Name)
    unique_orders = paid_df.drop_duplicates(subset=['Name'])
    
    stats = {
        'total_ventas': int(unique_orders['Total'].sum()),
        'num_pedidos': len(unique_orders),
        'ticket_promedio': int(unique_orders['Total'].mean()) if len(unique_orders) > 0 else 0,
        'productos_vendidos': int(paid_df['Lineitem quantity'].sum()),
        'total_descuentos': int(unique_orders['Discount Amount'].sum()),
        'pedidos_fulfilled': len(unique_orders[unique_orders['Fulfillment Status'] == 'fulfilled']),
        'pedidos_pending': len(unique_orders[unique_orders['Fulfillment Status'] != 'fulfilled']),
    }
    return stats

def get_ventas_por_dia(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Ventas agrupadas por día."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    paid_df = df[df['Financial Status'] == 'paid'].drop_duplicates(subset=['Name'])
    
    paid_df['Fecha'] = paid_df['Created at'].dt.date
    daily = paid_df.groupby('Fecha').agg({
        'Total': 'sum',
        'Name': 'count'
    }).reset_index()
    daily.columns = ['fecha', 'total', 'pedidos']
    daily['fecha'] = daily['fecha'].astype(str)
    
    return daily.to_dict('records')

def get_top_productos(limit=10, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Top productos más vendidos."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    paid_df = df[df['Financial Status'] == 'paid']
    
    top = paid_df.groupby('Lineitem name').agg({
        'Lineitem quantity': 'sum',
        'Lineitem price': 'first'
    }).reset_index()
    top.columns = ['producto', 'cantidad', 'precio']
    top['total'] = top['cantidad'] * top['precio']
    top = top.sort_values('cantidad', ascending=False).head(limit)
    
    return top.to_dict('records')

def get_ventas_por_ciudad(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Ventas agrupadas por ciudad."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    paid_df = df[df['Financial Status'] == 'paid'].drop_duplicates(subset=['Name'])
    
    by_city = paid_df.groupby('Shipping City').agg({
        'Total': 'sum',
        'Name': 'count'
    }).reset_index()
    by_city.columns = ['ciudad', 'total', 'pedidos']
    by_city = by_city.sort_values('total', ascending=False).head(10)
    
    return by_city.to_dict('records')

def get_ventas_por_region(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Ventas agrupadas por región."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    paid_df = df[df['Financial Status'] == 'paid'].drop_duplicates(subset=['Name'])
    
    by_region = paid_df.groupby('Shipping Province Name').agg({
        'Total': 'sum',
        'Name': 'count'
    }).reset_index()
    by_region.columns = ['region', 'total', 'pedidos']
    by_region = by_region.sort_values('total', ascending=False)
    
    return by_region.to_dict('records')

def get_ventas_por_metodo_pago(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Ventas por método de pago."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    paid_df = df[df['Financial Status'] == 'paid'].drop_duplicates(subset=['Name'])
    
    by_payment = paid_df.groupby('Payment Method').agg({
        'Total': 'sum',
        'Name': 'count'
    }).reset_index()
    by_payment.columns = ['metodo', 'total', 'pedidos']
    by_payment = by_payment.sort_values('total', ascending=False)
    
    return by_payment.to_dict('records')

def get_pedidos_recientes(limit=20, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Últimos pedidos."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    recent = df.drop_duplicates(subset=['Name']).sort_values('Created at', ascending=False).head(limit)
    
    result = []
    for _, row in recent.iterrows():
        result.append({
            'pedido': row['Name'],
            'fecha': row['Created at'].strftime('%Y-%m-%d %H:%M'),
            'cliente': row['Billing Name'] if pd.notna(row['Billing Name']) else 'N/A',
            'ciudad': row['Shipping City'] if pd.notna(row['Shipping City']) else 'N/A',
            'total': int(row['Total']),
            'estado_pago': row['Financial Status'],
            'estado_envio': row['Fulfillment Status'] if pd.notna(row['Fulfillment Status']) else 'pending',
        })
    return result


# ============================================
# API Endpoints
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """API: Estadísticas principales."""
    try:
        _, start_date, end_date = get_year_range_for_request(request)
        stats = get_dashboard_stats(start_date, end_date)
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_ventas_por_dia(request):
    """API: Ventas por día."""
    try:
        _, start_date, end_date = get_year_range_for_request(request)
        data = get_ventas_por_dia(start_date, end_date)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_top_productos(request):
    """API: Top productos."""
    try:
        _, start_date, end_date = get_year_range_for_request(request)
        limit = int(request.GET.get('limit', 10))
        data = get_top_productos(limit, start_date, end_date)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_ventas_por_ciudad(request):
    """API: Ventas por ciudad."""
    try:
        _, start_date, end_date = get_year_range_for_request(request)
        data = get_ventas_por_ciudad(start_date, end_date)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_ventas_por_region(request):
    """API: Ventas por región."""
    try:
        _, start_date, end_date = get_year_range_for_request(request)
        data = get_ventas_por_region(start_date, end_date)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_ventas_por_metodo_pago(request):
    """API: Ventas por método de pago."""
    try:
        _, start_date, end_date = get_year_range_for_request(request)
        data = get_ventas_por_metodo_pago(start_date, end_date)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_pedidos_recientes(request):
    """API: Pedidos recientes."""
    try:
        _, start_date, end_date = get_year_range_for_request(request)
        limit = int(request.GET.get('limit', 20))
        data = get_pedidos_recientes(limit, start_date, end_date)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# Chatbot de Ventas
# ============================================

def get_ventas_summary_for_ai(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Genera un resumen de datos para el chatbot."""
    df = _filter_dataframe_by_range(get_ventas_data(), start_date, end_date)
    stats = get_dashboard_stats(start_date, end_date)
    top_products = get_top_productos(5, start_date, end_date)
    top_cities = get_ventas_por_ciudad(start_date, end_date)[:5]
    payment_methods = get_ventas_por_metodo_pago(start_date, end_date)
    top_customers_total = get_top_clientes_por_total(5, start_date, end_date)
    top_customers_orders = get_top_clientes_por_pedidos(5, start_date, end_date)

    if df.empty:
        fecha_min = fecha_max = "sin registros"
    else:
        fecha_min = df['Created at'].min().strftime('%Y-%m-%d')
        fecha_max = df['Created at'].max().strftime('%Y-%m-%d')

    summary = f"""
RESUMEN DE VENTAS SHOPIFY (Período: {fecha_min} a {fecha_max})

📊 ESTADÍSTICAS GENERALES:
- Total ventas: {_format_currency(stats['total_ventas'])}
- Número de pedidos: {stats['num_pedidos']}
- Ticket promedio: {_format_currency(stats['ticket_promedio'])}
- Productos vendidos: {_format_number(stats['productos_vendidos'])} unidades
- Descuentos aplicados: {_format_currency(stats['total_descuentos'])}
- Pedidos enviados (fulfilled): {_format_number(stats['pedidos_fulfilled'])}
- Pedidos pendientes de envío: {_format_number(stats['pedidos_pending'])}

🏆 TOP 5 PRODUCTOS MÁS VENDIDOS:
"""
    for i, p in enumerate(top_products, 1):
        summary += (
            f"{i}. {p['producto']}: {int(p['cantidad'])} unidades "
            f"({_format_currency(p['total'])})\n"
        )

    summary += "\n🗺️ TOP 5 CIUDADES POR VENTAS:\n"
    for i, c in enumerate(top_cities, 1):
        summary += (
            f"{i}. {c['ciudad']}: {_format_currency(c['total'])} "
            f"({c['pedidos']} pedidos)\n"
        )

    summary += "\n💳 VENTAS POR MÉTODO DE PAGO:\n"
    for m in payment_methods:
        summary += (
            f"- {m['metodo']}: {_format_currency(m['total'])} "
            f"({m['pedidos']} pedidos)\n"
        )

    summary += "\n🙋‍♀️ CLIENTES QUE MÁS COMPRAN (por monto total):\n"
    if top_customers_total:
        for i, cliente in enumerate(top_customers_total, 1):
            summary += (
                f"{i}. {cliente['cliente']} - {_format_currency(cliente['total'])} en "
                f"{cliente['pedidos']} pedidos (ticket promedio {_format_currency(cliente['ticket_promedio'])})"
            )
            if cliente.get('ciudad'):
                summary += f" · Ciudad frecuente: {cliente['ciudad']}"
            summary += "\n"
    else:
        summary += "Sin datos disponibles.\n"

    summary += "\n📦 CLIENTES CON MÁS PEDIDOS:\n"
    if top_customers_orders:
        for i, cliente in enumerate(top_customers_orders, 1):
            summary += (
                f"{i}. {cliente['cliente']} - {cliente['pedidos']} pedidos "
                f"({_format_currency(cliente['total'])} en total)\n"
            )
    else:
        summary += "Sin datos disponibles.\n"

    return summary

def get_ventas_chatbot_system_prompt(start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    """Genera el prompt del sistema para el chatbot de ventas."""
    summary = get_ventas_summary_for_ai(start_date, end_date)

    return f"""Eres un asistente experto en análisis de ventas de la tienda BRONZ en Shopify.
Tu rol es responder preguntas sobre las ventas, productos, clientes y métricas del negocio.

Tienes acceso a los siguientes datos actualizados:

{summary}

INSTRUCCIONES:
- Responde siempre en español chileno de manera profesional pero cercana
- Usa los datos proporcionados para responder con precisión y evita decir que no tienes acceso cuando el dato está arriba
- Cuando hables de clientes, apóyate en los listados de clientes destacados (por monto y por pedidos) para responder con nombres concretos
- Si te preguntan algo que no está en los datos, indícalo amablemente y explica qué información relacionada sí está disponible
- Formatea los números con separadores de miles para mejor legibilidad
- Cuando hables de dinero, usa CLP (pesos chilenos)
- Si te piden análisis o recomendaciones, basálas en los datos disponibles
- Sé conciso pero informativo
"""


def answer_sales_question_directly(user_message: str, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None) -> str | None:
    """Intenta responder preguntas frecuentes sin llamar a OpenAI."""
    normalized = _normalize_text(user_message)
    if not normalized:
        return None

    top_total = get_top_clientes_por_total(5, start_date, end_date)
    top_orders = get_top_clientes_por_pedidos(5, start_date, end_date)

    phrases_top_total = [
        "cliente que mas compra",
        "cliente que mas gasta",
        "mejor cliente",
        "cliente principal",
        "cliente estrella",
        "quien es el cliente top",
    ]
    phrases_rank_total = [
        "top clientes",
        "ranking de clientes",
        "clientes top",
        "clientes que mas compran",
        "mejores clientes",
    ]
    phrases_orders = [
        "mas pedidos",
        "mas ordenes",
        "mas orden",
        "cliente recurrente",
        "compran seguido",
    ]

    if "cliente" in normalized:
        if any(phrase in normalized for phrase in phrases_top_total):
            if top_total:
                top = top_total[0]
                ciudad = top.get('ciudad') or 'sin ciudad registrada'
                region = top.get('region') or ''
                ubicacion = ciudad
                if region and region.lower() not in {"sin región", "sin region"} and region.lower() != ciudad.lower():
                    ubicacion = f"{ciudad}, {region}"
                respuesta = (
                    f"El cliente que más ha comprado es {top['cliente']}, con un acumulado de "
                    f"{_format_currency(top['total'])} repartidos en {top['pedidos']} pedidos. "
                    f"Su ticket promedio alcanza {_format_currency(top['ticket_promedio'])}."
                )
                if ubicacion and "sin" not in ubicacion.lower():
                    respuesta += f" Habitualmente compra desde {ubicacion}."
                return respuesta

        if any(phrase in normalized for phrase in phrases_rank_total):
            if top_total:
                listado = [
                    f"{idx}. {cliente['cliente']} – {_format_currency(cliente['total'])} en {cliente['pedidos']} pedidos"
                    for idx, cliente in enumerate(top_total, 1)
                ]
                return "Estos son los clientes con mayor monto acumulado:\n" + "\n".join(listado)

        if any(phrase in normalized for phrase in phrases_orders):
            if top_orders:
                listado = [
                    f"{idx}. {cliente['cliente']} – {cliente['pedidos']} pedidos "
                    f"({_format_currency(cliente['total'])} en total)"
                    for idx, cliente in enumerate(top_orders, 1)
                ]
                return "Los clientes con más pedidos registrados son:\n" + "\n".join(listado)

    return None


@csrf_exempt
@require_http_methods(["POST"])
def api_ventas_chat(request):
    """API del chatbot de ventas."""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])

        if not isinstance(conversation_history, list):
            conversation_history = []
        
        if not user_message:
            return JsonResponse({'error': 'El mensaje no puede estar vacío'}, status=400)

        year, start_date, end_date = get_year_range_for_request(request)

        direct_answer = answer_sales_question_directly(user_message, start_date, end_date)
        if direct_answer:
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": direct_answer})
            return JsonResponse({'response': direct_answer, 'history': conversation_history, 'panel_year': year})
        
        # Preparar mensajes para OpenAI
        messages = [
            {"role": "system", "content": get_ventas_chatbot_system_prompt(start_date, end_date)}
        ]
        
        # Agregar historial (últimos 10 mensajes)
        for msg in conversation_history[-10:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        # Llamar a OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        
        # Actualizar historial
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return JsonResponse({
            'response': assistant_message,
            'history': conversation_history,
            'panel_year': year
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_ventas_chat_clear(request):
    """Limpiar historial del chat."""
    return JsonResponse({'message': 'Historial limpiado', 'history': []})
