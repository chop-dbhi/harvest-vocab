from django.db import models

class VocabularyIndexAbstract(models.Model):
    """This is a generic flattened index for vocabs. It may replace the main
    model eventually"""
    
    level = models.IntegerField(blank=True, null=True)
    is_terminal = models.BooleanField(default=False)
    
    def __unicode__(self):
        return u'%s' % self.id

    class Meta:
        abstract = True
    
class VocabularyCategoryAbstract(models.Model):
    """Vocab categories are all essentially the same, so inherit from this for specific cases"""
    name  = models.TextField(max_length=255)
    #level = models.IntegerField()
    
    
    def path_to_root(self):
        """Returns a list of the parent categories to help with navigation"""
        parents = []
        parent_category = self
        while parent_category.parent_category != None:
            parents.append(parent_category.parent_category)
            parent_category = parent_category.parent_category
        """Reorder so the lowest index is the highest (lest-specific) category"""
        parents.reverse()
        return parents
   
    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        abstract = True

class VocabularyItemAbstract(models.Model):
    """Vocab items are all essentially the same, so inherit from this for specifc cases"""
    
    def path_to_root(self):
        pass
    
    def __unicode__(self):
            return u'%s' % self.name
    
    class Meta:
        abstract = True


class DiagnosisCategoryAbstract(VocabularyCategoryAbstract):
    """Abstract model to define the hierarchy of categories for diagnoses"""
    
    class Meta:
        abstract = True

class DiagnosisIndexAbstract(VocabularyIndexAbstract):
    class Meta:
        abstract = True

class ProcedureIndexAbstract(VocabularyIndexAbstract):
    class Meta:
        abstract = True

class DiagnosisAbstract(VocabularyItemAbstract):
    """Contains a list of diagnoses organized into categories"""
    
    name = models.TextField(max_length=255)
    icd9 = models.TextField(null=True)
    
    class Meta:
        abstract = True

class ProcedureCategoryAbstract(VocabularyCategoryAbstract):
    """Abstract model for the hierarchy of procedures"""
    class Meta:
        abstract = True

class ProcedureTypeAbstract(models.Model):
    """Type of procedure based on cath lab hierarchy"""
    name = models.CharField(max_length=255)
    cpt = models.CharField(max_length=20, null=True)
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return u'%s' % self.name

class Diagnosis(DiagnosisAbstract):
    #category = models.ForeignKey('DiagnosisCategory')
    categories = models.ManyToManyField('DiagnosisCategory', 
                through='DiagnosisIndex')

    class Meta:
        app_label = u'production'
        verbose_name = u'Diagnosis'
        verbose_name_plural = u'Diagnoses'

class DiagnosisCategory(DiagnosisCategoryAbstract):
    parent_category = models.ForeignKey('self', null=True)
    diagnoses = models.ManyToManyField(Diagnosis, through='DiagnosisIndex')


    class Meta:
        app_label = u'production'
        verbose_name = u'Diagnosis Category'
        verbose_name_plural = u'Diagnosis Categories'

class DiagnosisIndex(DiagnosisIndexAbstract):

    diagnosis = models.ForeignKey(Diagnosis)
    category = models.ForeignKey(DiagnosisCategory)

    class Meta:
        app_label = u'production'
        verbose_name = u'Diagnosis Index'
        verbose_name_plural = u'Diagnosis Index'


class ProcedureCategory(ProcedureCategoryAbstract):
    parent_category = models.ForeignKey('self', null=True)
    procedures = models.ManyToManyField('ProcedureType',
        through = 'ProcedureIndex')

    class Meta:
        app_label = u'production'
        verbose_name = u'Procedure Category'
        verbose_name_plural = u'Procedure Categories'

class ProcedureType(ProcedureTypeAbstract):
    #category = models.ForeignKey(ProcedureCategory)
    categories = models.ManyToManyField('ProcedureCategory',
        through = 'ProcedureIndex')

    class Meta:
        app_label = u'production'
        verbose_name = u'Procedure Type'
        verbose_name_plural = u'Procedure Types'

class ProcedureIndex(ProcedureIndexAbstract):
    procedure = models.ForeignKey(ProcedureType)
    category = models.ForeignKey(ProcedureCategory)

    class Meta:
        app_label = u'production'
        verbose_name = u'Diagnosis Index'
        verbose_name_plural = u'Diagnosis Index'

