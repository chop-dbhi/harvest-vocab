require.def(function(){  // $target refers to the div on screen where the concept will be displayed
    var $target = $(document.createElement("div"));
    var prefix = "/vocab";
    
    var breadcrumbsTemplate = [ 
    '<% if (this.path.length===0) {%>',
    '<input type="button" style="visibility:hidden;" id="button-back" class="button-back" value="Back"/><b>Diagnoses</b>',
    '<%} else { %>',
    '<input type="button" id="button-back" class="button-back" value="Back"/><div class="breadcrumb" catid="">Diagnoses</div>',
    '<% } %>',
    '<% for (var index = 0; index < this.path.length; index+=1) {%>',
    '   <% if (index === (this.path.length-1)) {%>',
    '&raquo; <b><%=this.path[index].name%></b>',
    '   <% } else { %>',
    '&raquo; <div class="breadcrumb" catid="<%=this.path[index].child_ref%>"><%=this.path[index].name%></div>',
    '   <% } %>',
    '<% } %>'].join("");
    
    var browseTemplate = [
    '<% if (this.child_ref) { %>',
    '<li class="browser-item cf folder">',
    '<div class="node_item_left">',
    '<input type="button" class="button-add" value = "+"/>',
    '</div>',
    '<div class="node_item_right">',
    '<div style="float:left">',
    '<%=this.name%>',
    '</div>',
    '</div>',
    '</li>',
    '<% } else { %>',
    '<li class="browser-item cf leaf">',
    '<div class="node_item_left">',
    '<input type="button" class="button-add" value = "+"/>',
    '</div>',
    '<div class="node_item_right">',
    '<div>',
    '<%=this.name%>',
    '</div>',
    '<div class="custom_attr">',
    '<% if (this.attributes.icd9) { %>',
    'ICD-9 : <%=this.attributes.icd9%>',
    '<% } %>',
    '<% if (this.attributes.clinibase) { %>',
    'Clinibase ID : <%=this.attributes.clinibase%>',
    '<% } %>',
    '</div>',
    '</div>',
    '</li>',
    '<% } %>'].join('');
    
    var searchResultsTemplate = [
    '<li class="search-item">',
    '<div class="node_item_left">',
    '<% if (this.child_ref) {%>',
    '<input type="button" value="+" class="button-add folder" id="folder<%=this.id%>"/>',
    '<% } else {%>',
    '<input type="button" value="+" class="button-add leaf" id="leaf<%=this.id%>"/>',
    '<%}%>',
    '</div>',
    '<div class="node_item_right">',
    '<div>',
    '<% if (this.child_ref) { %>',
    '<%=this.name%>',
    '<% } else { %>',
    '<%=this.name%>',
    '<% } %>',
    '</div>',
    '<div class="custom_attr">',
    '<% if (this.attributes.icd9) { %>',
    'ICD-9 : <%=this.attributes.icd9%>',
    '<% } %>',
    '<% if (this.attributes.clinibase) { %>',
    'Clinibase ID : <%=this.attributes.clinibase%>',
    '<% } %>',
    '</div>',
    '<div class="node_path">',
    '<% for (index = 0; index < this.path.length; index++){ %>',
    '<div pathid="<%=index%>" class="path_node" style="display:inline;"><%=this.path[index].name%></div>',
    '<% if (index != this.path.length -1){%> &raquo <%}%>',
    '<% } %>',
    '</div>',
    '</div>',
    '</li>',
    '<div class="floatclear"></div>',
    ].join('');
    
    var vocabBrowserTemplate = [
    ' <div class="toolbar header tabs">',
    '    <a id ="showBrowse" class="tab tab-selected" href="#browseTab">Browse Diagnoses</a>',
    '    <a class="tab" href="#searchTab">Search Diagnoses</a>',
    ' </div>',
    ' <div class="content">',
    '     <div id="browseTab">',
    '         <div id="nav"></div>',
    '         <ul id="browser_list" class="browser-section cf"></ul>',
    '     </div>',
    '     <div id="searchTab">',
    '         <form method="get" action="/plugins/vb/search">',
    '             <input type="text" class="searchIdle" id="vocab_search" name="term" size="50"/>',
    '         </form>',
    '         <div>',
    '         <ul id="results" class="browser-section">',
    '         </ul>',
    '         </div>',
    '     </div>',
    '     <hr />',
    '     <p>Patient has been diagnosed with:</p>',
    '     <div id="selected"><ul class="browser-section" id="members"></ul></div>',
    '</div>'
    ].join('');
    
    // Make sure the currently displayed nodes are correctly colored
    // as to whether they are selected for the query.
    var refreshBrowser = function(){
        $target.find("#browser_list li").removeClass("added");
        $target.find("#browser_list li input").attr("disabled","");
        
        $target.find("#results li").removeClass("added");
        $target.find("#results li input").attr("disabled","");
        
        
        $target.find("#browser_list li").add("#results li").each(function(index, element){
           element = $(element);
           if (element.data('node').child_ref){
               if ($.inArray(element.data('node').id, ds[folder]) !=-1){
                   element.addClass("added");
                   element.find("input").attr("disabled","disabled");
               }
    
           } else{
               if ($.inArray(element.data('node').id, ds[leaf]) !=-1){
                    element.addClass("added");
                    element.find("input").attr("disabled","disabled");
               }
           }
        });
    };
    
    // Remove a previously selected node..
    var removeNode = function($node){
        var index;
        if ($node.data("node").child_ref){
            index = $.inArray($node.data("node").id,ds[folder]);
            ds[folder].splice(index,1);
            $target.trigger("ElementChangedEvent", [{name:folder, value:ds[folder]}]);
        }else{
            index = $.inArray($node.data("node").id,ds[leaf]);
            ds[leaf].splice(index,1);
            $target.trigger("ElementChangedEvent", [{name:leaf, value:ds[leaf]}]);
        }
        $node.remove();
        refreshBrowser();
    };



    // This function will use the "selected" object to create
    // the tree structure that the Avocado state framework expects
    var addNode = function(node){
       var isFolder = false;
       if (node.child_ref){
           isFolder = true;
       }
       var $new_node = $('<li class="selected-item"><input type="button" value="-" class="button-remove"/>'+node.name+'</li>');
       $new_node.find("input").click(function(){
          $(this).trigger("removeItemEvent"); 
       });
       
       $new_node.data('node',node);
       $new_node.bind("removeItemEvent", function(){
            removeNode($(this));
            return false;
       });
       
       if (isFolder){
           if ($.inArray(node.id,ds[folder])!=-1){
               return;
           }
           $target.find("#members").prepend($new_node);
           ds[folder].unshift(node.id);
           $target.trigger("ElementChangedEvent", [{name:folder, value:ds[folder]}]);
       }else{
            if ($.inArray(node.id, ds[leaf])!=-1){
                  return;
            }
            $target.find("#members").prepend($new_node);
            ds[leaf].unshift(node.id);
            $target.trigger("ElementChangedEvent", [{name:leaf, value:ds[leaf]}]);
       }
       
    };
    
    var reloadBrowser = function(category){
       $.get(prefix+'/browse/'+category.replace("#",""), function(data){
               data = $.parseJSON(data);
               $target.find("#browser_list").empty();
               for (var index = 0; index < data.nodes.length; index++) {
                   var $li = $($.jqote(browseTemplate,data.nodes[index]));
                   $li.data("node",data.nodes[index]);
                   
                   // Check to see if the item has been selected
                   if (data.nodes[index].child_ref){
                       if ($.inArray(data.nodes[index].id, ds[folder])!=-1){
                           $li.addClass("added");
                       }
                   }else{
                        if ($.inArray(data.nodes[index].id, ds[leaf])!=-1){
                              $li.addClass("added");
                        }
                   }
                   $("#browser_list").append($li);
                   $li.bind("addItemEvent", function(evt){
                       addNode($(this).data("node"));
                       $(this).addClass("added");
                       return false;
                   });
                   $li.bind("descendEvent", function(){
                       reloadBrowser("#"+$(this).data("node").child_ref);
                       return false;
                   });
                   $li.filter(".folder").click(function(){
                       $(this).trigger("descendEvent");
                   });
                   
                   $li.filter(".folder").hover(function(){
                      $(this).addClass("list_on"); 
                   }, function(){
                      
                      $(this).removeClass("list_on");
                   });
               }
               $target.find('.button-add').click(function(evt){
                   $(this).trigger("addItemEvent");
                   $(this).attr("disabled", "disabled");
                   return false;
               });
               
               $target.find('.button-descend').click(function(evt){
                    $(this).trigger("descendEvent");
                    return false;
               });
               
               $target.find('#nav').empty().html($.jqote(breadcrumbsTemplate,data));
               $target.find('#nav div.breadcrumb').bind("click", function(){
                   reloadBrowser("#"+$(this).attr("catid"));
                   return false;
               });
               $target.find('#nav div.breadcrumb').hover(function(){
                   $(this).addClass("hovercrumbs");
                   
               }, function(){
                   $(this).removeClass("hovercrumbs");
               });

               $target.find('#button-back').click(function(evt){
                   if (data.path.length == 1) {
                       reloadBrowser("#");
                   }else{ 
                       reloadBrowser("#"+data.path[data.path.length-2].child_ref);
                   }
               });
       }, "json", function(settings){
           if (settings.url === (prefix+"/browse/")) {
              return $.parseJSON($.ajax({ type: "GET", url: "/static/fixtures/root.json", async: false, dataType:"json" }).responseText); 
           } else {
              return $.parseJSON($.ajax({ type: "GET", url: "/static/fixtures/notroot.json", async: false, dataType:"json" }).responseText);
           }
       }); 
    };
    
    var ds = {};
    var that = {};
    var leaf;
    var folder;
    var execute = function($content_div, concept_id, data){
        
        leaf = concept_id+"_"+data.leaf;
        folder = concept_id+"_"+data.folder;
        ds[leaf] = [];
        ds[folder] = [];
        
        // We need to inject our templates into the application, at this point we are assuming that our jqote templates
        // are being delivered by the django template system
        $target.append($.jqote(vocabBrowserTemplate,{browsertype:"Diagnoses"}));
        $target.addClass("container cf");
        
        var $receiver = $target.find("#results");
        var $input = $target.find("#vocab_search");
        
        // enable tabs, we use a very barebones tabs implementation
        // the core code only adds the appropriate classes to selected
        // and non-selected tabs, represented by <a> elements.
        $target.find('.tabs').tabs(false, function (evt, $tab){
            refreshBrowser();
            var $siblings = $tab.siblings('.tab');
            $target.find($tab.attr('hash')).show();
            $siblings.each(function(index, neighbor){
                $target.find($(neighbor).attr('hash')).hide();
            });
        });
        
        // Setup the browser
        reloadBrowser("");
        
        // Setup the search 
        $target.find("#vocab_search").autocomplete2({
            fixture:"/static/fixtures/search_results.json",
            start: function() {
                $input.removeClass("searchIdle").addClass("searchAjax");
            },
            success: function(query, resp) {
                $input.removeClass("searchAjax").addClass("searchIdle");
                $receiver.empty();
                resp = $.parseJSON(resp);
                $.each(resp, function(index, value){
                    if (value.id === -1) {
                          $receiver.append("<div>No matches.</div>");
                          return;
                    }
                    var $li=$($.jqote(searchResultsTemplate,value));
                    $li.data("node",value);
                    $li.find(".path_node").hover(function(){$(this).addClass("over");},
                                                 function(){$(this).removeClass("over");});
                    $li.find(".path_node").each(function(index,element){

                       $(element).click(function(evt){
                           reloadBrowser("#" + value.path[parseInt($(evt.target).attr("pathid"))].id);
                           $("#showBrowse").trigger("click");
                           return false;
                       });
                        
                    });
                    
                    if (value.child_ref){
                         if ($.inArray(value.id, ds[folder])!=-1){
                             $li.addClass("added");
                         }
                    }else{
                          if ($.inArray(value.id,ds[leaf])!=-1){
                            $li.addClass("added");
                          }
                    }
                    
                    $li.filter(".folder").hover(function(){
                       $(this).addClass("list_on"); 
                    }, function(){
                       $(this).removeClass("list_on");
                    });
                    $li.bind("addItemEvent",function(){
                        addNode($(this).data("node"));
                        $(this).addClass("added");
                        return false;
                    });
                    $li.hover(function(){
                         $(this).addClass("list_on"); 
                      }, function(){
                         
                         $(this).removeClass("list_on");
                      });
                    $li.click(function(){
                       var info = $(this).data("node");
                       if (info.child_ref){
                           reloadBrowser("#"+info.id);
                       }else if (info.path){
                           reloadBrowser("#"+info.path[info.path.length-1].id);
                       }else{
                           reloadBrowser("");
                       }
                    $("#showBrowse").trigger("click");
                       return false;
                    });
                    
                    $receiver.append($li);
                });
                
                
                $receiver.find(".button-add").click(function(){
                    $(this).trigger("addItemEvent");
                    $(this).attr("disabled", "disabled");
                    return false;
                });
            },
            error: function(){
                $input.removeClass("searchAjax").addClass("searchIdle");
            }
        }, 'Search criteria...');//helptext('Search criteria...');
        
        $target.bind("UpdateDSEvent", function(evt,new_ds){
            if (!$.isEmptyObject(new_ds)){
                ds = new_ds;
                reloadBrowser();
            } 
        });
        
       $target.bind("UpdateQueryButtonClicked", function(event){
              $target.trigger("ConstructQueryEvent");
       });
       
       $content_div.trigger("ViewReadyEvent", [$target]);
 };
 that.execute = execute;
 return that;
});