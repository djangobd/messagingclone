import graphene
from graphene import relay
from graphql import GraphQLError
from django.contrib.auth import authenticate, login, logout
from graphql_jwt.decorators import login_required

from backend.utils import clean_input
from backend.users.models import User as UserModel
from .queries import UserNode


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

        new_user = UserModel(username=cleaned_input['username'])
        new_user.set_password(password)
        new_user.save()

        return Register(user=new_user)


class Login(relay.ClientIDMutation):
    class Input:
        username = graphene.String(
            required=True, description="User's username")
        password = graphene.String(
            required=True, description="User's password")

    ' Fields '
    user = graphene.Field(UserNode)

    def mutate_and_get_payload(root, info, **input):
        input['username'] = input.get('username').strip()
        user = authenticate(**input)

        if user is None:
            raise GraphQLError(
                'Unable to authenticate user. Either the account is disabled or the entered credentials are wro    ng.')

        login(info.context, user)
        return Login(user=user)


class Logout(graphene.Mutation):
    ' Fields '
    successful = graphene.Boolean()

    @login_required
    def mutate(self, info):
        try:
            logout(info.context)
        except:
            raise GraphQLError('Failed to logout')
        return Logout(successful=True)
