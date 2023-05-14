from users.models import User
from graphql import GraphQLError
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import authenticate
from datetime import datetime
from app.authentication import TokenManager
from app.permissions import is_authenticated, paginate


class UserType(DjangoObjectType):
    class Meta:
        model = User


class Query(graphene.ObjectType):
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    users = graphene.List(UserType)
    me = graphene.Field(UserType)

    def resolve_user(self, info, id):
        return User.objects.get(id=id)

    def resolve_users(self, info):
        return User.objects.all()

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Not logged in!')

        return user


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        name = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, name, password, email):
        user = User(
            name=name,
            email=email
        )
        user.set_password(password)
        user.save()
        return CreateUser(user=user)


class LoginUser(graphene.Mutation):
    access = graphene.String()
    refresh = graphene.String()
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        user = authenticate(username=email, password=password)

        if not user:
            raise Exception("invalid credentials")

        user.last_login = datetime.now()
        user.save()

        access = TokenManager.get_access({"user_id": user.id})
        refresh = TokenManager.get_refresh({"user_id": user.id})

        return LoginUser(
            access=access,
            refresh=refresh,
            user=user
        )


class GetAccess(graphene.Mutation):
    access = graphene.String()

    class Arguments:
        refresh = graphene.String(required=True)

    def mutate(self, info, refresh):
        token = TokenManager.decode_token(refresh)

        if not token or token["type"] != "refresh":
            raise Exception("Invalid token or has expired")

        access = TokenManager.get_access({"user_id": token["user_id"]})

        return GetAccess(
            access=access
        )


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()
    get_access = GetAccess.Field()
