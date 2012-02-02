from avocado.fields.operators import SequenceOperator

class RequireAll(SequenceOperator):
    join_operator = 'and'
    short_name = 'require all'
    verbose_name = 'requires all of'
    operator = 'all'


class NotAll(RequireAll):
    short_name = 'not all'
    verbose_name = 'can not have'
    negated = True


class Only(RequireAll):
    short_name = 'only be'
    verbose_name = 'can only be'
    operator = 'only'


requireall = RequireAll()
notall = NotAll()
only = Only()
