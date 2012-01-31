from avocado.fields.operators import SequenceOperator, Exact, NotExact

class RequireAll(SequenceOperator):
    short_name = 'require all'
    verbose_name = 'requires all of'
    operator = 'all'

    def text(self, value):
        value = map(self.stringify, value)
        if len(value) == 1:
            if self.negated:
                return '%s %s' % (NotExact.verbose_name, value[0])
            return '%s %s' % (Exact.verbose_name, value[0])
        value = ', '.join(value[:-1]) + ' and %s' % value[-1]
        return '%s %s' % (self.verbose_name, value)


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
