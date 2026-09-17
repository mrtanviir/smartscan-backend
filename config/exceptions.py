from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    """
    Custom exception handler to format framework-level errors (401 Unauthorized,
    403 Forbidden, 404 Not Found, Validation errors) into the standardized API envelope:
    {
        "status": false,
        "message": "...",
        "data": null,
        "code": status_code
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        message = "অনুরোধটি সফল হয়নি"
        
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = str(response.data['detail'])
            elif 'messages' in response.data and isinstance(response.data['messages'], list) and len(response.data['messages']) > 0:
                msg_item = response.data['messages'][0]
                message = msg_item.get('message', 'টোকেনের মেয়াদ শেষ হয়ে গেছে বা অকার্যকর')
            elif response.data:
                first_key = next(iter(response.data))
                first_val = response.data[first_key]
                if isinstance(first_val, list) and len(first_val) > 0:
                    message = str(first_val[0])
                else:
                    message = str(first_val)
        elif isinstance(response.data, list) and len(response.data) > 0:
            message = str(response.data[0])

        response.data = {
            "status": False,
            "message": message,
            "data": None,
            "code": response.status_code
        }

    return response
