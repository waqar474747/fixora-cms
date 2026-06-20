from app.complaints.models import Complaint

def api_token(request):
    token_key = None
    if request.user.is_authenticated:
        from rest_framework.authtoken.models import Token
        try:
            token = Token.objects.get(user=request.user)
            token_key = token.key
        except Token.DoesNotExist:
            pass
    return {'api_token': token_key}

def user_complaint_count(request):
    if request.user.is_authenticated:
        return {
            'total_complaints': Complaint.objects.filter(user=request.user).count(),
        }
    return {}