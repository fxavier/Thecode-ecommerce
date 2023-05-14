from .permissions import resolve_paginated


class CustomAuthMiddleware:
    def resolve(self, next, root, info, **kwargs):
        """
        Middleware to authenticate the user.
        """
        info.context.user = self.authorize_user(info)
        return next(root, info, **kwargs)

    @staticmethod
    def authorize_user(info):
        """
        Authorizes the user by calling the authenticate method
        of the Authentication class.
        """
        from .authentication import Authentication
        auth = Authentication(info.context)
        return auth.authenticate()


class CustomPaginationMiddleware:
    def resolve(self, next, root, info, **kwargs):
        """
        Middleware to handle pagination in GraphQL queries.
        """
        is_paginated = self.is_paginated(info)

        if is_paginated:
            page = kwargs.pop("page", 1)
            return resolve_paginated(
                next(root, info, **kwargs).value, info, page
            )

        return next(root, info, **kwargs)

    @staticmethod
    def is_paginated(info):
        """
        Checks if the GraphQL query is paginated.
        """
        try:
            paginated_type_suffix = info.return_type.name[-9:]
            return paginated_type_suffix == "Paginated"
        except Exception:
            return False
