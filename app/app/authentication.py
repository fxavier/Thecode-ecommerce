from datetime import datetime
import jwt
from django.conf import settings


class TokenManager:
    @staticmethod
    def get_token(exp, payload, token_type="access"):
        exp = datetime.now().timestamp() + (exp * 60)

        return jwt.encode(
            {"exp": exp, "type": token_type, **payload},
            settings.SECRET_KEY,
            algorithm="HS256"
        )

    @staticmethod
    def decode_token(token):
        try:
            decoded = jwt.decode(
                token, key=settings.SECRET_KEY, algorithms="HS256")
        except jwt.DecodeError:
            return None

        if datetime.now().timestamp() > decoded["exp"]:
            return None

        return decoded

    @staticmethod
    def get_access(payload):
        return TokenManager.get_token(24*60, payload)

    @staticmethod
    def get_refresh(payload):
        return TokenManager.get_token(7*24*60, payload, "refresh")


class Authentication:
    def __init__(self, request):
        self.request = request

    def authenticate(self):
        decoded_data = self.validate_request()

        if not decoded_data:
            return None

        return self.get_user(decoded_data["user_id"])

    def validate_request(self):
        authorization = self.request.headers.get("Authorization", None)

        if not authorization or not authorization.startswith('Bearer '):
            return None

        token = authorization[7:]
        decoded_data = TokenManager.decode_token(token)

        if not decoded_data:
            return None

        return decoded_data

    @staticmethod
    def get_user(user_id):
        from users.models import User
        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            return None
