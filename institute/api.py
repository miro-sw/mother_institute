from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

@api_view(["GET"])
@permission_classes([AllowAny])
def info(request):
    """Minimal health/info endpoint for Streamlit frontend and smoke tests."""
    return Response({
        "app": "mother_institute",
        "status": "ok",
        "version": "0.1",
    })
