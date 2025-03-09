from django.http import JsonResponse
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Avg
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
import json
from .models import Professor, Module, ModuleInstance, Rating


# ------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------

def token_required(request):
    """Check if a valid token is provided."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Token '):
        token_key = auth_header.split(' ')[1]
        try:
            token = Token.objects.get(key=token_key)
            request.user = token.user
            return True
        except Token.DoesNotExist:
            return JsonResponse({'error': 'Invalid token or token expired. Please log in again.'}, status=401)
    return JsonResponse({'error': 'Authentication token required. Please log in.'}, status=401)


def parse_json_request(request):
    """Parse JSON body of a POST request."""
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return None


def json_response(message, status=200):
    """Return a standardized JSON response."""
    return JsonResponse(message, status=status, content_type='application/json')


# ------------------------------------------------------------------------
# Authentication Views
# ------------------------------------------------------------------------

@csrf_exempt
def register(request):
    """Register a new user."""
    if request.method != 'POST':
        return json_response({'error': 'Invalid request method.'}, status=405)

    data = parse_json_request(request)
    if not data:
        return json_response({'error': 'Invalid JSON data.'}, status=400)

    username, email, password = data.get('username'), data.get('email'), data.get('password')
    if not username or not email or not password:
        return json_response({'error': 'All fields are required.'}, status=400)

    if User.objects.filter(username=username).exists():
        return json_response({'error': 'Username already exists.'}, status=400)

    User.objects.create_user(username=username, email=email, password=password)
    return json_response({'message': 'User registered successfully!'}, status=200)


@csrf_exempt
def login(request):
    """Log in a user and return a token."""
    if request.method != 'POST':
        return json_response({'error': 'Invalid request method.'}, status=405)

    data = parse_json_request(request)
    if not data:
        return json_response({'error': 'Invalid JSON data.'}, status=400)

    username, password = data.get('username'), data.get('password')
    if not username or not password:
        return json_response({'error': 'Username and password are required.'}, status=400)

    user = authenticate(username=username, password=password)
    if user:
        Token.objects.filter(user=user).delete()  # Remove old tokens
        token = Token.objects.create(user=user)
        return json_response({'message': 'Login successful!', 'token': token.key}, status=200)
    return json_response({'error': 'Username or Password is incorrect!'}, status=401)


@csrf_exempt
def logout(request):
    """Log out a user by deleting their token."""
    if request.method != 'POST':
        return json_response({'error': 'Invalid request method.'}, status=405)

    token_check = token_required(request)
    if token_check is not True:
        return token_check

    Token.objects.filter(user=request.user).delete()
    return json_response({'message': 'Logout successful!'}, status=200)


# ------------------------------------------------------------------------
# Data Retrieval Views
# ------------------------------------------------------------------------

def professor_list(request):
    """List all professors."""
    token_check = token_required(request)
    if token_check is not True:
        return token_check

    professors = Professor.objects.values('id', 'name')
    return json_response(list(professors), status=200)


def module_instance_list(request):
    """List all module instances."""
    token_check = token_required(request)
    if token_check is not True:
        return token_check

    instances = ModuleInstance.objects.select_related('module').prefetch_related('professors').all()
    instance_list = [
        {
            'id': instance.id,
            'module_code': instance.module.code,
            'module_name': instance.module.module_name,
            'year': instance.year,
            'semester': instance.semester,
            'professors': [prof.id for prof in instance.professors.all()]
        }
        for instance in instances
    ]
    return json_response(instance_list, status=200)


def rating_list(request):
    """List all ratings by the logged-in user."""
    token_check = token_required(request)
    if token_check is not True:
        return token_check

    ratings = Rating.objects.filter(user=request.user).select_related('professor', 'module_instance__module').values(
        'professor__id', 'professor__name', 'module_instance__module__module_name', 'rating'
    )
    return json_response(list(ratings), status=200)


# ------------------------------------------------------------------------
# Rating Views
# ------------------------------------------------------------------------

def average_rating(request, professor_id, module_code):
    """Get average rating for a professor in a module."""
    token_check = token_required(request)
    if token_check is not True:
        return token_check

    professor = get_object_or_404(Professor, id=professor_id)
    module = get_object_or_404(Module, code=module_code)
    module_instances = ModuleInstance.objects.filter(module=module, professors=professor)

    if not module_instances.exists():
        return json_response({'message': f"Professor {professor.name} does not teach {module.module_name}"}, status=404)

    ratings = Rating.objects.filter(professor=professor, module_instance__in=module_instances)
    if ratings.exists():
        avg_rating = round(ratings.aggregate(Avg('rating'))['rating__avg'], 1)
        return json_response({'average_rating': avg_rating}, status=200)
    return json_response({'message': 'No ratings available.'}, status=404)


@csrf_exempt
def rate_professor(request):
    """Submit a rating for a professor."""
    token_check = token_required(request)
    if token_check is not True:
        return token_check

    if request.method != 'POST':
        return json_response({'error': 'Invalid request method.'}, status=405)

    data = parse_json_request(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, status=400)

    professor_id, module_instance_id, rating_value = data.get('professor_id'), data.get('module_instance_id'), data.get('rating')
    if not (professor_id and module_instance_id and rating_value):
        return json_response({'error': 'All fields are required.'}, status=400)

    if not Professor.objects.filter(id=professor_id).exists() or not ModuleInstance.objects.filter(id=module_instance_id).exists():
        return json_response({'error': 'Invalid professor or module instance ID.'}, status=400)

    Rating.objects.create(
        user=request.user,
        professor_id=professor_id,
        module_instance_id=module_instance_id,
        rating=rating_value
    )
    return json_response({'message': 'Rating submitted successfully.'}, status=200)


# ------------------------------------------------------------------------
# API Root
# ------------------------------------------------------------------------

def api_root(request):
    """Root API view to list all available endpoints."""
    endpoints = {
        "register": reverse('register', request=request),
        "login": reverse('login', request=request),
        "logout": reverse('logout', request=request),
        "professors": reverse('professor_list', request=request),
        "module_instances": reverse('module_instance_list', request=request),
        "ratings": reverse('rating_list', request=request),
        "rate_professor": reverse('rate_professor', request=request)
    }
    return json_response(endpoints, status=200)