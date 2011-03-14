from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from avocado.models import Field, Criterion
from core.models import VocabularyCategoryAbstract,VocabularyItemAbstract
from production.models import Diagnosis, DiagnosisCategory, ProcedureType, ProcedureCategory
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.db.models import Q
import json

def children_of_folder(request, vocab_index=None, folder_id=None):
    leaf_model = None
    category_model = None
    
    
    criterion = Criterion.objects.get(id=vocab_index)
    category_model = criterion.conceptfields.select_related('field').order_by('order')[2].field.model
    leaf_model = criterion.conceptfields.select_related('field').order_by('order')[3].field.model
    
    if folder_id:
        folder = category_model.objects.get(id=folder_id)
        folders = folder.get_child_categories()
        leaves = folder.get_child_leaves()
    else:
        folder = None
        folders = category_model.objects.filter(parent_category=None)
        leaves = []
    
    json_object = {}
    json_object['nodes'] = [{"name":node.name,"id":node.id, "child_ref":node.id} for node in folders]
    json_object['nodes'].extend([{"name":leaf.name, 
                                  "id":leaf.id,
                                  "child_ref":"",
                                  "attributes": leaf.display_attributes()
                                  } for leaf in leaves])
    
    if folder:
        path_to_root = folder.path_to_root()
        json_object['path'] = [{"name":node.name, "id":node.id, "child_ref":node.id } for node in path_to_root + [folder]]
    else:
        json_object['path'] = []
    
    return HttpResponse(json.dumps(json_object), mimetype="application/json")
    
def search_nodes(request, vocab_index=None):  
    search_string = request.GET['q']
    if not search_string:
        return HttpResponse(json.dumps([]), mimetype="application/json")
    
    leaf_model = None
    category_model = None
    
    criterion = Criterion.objects.get(id=vocab_index)
    category_model = criterion.conceptfields.select_related('field').order_by('order')[2].field.model
    leaf_model = criterion.conceptfields.select_related('field').order_by('order')[3].field.model
    
    folders = category_model.objects.filter(name__icontains=search_string)
    leaves = leaf_model.objects.filter(name__icontains=search_string)
    
    folders = [  {
                    "path":[{"name":item.name, "id":item.id, "child_ref":item.id } for item in node.path_to_root()],
                    "name": node.name,
                    "id":node.id,
                    "child_ref": node.id,
                    "attributes": {}
                 } for node in folders.all() ]
    #Note: removed a sort order on diagnosisindex__level here, since it wasn't easy to find a simple alternative
    leaves =  [  { 
                    "path":[{"name":item.name, "id":item.id, "child_ref":item.id } for item in node.categories.all()],
                    "name": node.name,
                    "id":node.id,
                    "child_ref": "",
                    "attributes": node.display_attributes()
                 } for node in leaves.all() ]
    
    folders.extend(leaves)
    
    if not folders:
        folders.append({"id" : -1})
    
    return HttpResponse(json.dumps(folders), mimetype="application/json")

def retrieve_node(request, vocab_index=None):
    field_id = request.GET['field']
    instance_id = request.GET['instance']
    
    field = Field.objects.get(id=field_id)
    node = field.model.objects.get(id=instance_id)
    
    if isinstance(node, VocabularyItemAbstract):
        # Request is for a leaf node
        #Note: removed a sort order on diagnosisindex__level here, since it wasn't easy to find a simple alternative
        value = { 
            "path":[{"name":item.name, "id":item.id, "child_ref":item.id } for item in node.categories],
            "name": node.name,
            "id":node.id,
            "child_ref": "",
            "attributes": node.display_attributes
        }        
    else:
        # request is for a category node
        value = {
            "path":[{"name":item.name, "id":item.id, "child_ref":item.id } for item in node.path_to_root()],
            "name": node.name,
            "id":node.id,
            "child_ref": node.id,
            "attributes": {}
        }
        
    return HttpResponse(json.dumps(value), mimetype="application/json")

