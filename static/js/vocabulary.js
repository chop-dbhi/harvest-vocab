// Initiate the main screen of the vocabulary browser
// The first thing to be displayed is always the root category
(function(){  // $target refers to the div on screen where the concept will be displayed
    var $target = $(document.createElement("div"));
    
    var prefix = "/plugins/vb";
    var selected = { leaves:[], folders:[]};
    
    // This function will use the "selected" object to create
    // the tree structure that the Avocado state framework expects
    
   
    
    var addNode = function(node){
       var folder = false;
       if (node.child_ref){
           folder = true;
       }
       if (folder){
           if ($.inArray(node.id,selected.folders)!=-1){
               return;
           }
           $target.find("#members").prepend("<li class='selected-item'>"+node.name+"</li>");
           selected.folders.unshift(node.id);
       }else{
            if ($.inArray(node.id, selected.leaves)!=-1){
                  return;
            }
            $target.find("#members").prepend("<li class='selected-item'>"+node.name+"</li>");
            selected.leaves.unshift(node.id);
       }
    };
    
    var reloadBrowser = function(category){
       $.get(prefix+'/browse/'+category.replace("#",""), function(data){
               data = $.parseJSON(data);
               $target.find("#browser_list").empty();
               for (var index = 0; index < data.nodes.length; index++) {
                   var $li = $($("#browse-template").jqote(data.nodes[index]));
                   $li.data("node",data.nodes[index]);
                   
                   
                   //Check to see if the item has been selected
                   if (data.nodes[index].child_ref){
                       if ($.inArray(data.nodes[index].id, selected.folders)!=-1){
                           $li.addClass("added");
                       }
                   }else{
                        if ($.inArray(data.nodes[index].id, selected.leaves)!=-1){
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
               
               $target.find('#nav').empty().html($("#breadcrumbs-template").jqote(data));
               $target.find('#nav div.breadcrumb').bind("click", function(){
                   reloadBrowser("#"+$(this).attr("catid"));
                   return false;
               });
               $target.find('#nav div.breadcrumb').hover(function(){
                   $(this).addClass("hovercrumbs");
                   
               }, function(){
                   $(this).removeClass("hovercrumbs");
               });
               
               
               $target.find('#button-back').button({text:false,icons:{primary:'ui-icon-arrowthick-1-w'}});
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
    
    // We need to inject our templates into the application, at this point we are assuming that our jqote templates
    // are being delivered by the django template system
    $target.append($("#vocabulary_browser").jqote({browsertype:"Diagnoses"}));
    $target.addClass("container cf");
    
    var $receiver = $target.find("#results");
    var $input = $target.find("#vocab_search");
    
    // enable tabs, we use a very barebones tabs implementation
    // the core code only adds the appropriate classes to selected
    // and non-selected tabs, represented by <a> elements.
    $target.find('.tabs').tabs(false, function (evt, $tab){
        var $siblings = $tab.siblings('.tab');
        $($tab.attr('hash')).show();
        $siblings.each(function(index, neighbor){
            $($(neighbor).attr('hash')).hide();
        });
    });
    // Setup the browser
    reloadBrowser("");
    
    // Hijacking all links that contain an href
    $target.find('a[href]:not(.tab)').live("click", function(){
        reloadBrowser(this.hash);
        $("#showBrowse").trigger("click");
        return false;
    });
    
    
    // Setup the search 
    $target.find("#vocab_search").autocomplete({
        fixture:"/static/fixtures/search_results.json",
        start: function() {
            $input.removeClass("searchIdle").addClass("searchAjax");
        },
        success: function(query, resp) {
            $input.removeClass("searchAjax").addClass("searchIdle");
            $receiver.empty();
            $.each(resp, function(index, value){
                if (value.id === -1) {
                      $receiver.append("<div>No matches.</div>");
                      return;
                }
                var $li=$($("#results_template").jqote(value));
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
                     if ($.inArray(value.id, selected.folders)!=-1){
                         $li.addClass("added");
                     }
                }else{
                      if ($.inArray(value.id, selected.leaves)!=-1){
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
            //$receiver.find(".button-add").button({text:false,icons:{primary:'ui-icon-plusthick'}});
            $receiver.find(".button-add").click(function(){
                $(this).trigger("addItemEvent");
                return false;
            });
        },
        error: function(){
            $input.removeClass("searchAjax").addClass("searchIdle");
        }
    }, 'Search criteria...').helptext('Search criteria...');
    
    $target.find("#add-to-query").click(function(){
          console.log("HERE");
          var tree =  [{
                        'type': 'logic',
                        'operator': 'or',
                        'children': [{
                            'type': 'field',
                            'id': 1,
                            'operator': 'in',
                            'value': selected.leaves
                        }, {
                            'type': 'field',
                            'id': 2,
                            'operator': 'in',
                            'value': selected.folders
                        }]
                      }];
           $target.trigger("queryEvent", tree);
           console.log(tree);
       });
    $("body").trigger("widgetLoadedEvent", $target);
})();