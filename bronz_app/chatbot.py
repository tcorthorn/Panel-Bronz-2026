"""
Módulo del Chatbot de productos BRONZ
Utiliza OpenAI GPT para responder preguntas basándose en el archivo de conocimiento.
"""
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

# Cliente de OpenAI
client = None

def get_openai_client():
    """Obtiene o crea el cliente de OpenAI."""
    global client
    if client is None:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return client

def load_knowledge_base():
    """Carga el archivo de conocimiento de productos."""
    try:
        with open(settings.CHATBOT_KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "No se encontró el archivo de conocimiento de productos."
    except Exception as e:
        return f"Error al cargar el archivo: {str(e)}"

def get_system_prompt(knowledge_base):
    """Genera el prompt del sistema con el contexto del conocimiento."""
    return f"""Eres un asistente experto en los productos de BRONZ, una marca de productos de belleza y cuidado personal especializada en autobronceantes y cuidado de la piel.

Tu rol es:
- Responder preguntas sobre los productos BRONZ de manera amable y profesional
- Proporcionar información precisa basada únicamente en el conocimiento que tienes
- Si no tienes información sobre algo, indica que no tienes esa información disponible
- Responder siempre en español chileno de manera cercana y amigable
- Dar recomendaciones de uso cuando sea apropiado

IMPORTANTE: Solo responde basándote en la siguiente información de productos:

---
{knowledge_base}
---

Si te preguntan sobre algo que no está en esta información, indica amablemente que no tienes esa información disponible y sugiere contactar directamente a BRONZ."""


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """
    Endpoint API para el chatbot.
    Recibe: JSON con 'message' y opcionalmente 'history'
    Retorna: JSON con 'response' y 'history'
    """
    try:
        # Parsear el cuerpo de la solicitud
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        
        if not user_message:
            return JsonResponse({'error': 'El mensaje no puede estar vacío'}, status=400)
        
        # Cargar base de conocimiento
        knowledge_base = load_knowledge_base()
        
        # Preparar mensajes para OpenAI
        messages = [
            {"role": "system", "content": get_system_prompt(knowledge_base)}
        ]
        
        # Agregar historial de conversación (máximo últimos 10 mensajes)
        for msg in conversation_history[-10:]:
            messages.append(msg)
        
        # Agregar mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})
        
        # Llamar a la API de OpenAI
        openai_client = get_openai_client()
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extraer respuesta
        assistant_message = response.choices[0].message.content
        
        # Actualizar historial
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return JsonResponse({
            'response': assistant_message,
            'history': conversation_history
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def clear_chat_api(request):
    """Endpoint para limpiar el historial de chat."""
    return JsonResponse({'message': 'Historial limpiado', 'history': []})
