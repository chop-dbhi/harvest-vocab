from avocado.query.operators import ContainerTypeOperator, registry

class RequireAll(ContainerTypeOperator):
    lookup = 'all'
    join_operator = 'and'
    short_name = 'require all'
    verbose_name = 'requires all of'


class NotAll(RequireAll):
    short_name = 'not all'
    verbose_name = 'can not have'
    negated = True


class Only(RequireAll):
    short_name = 'only be'
    verbose_name = 'can only be'
    lookup = 'only'


registry.register(RequireAll, RequireAll.uid)
registry.register(NotAll, NotAll.uid)
registry.register(Only, Only.uid)
