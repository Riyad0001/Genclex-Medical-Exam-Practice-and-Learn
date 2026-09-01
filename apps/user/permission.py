from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.user.models import BlacklistedAccessToken

class IsNotBlacklisted(BasePermission):
    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return True

        try:
            token = auth_header.split(" ")[1]

            decoded = UntypedToken(token)
            jti = decoded["jti"]

            if BlacklistedAccessToken.objects.filter(jti=jti).exists():
                return False

        except TokenError:
            return False
        except:
            return False

        return True
    