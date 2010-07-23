from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from production.models import (Diagnosis, DiagnosisCategory)
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.db.models import Q
import json


def children_of_folder(request, folder_id=None):
    if folder_id:
        folder = DiagnosisCategory.objects.get(id=folder_id)
        folders = folder.diagnosiscategory_set.all()
        leaves = folder.diagnoses.filter(diagnosisindex__level=1)
    else:
        folder = None
        folders = DiagnosisCategory.objects.filter(level=1)
        leaves = []
    
    json_object = {}
    json_object['nodes'] = [{"name":node.name,"id":node.id, "child_ref":node.id} for node in folders]
    json_object['nodes'].extend([{"name":leaf.name, 
                                  "id":leaf.id,
                                  "child_ref":"",
                                  "attributes": { "icd9": leaf.icd9 if leaf.icd9 and leaf.icd9 != "None" else None,
                                                  "clinibase": (leaf.datasource.id_1 if leaf.datasource and leaf.datasource.field_1 == "diagnosis.id"
                                                                                    and leaf.datasource.source == "Clinibase" 
                                                                                    else None)
                                                }
                                  } for leaf in leaves])
    
    if folder:
        path_to_root = folder.path_to_root()
        json_object['path'] = [{"name":node.name, "id":node.id, "child_ref":node.id } for node in path_to_root + [folder]]
    else:
        json_object['path'] = []
    
    return HttpResponse(json.dumps(json_object), mimetype="application/json")
    
def search_nodes(request):  
    search_string = request.GET['q']
    if not search_string:
        return HttpResponse(json.dumps([]), mimetype="application/json")
    
    folders = DiagnosisCategory.objects.filter(name__icontains=search_string)
    leaves = Diagnosis.objects.filter(name__icontains=search_string)
    
    folders = [  {
                    "path":[{"name":item.name, "id":item.id, "child_ref":item.id } for item in node.path_to_root()],
                    "name": node.name,
                    "id":node.id,
                    "child_ref": node.id,
                    "attributes": {}
                 } for node in folders ]

    leaves =  [  { 
                    "path":[{"name":item.name, "id":item.id, "child_ref":item.id } for item in node.categories.order_by("diagnosisindex__level").reverse()],
                    "name": node.name,
                    "id":node.id,
                    "child_ref": "",
                    "attributes": { "icd9": node.icd9 if node.icd9 and node.icd9 != "None" else None,
                                    "clinibase": (node.datasource.id_1 if node.datasource and node.datasource.field_1 == "diagnosis.id"
                                                                      and node.datasource.source == "Clinibase" 
                                                                      else None)
                                        
                                 }
                 } for node in leaves ]
    
    folders.extend(leaves)
    
    if not folders:
        folders.append({"id" : -1})
    
    return HttpResponse(json.dumps(folders), mimetype="application/json")


def dependencies(request):
    
    depends = {
        "views": [
            {
                "title": "Vocabulary Browser",
                "datatype": "diagnoses",
                "type": "vocabulary",
                "id": "graphical",
                "execute": "/static/js/vocabulary.js",
                "css": "/static/css/vocabulary.css"
            } 
        ]
    }
    
    return HttpResponse(json.dumps(depends),mimetype="application/json")