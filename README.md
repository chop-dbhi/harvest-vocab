# Harvest-Vocab

Harvest-Vocab provides a set of abstract Django models for making it trivial to query hierarchical data. Most database systems do not have operators supporting [logical conjunction](http://en.wikipedia.org/wiki/Logical_conjunction) _across multiple rows_. The `IN` operator is [disjunctive](http://en.wikipedia.org/wiki/Logical_disjunction) since only one of _operands_ must be true to satisfy the truth. Harvest-Vocab provides support for constructing _conjunctive_ queries (and the negation of that) as well as _exclusive conjunctive_ queries. The query generation are exposed using Django manager methods.

In addition, hooks are for integrating with [Harvest](http://harvest.research.chop.edu) applications including an Avocado Translator which support defines Avocado operators that map to the manager methods for constructing these kinds of queries. This can be used with the [Harvest-Vocab Client](https://github.com/cbmi/harvest-vocab-client) which integrates with the [Cilantro](http://cilantro.harvest.io), the official client of Harvest.

## Introduction

Harvest-Vocab provides abstract models for defining vocabulary-like models and building a corresponding index for hierarchical data.

For example, this is how you could define models for storing [ICD9 codes](http://en.wikipedia.org/wiki/List_of_ICD-9_codes):

```python
from vocab.models import AbstractItem

class Diagnosis(AbstractItem):
    code = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    parent = models.ForeignKey('self', related_name='children')
```

ICD9 codes are hierachical therefore when I ask the questions, _"Give me all the patients who have a diagnosis of ICD9 367 (Disorders of refraction and accommodation)"_, then this should not only query 367, but all descendent diagnoses as well (which includes another 2 levels).

This kind of query becomes difficult to write (using the Django ORM or raw SQL) since only the direct parent of the a particular diagnosis is accessible for a given diagnosis, thus the query would look like this.

```python
from django.db.models import Q

condition = Q(code='367') | Q(parent__code='367')
Diagnosis.objects.filter(condition)
```

The obvious problem here is that any diagnoses 2+ levels down from '367' are not included.

### Flat Index

To alleviate this issue, we build a flat index for all levels of the hierarchy. Define it like this:

```python
from vocab.models import AbstractItemIndex

class DiagnosisIndex(AbstractItemIndex):
    item = models.ForeignKey(Diagnosis, related_name='item_indexes')
    parent = models.ForeignKey(Diagnosis, related_name='parent_indexes')


DiagnosisIndex.objects.index()
```

The last line builds a flat index of the hierarchy which alleviates the depth issue. So now, the same question stated above can be answered this way (using the same condition from above):

```python
subquery = DiagnosisIndex.objects.filter(condition)
diagnoses = Diagnosis.objects.filter(id__in=subquery)
```

This utilizes the index and returns all diagnoses that match the condition explictly or are descedents of the ICD9 code of interest.

## Operators

The only native multi-row operator SQL supports is `IN`. A row will be returned if it matches _any_ of the values in the `IN` tuple. However there is no native operator for requiring _all_, _not all_ and _only_.

Harvest-Vocab defines four operators to support these kinds of queries and exposes them via the `ItemThroughManager` class.

- `requires_any(values)` - Corresponds to the `IN` clause (defined for completeness)
- `excludes_any(values)` - Corresponds to the `NOT IN` clause
- `requires_all(values)` - Requires all values to match
- `excludes_all(values)` - Requires all vlaues to _not_ match
- `only(values)` - Matches if the object _only_ contains the specified values

## Get Started

### Install

```bash
pip install harvest-vocab
```

### Setup

#### Define the Models

```python
from vocab.models import AbstractItem

# Subclass AbstractItem with your model of interest. Add a ManyToManyField
# to the target object this hierarchy is related to.
class Diagnosis(AbstractItem):
    patients = models.ManyToManyField(Patient, through='PatientDiagnosis')
    ...

# Create a many-to-many through model with the correct foreign keys
class PatientDiagnosis(models.Model):
    diagnosis = models.ForeignKey(Diagnosis)
    patient = models.ForeignKey(Patient)
    ...

    # pass the field names of the term (diagnosis) and related object (patient)
    objects = ItemThroughManager('diagnosis', 'patient')

# Create the index model. Note the foreign keys must be named exactly
# as show below including the related_name fields
class DiagnosisIndex(AbstractItemIndex):
    item = models.ForeignKey(Diagnosis, related_name='item_indexes')
    parent = models.ForeignKey(Diagnosis, related_name='parent_indexes')
```

#### Build the Index

This builds a simple item/ancestor index which enables querying the underlying data as a flat structure. **Note: the index must be rebuild every time the data changes in target model, e.g. `Diagnosis` in this case.**

```python
>>> DiagnosisIndex.objects.index()
```

Now that the index has been built the `PatientDiagnosis` manager methods can now be used.

### Harvest Integration

Harvest-Vocab comes bundled with a custom Avocado translator which exposes custom operators corresponding to the above manager methods. The translator must be subclassed and the `through_model` class attribute must be set:

```python
from avocado import translators
from vocab.translators import VocabularyTranslator
from myapp.models import PatientDiagnosis

class DiagnosisTranslator(VocabularyTranslator):
    through_model = PatientDiagnosis

translators.register(DiagnosisTranslator)
```

To support the [harvest-vocab-client](https://github.com/cbmi/harvest-vocab-client/), endpoints must be defined for the client components to query. Include the `vocab.urls` in the `ROOT_URLCONF` patterns:

```python
from django.conf.urls import url, reverse, patterns

urlpatterns = patterns('',
    # Other url patterns...

    url(r'^vocab/', include('vocab.urls')),
)
```

In addition, define the `VOCAB_FIELDS` setting which is a list/tuple of Avocado field IDs that are supported.

## Implementation

The custom operators are implemented using SQL `CASE` statements. An example output for an _requires all_ query would look something like this. Although this query may look daunting, the important bits are only the summed `CASE` statements combined with the `WHERE` condition for those expressions, e.g. `sc1` and `sc5`. To handle the hierarchical nature of the data (in this case [ICD9 codes](http://en.wikipedia.org/wiki/List_of_ICD-9_codes), the index table is being used which enables matching against the item itself (via `"item_id" = 1`) or a descendent of the item (via `"parent_id" = 1`).

```sql
SELECT DISTINCT "core_person"."id",
FROM "core_person",
     "core_subject"
WHERE "core_person"."id" = "core_subject"."person_id"
    AND "core_subject"."id" IN (
        SELECT "patient_id"
        FROM (
            SELECT "patient_id",
            SUM(
                CASE
                    WHEN "core_diagnosisindex"."item_id" = 1 THEN 1
                    WHEN "core_diagnosisindex"."parent_id" = 1 THEN 1
                    ELSE 0
                END
            ) AS "sc1",
            SUM(
                CASE
                    WHEN "core_diagnosisindex"."item_id" = 5 THEN 1
                    WHEN "core_diagnosisindex"."parent_id" = 5 THEN 1
                    ELSE 0
                END
            ) AS "sc5",
            FROM "core_patientdiagnosis"
                INNER JOIN "core_diagnosisindex" ON ("core_patientdiagnosis"."diagnosis_id" = "core_diagnosisindex"."item_id" )
           GROUP  BY "patient_id"
        ) AS T
        WHERE  "sc1" > 0
            AND "sc5" > 0
    )
```

The difference between operators are simply the whether the condition is negated and how many are required to match.

- **requires all** - An item must match at least once for all items
- **requires any** - An item must match at least once for any items (equivalent to the `IN` clause)
- **excludes all** - An item must not match for all items
- **excludes any** - An item must not match for any items (equivalent to the `NOT IN` clause)
- **only** - An item must match only once for all items and nothing else
