import graphene
from users import schema as user_schema
from core import schema as core_schema


class Query(user_schema.Query, core_schema.Query, graphene.ObjectType):
    pass


class Mutation(user_schema.Mutation, core_schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
