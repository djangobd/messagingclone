import graphene
from graphene import relay
import graphql_jwt
from graphql import GraphQLError
from django.contrib.auth import authenticate, login, logout

from backend.utils import clean_input
from backend.enums import SpecialMutationTypes
from backend.users.models import User as UserModel
from .queries import UserNode
from .subscriptions import UserSubscriptions


class Register(relay.ClientIDMutation):
    class Input:
        username = graphene.String(
            required=True, description="User's username")
        password = graphene.String(
            required=True, description="User's password")

    ' Fields '
    user = graphene.Field(UserNode)

    def mutate_and_get_payload(root, info, **input):
        password = input.pop('password')
        cleaned_input = clean_input(input)
        cleaned_input['username'] = cleaned_input.get('username').lower()
        username = cleaned_input.get('username')

        # check if username exists
        if UserModel.objects.filter(username=username).exists():
            raise GraphQLError('Username Taken.')

        new_user = UserModel(username=username)
        new_user.set_password(password)
        new_user.save()

        UserSubscriptions.broadcast(
            group='users-subscription',
            payload={
                "type": SpecialMutationTypes.REGISTER.name,
                "username": username
            }
        )

        return Register(user=new_user)


class Login(graphql_jwt.relay.JSONWebTokenMutation):
    user = graphene.Field(UserNode)

    def resolve(self, info):

        # login(info.context, info.context.user)

        UserSubscriptions.broadcast(
            group='users-subscription',
            payload={
                "type": SpecialMutationTypes.LOGIN.name,
                "username": info.context.user.username
            }
        )

        return Login(user=info.context.user)


# No need for logout.
# class Logout(graphene.Mutation):
#     ' Fields '
#     successful = graphene.Boolean()

#     def mutate(self, info):
#         if info.context.user.is_anonymous:
#             raise GraphQLError('Not logged in.')
#         try:
#             UserSubscriptions.broadcast(
#                 group='users-subscription',
#                 payload={
#                     "type": SpecialMutationTypes.LOGOUT.name,
#                     "username": info.context.user.username
#                 }
#             )
#             logout(info.context)
#         except:
#             raise GraphQLError('Failed to logout')
#         return Logout(successful=True)
