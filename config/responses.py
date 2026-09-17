from rest_framework.response import Response
from rest_framework import status

def api_response(status=True, message="", data=None, code=status.HTTP_200_OK):
    """
    Standardized API response structure across all SmartScan endpoints.
    Format:
    {
        "status": bool,
        "message": str,
        "data": dict/list/null,
        "code": int
    }
    """
    return Response({
        "status": status,
        "message": message,
        "data": data,
        "code": code
    }, status=code)
