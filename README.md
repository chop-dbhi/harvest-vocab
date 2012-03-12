Harvest-Vocab
=============

Quick Setup
-----------
**1. Setup the models**
```python
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

    # pass the field names of the term and related object
    objects = ItemThroughManager('diagnosis', 'patient')

# Create the index model. Note the foreign keys must be named exactly
# as show below including the related_name fields
class DiagnosisIndex(AbstractItemIndex):
    item = models.ForeignKey(Diagnosis, related_name='item_indexes')
    parent = models.ForeignKey(Diagnosis, related_name='parent_indexes')
```

**2. Build Index**
```python
>>> DiagnosisIndex.objects.index()
```

**3. Use Pivot Queries**
```python
>>> diagnoses = Diagnosis.objects.filter(pk__in=[1, 2])
>>> patient_ids = PatientDiagnosis.objects.requires_all(diagnoses)
>>> patients = Patient.objects.filter(pk__in=patient_ids)
```

Introduction
------------
Harvest-Vocab provides abstract models for defining vocabulary-like models
and building a corresponding index for hierarchical _self-related_ data.

For example, this is how you could define models for storing ICD9 codes:

```python
from vocab.models import AbstractItem, AbstractItemIndex

class Diagnosis(AbstractItem):
    description = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    parent = models.ForeignKey('self', related_name='children')
```

ICD9 codes are hierachical therefore when I ask the questions, _"Give me all
the patients who have a diagnosis in ICD9 367 (Disorders of refraction and
accommodation)"_, then this should not only query 367, but all descendent
diagnoses as well (which includes another 2 levels).

This kind of query becomes difficult to write since you only have access to
the direct parent of the a particular diagnosis, thus the query would look like
this.

```python
from django.db.models import Q
Diagnosis.objects.filter(Q(code='367') | Q(parent__code='367'))
```

The obvious problem here is that any diagnoses 2+ levels down from '367' are
not included.

Create A Flat Index
-------------------
To alleviate this issue, an ``AbstractItemIndex`` subclass can be defined
which will build a flat index for an ``AbstractItem`` subclass. Simply define
it like this:

```python
class DiagnosisIndex(AbstractItemIndex):
    item = models.ForeignKey(Diagnosis, related_name='item_indexes')
    parent = models.ForeignKey(Diagnosis, related_name='parent_indexes')

# builds the index for Diagnosis
DiagnosisIndex.objects.index()
```

The last line generates a flat index of the hierarchy which alleviates the
_unknown_ depth issue. So now, the same question stated above can be answered
this way:

```python
# either the item has this code or one of it's parents has this code
condition = Q(item__code='367') | Q(parent__code='367')
item_ids = DiagnosisIndex.objects.filter(condition).values_list('item__id', flat=True)
diagnoses = Diagnosis.objects.filter(id__in=item_ids)
```

Harvest Integration
-------------------
Harvest-Vocab comes bundled with a custom Avocado translator. Subclass the
translator `vocab.translate.VocabularyTranslator` and set the `through_model`
class attribute:

```python
from avocado.fields import translate
from vocab.translate import VocabularyTranslator
from myapp.models import PatientDiagnosis

@translate.register
class DiagnosisTranslator(VocabularyTranslator):
    through_model = PatientDiagnosis
```
