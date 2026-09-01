import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# Ensure Daphne WebSocket frame size defaults to 25MB even under runserver
try:
    import daphne.server
    _orig_init = daphne.server.Server.__init__
    def _patched_init(self, *args, **kwargs):
        kwargs['websocket_max_message_size'] = getattr(settings, 'DAPHNE_WEBSOCKET_MAX_MESSAGE_SIZE', 25 * 1024 * 1024)
        kwargs['websocket_max_frame_size'] = getattr(settings, 'DAPHNE_WEBSOCKET_MAX_FRAME_SIZE', 25 * 1024 * 1024)
        _orig_init(self, *args, **kwargs)
    daphne.server.Server.__init__ = _patched_init
except Exception:
    pass

from django.conf import settings

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing consumers and routing.
django_asgi_app = get_asgi_application()

from apps.my_tutor.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
