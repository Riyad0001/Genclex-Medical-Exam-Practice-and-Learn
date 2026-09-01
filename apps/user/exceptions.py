from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler to ensure all errors are returned as strings,
    preventing the drf_response_wrapper middleware from crashing on nested dicts.
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Flatten any nested error structures to strings
        if isinstance(response.data, dict):
            for key, value in response.data.items():
                if isinstance(value, dict):
                    # Convert nested dict to a string representation
                    response.data[key] = str(value)
                elif isinstance(value, list):
                    # Flatten list of errors to single string
                    response.data[key] = " ".join([str(item) for item in value])
    
    return response
