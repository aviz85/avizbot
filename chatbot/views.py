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

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def chat(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            logger.error(f"Unauthenticated user tried to access chat. User: {request.user}")
            return JsonResponse({'error': 'Not authenticated'}, status=403)
        
        logger.debug(f"Received POST request: {request.body}")
        try:
            data = json.loads(request.body)
            user_input = data.get('user_input')
            logger.debug(f"User input: {user_input}")
            
            # Initialize the Anthropic client
            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            
            # Call the Anthropic API
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            
            logger.debug(f"Anthropic API response: {response}")
            
            bot_response = response.content[0].text
            
            # Save the message to the database
            Message.objects.create(user_input=user_input, bot_response=bot_response)
            
            return JsonResponse({'response': bot_response})
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
@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    logger.info(f"User {request.user.username} logged out")
    return JsonResponse({'success': True})
    
@require_http_methods(["GET"])
def check_auth(request):
    return JsonResponse({'authenticated': request.user.is_authenticated})