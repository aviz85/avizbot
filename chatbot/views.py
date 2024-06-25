# chatbot/views.py
import os
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods, require_POST
from .models import Message
import anthropic
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global chat history dictionary
global_chat_history = defaultdict(list)

@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def chat(request):
    global global_chat_history
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            logger.error(f"Unauthenticated user tried to access chat. User: {request.user}")
            return JsonResponse({'error': 'Not authenticated'}, status=403)
        
        logger.debug(f"Received POST request: {request.body}")
        try:
            data = json.loads(request.body)
            user_input = data.get('user_input')
            user_id = request.user.id
            chat_history = global_chat_history[user_id]
            
            logger.debug(f"User input: {user_input}")
            logger.debug(f"Chat history length for user {user_id}: {len(chat_history)}")
            
            # Initialize the Anthropic client
            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            
            # Prepare messages for the API call
            messages = chat_history + [{"role": "user", "content": user_input}]
            
            # Call the Anthropic API
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                system="""
                    ALWAYS ANSWER THE USER IN THE LANGUAGE THAT HE TALKED TO YOU.
                    Each answer should be up to 3 sentences long.
                    You are a playful and witty friend, quick with sarcastic remarks,
                    but when asked a concrete or specific question, respond clearly and straightforwardly.
                    Keep your responses short and snappy, one sentence only each time - we're in the middle of a chat,
                    so brevity is key. Aim for concise quips and clever comebacks in casual chat,
                    but provide simple and clear answers for serious questions, sometimes with a touch of sarcasm.
                """,
                max_tokens=1024,
                messages=messages
            )
            
            logger.debug(f"Anthropic API response: {response}")
            
            bot_response = response.content[0].text
            
            # Update chat history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": bot_response})
            
            # Limit chat history to 10 pairs (20 messages)
            while len(chat_history) > 20:
                chat_history.pop(0)
                chat_history.pop(0)
            
            # Update global chat history
            global_chat_history[user_id] = chat_history
            
            # Save the message to the database
            Message.objects.create(user_input=user_input, bot_response=bot_response)
            
            return JsonResponse({'response': bot_response, 'chat_history': chat_history})
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in chat view: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    logger.debug("Rendering chat template")
    return render(request, 'chatbot/chat.html')

@ensure_csrf_cookie
@require_http_methods(["POST"])
def login_view(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        logger.info(f"User {username} logged in successfully")
        return JsonResponse({'success': True})
    else:
        logger.warning(f"Failed login attempt for user {username}")
        return JsonResponse({'success': False, 'error': 'Invalid credentials'})

@require_POST
@ensure_csrf_cookie
def logout_view(request):
    user_id = request.user.id
    logout(request)
    # Clear the chat history for the logged out user
    if user_id in global_chat_history:
        del global_chat_history[user_id]
    logger.info(f"User {request.user.username} logged out and chat history cleared")
    return JsonResponse({'success': True})

@require_http_methods(["GET"])
def check_auth(request):
    return JsonResponse({'authenticated': request.user.is_authenticated})