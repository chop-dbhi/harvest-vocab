# Harvest-Vocab

Harvest-Vocab provides a set of abstract Django models for making it trivial to query hierarchical data. Most database systems do not have operators supporting [logical conjunction](http://en.wikipedia.org/wiki/Logical_conjunction) _across multiple rows_. The `IN` operator is [disjunctive](http://en.wikipedia.org/wiki/Logical_disjunction) since only one of _operands_ must be true to satisfy the truth. Harvest-Vocab provides support for constructing _conjunctive_ queries (and the negation of that) as well as _exclusive conjunctive_ queries. The query generation are exposed using Django manager methods.

In addition, hooks are for integrating with [Harvest](http://harvest.research.chop.edu) applications including an Avocado Translator which support defines Avocado operators that map to the manager methods for constructing these kinds of queries. This can be used with the [Harvest-Vocab Client](https://github.com/cbmi/harvest-vocab-client) which integrates with the [Cilantro](http://cilantro.harvest.io), the official client of Harvest.

## Install

```bash
pip install harvest-vocab
```

## Problem & Example

A common vocabulary used in healthcare for billing purposes are [ICD9 codes](http://en.wikipedia.org/wiki/List_of_ICD-9_codes). These codes are hierarchical with each level being more specific than the previous. The standard way to store hierarchical data in a relational database is having a _self_-relationship to the parent (the `Patient` model is also defined here for the example).

```python
class Diagnosis(models.Model):
    code = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    parent = models.ForeignKey('self', related_name='children', null=True)


class Patient(models.Model):
    diagnoses = models.ManyToManyField(Diagnosis)
    # other fields...
```

This is perfectly suitable for storing the data, but it falls over when performing queries. An example query could be _"find all the patients who have a diagnosis of ICD9 367 (Disorders of refraction and accommodation)"_. Performing this query is simple.

```python
Patient.objects.filter(diagnoses__code='367')
```

However, this will only find patients who have this _exact_ diagnosis. The problem is that _Disorders of refraction and accommodation_ is a very general _diagnosis_ (it is more of a category) and it is has have two levels of codes underneath it. Any patient that has a more specific diagnosis under 367 (such as code 367.1 for Myopia, i.e. near-sightedness) will be left out of the results. This _naive_ behavior is generally never desired and users expect the descedents of a code to be queried as well. When the depth of the hierarchy is unknown or arbitrary, this kind of query becomes difficult to write (using the Django ORM or raw SQL).

## Solution & Setup

The solution harvest-vocab takes to enable querying arbitrary depth hierarchies is to utilize a _flat index_. That is, an item will have an association to each and every ancestor up to the root. Start by defining the model for the item, the through model for the self relationship and the index.

```python
from vocab.models import AbstractItem, AbstractItemIndex

# Subclass the abstract item model
class Diagnosis(AbstractItem):
    code = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True)

# Define an index of item/parent fields
class DiagnosisIndex(AbstractItemIndex):
    item = models.ForeignKey(Diagnosis, related_name='item_indexes')
    parent = models.ForeignKey(Diagnosis, related_name='parent_indexes')

# Add many-to-many field to associated model
class Patient(models.Model):
    diagnoses = models.ManyToManyField(Diagnosis, through='PatientDiagnosis')
    # other fields...

# Through table between patient and diagnosis, the custom manager provides
# methods for working the custom operators
class PatientDiagnosis(models.Model):
    diagnosis = models.ForeignKey(Diagnosis, null=True)
    patient = models.ForeignKey(Patient, null=True)

    objects = ItemThroughManager('diagnosis', 'patient')
```

After the tables are created in the database, we can build an index by calling:

```python
DiagnosisIndex.objects.index()
```

So now, the same question stated above can be answered this way (using the same condition from above):

```python
diagnosis = Diagnosis.objects.filter(code='367')
# Removes patient ids to be used as a subquery
subquery = PatientDiagnosis.objects.requires_any(diagnosis)
diagnoses = Diagnosis.objects.filter(id__in=subquery)
```

_The above is a bit verbose and the plan is for abstraction to be a bit more transparent._

This utilizes the index and returns all diagnoses that match the condition explictly or any of the descedents of the diagnosis of interest.

## Manager Methods

harvest-vocab defines five methods to support hierarchy-based queries and exposes them via the `ItemThroughManager` class.

- `requires_any(values)` - Corresponds to the `IN` clause (defined for completeness)
- `excludes_any(values)` - Corresponds to the `NOT IN` clause
- `requires_all(values)` - Requires all values to match
- `excludes_all(values)` - Requires all vlaues to _not_ match
- `only(values)` - Matches if the object _only_ contains the specified values

## Harvest Integration

Harvest-Vocab comes bundled with a custom Avocado translator which exposes custom operators corresponding to the above manager methods. The translator must be subclassed and the `through_model` class attribute must be set:

```python
from avocado.query.translators import registry
from vocab.translators import VocabularyTranslator
from myapp.models import PatientDiagnosis

class DiagnosisTranslator(VocabularyTranslator):
    through_model = PatientDiagnosis

registry.register(DiagnosisTranslator)
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


## Resources

Harvest-vocab come with two custom resource classes intended to override the default Serrano values resource for fields. The primary resource exposes a superset of Serrano's `FieldValuesResource` to ensure compatibility. The superset exposes `_links` and `id` properties. The `_links` object enables it to be crawled and used for descendending in the hierarchy if the `children` entry is present (it is not below). Below is an example representation:

```javascript
{
    "_links": {
        "parent": {
            "href": "http://localhost:8000/api/fields/2209/values/"
        },
        "self": {
            "href": "http://localhost:8000/api/fields/2209/values/190/"
        }
    },
    "id": 190,
    "label": "L-LOOP CORRECTED TRANSPOSITION {SL?}",
    "value": 190
}
```
