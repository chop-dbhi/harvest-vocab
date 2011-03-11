define(["utils/frontdesk", "define/viewelement"],
    function(FrontDesk, ViewElement) {
    // browser refers to the div on screen where the concept will be displayed 
    var VocabBrowser = ViewElement.extend({
         constructor: function(viewset, concept_pk){
             var ds = this.ds =  {};
             var leaf = this.leaf = null;
             var folder = this.folder = null;
             this.base(viewset, concept_pk);
         },
         render: function(){
              var objRef = this;
              var dom = this.dom = $(VocabBrowser.vocabBrowserTemplate);
              var tabs = $('.tabs', dom);
              var choices = this.choices = $('#browser-choices', dom);
              var selected = this.selected = $('#browser-selected', dom);
              var search = this.search = $('#browser-search', dom);
              var results = this.results = $('#browser-results', dom);
              var breadcrumbs = this.breadcrumbs = $('#browser-breadcrumbs', dom);
             
              // enable tabs, we use a very barebones tabs implementation
              // the core code only adds the appropriate classes to selected
              // and non-selected tabs, represented by <a> elements.
             
              tabs.tabs(false, function (evt, $tab){
                  objRef.refreshBrowser();
                  var $siblings = $tab.siblings('.tab');
                  dom.find($tab.attr('hash')).show();
                  $siblings.each(function(index, neighbor){
                      dom.find($(neighbor).attr('hash')).hide();
                  });
              });
              
              // breadcrumb navigation
              breadcrumbs.delegate('a', 'click', function(){
                  objRef.reloadBrowser($(this).data("catid"));
                  return false;
              });
              
              // add item from available choices
              choices.delegate('button', 'click', function(evt) {
                  var target = $(this);
                  var li = target.parent();
              
                  target.attr("disabled", "disabled");
              
                  objRef.addNode(li.data("node"));
                  li.addClass("added");
              
                  return false;
              });
              
              // add item from search results
              results.delegate('button', 'click', function(evt) {
                  var target = $(this);
                  var li = target.parent();
              
                  target.attr("disabled", "disabled");
              
                  objRef.addNode(li.data("node"));
                  li.addClass("added");
              
                  return false;
              });
              
              // descend in hierarchy
              choices.delegate('.folder', 'click', function() {
                  objRef.reloadBrowser($(this).data("node").child_ref);
                  return false;
              });
              
              // remove item from selected items
              selected.delegate('button', 'click', function() {
                  var target = $(this);
                  var li = target.parent();
                  objRef.removeNode(li.data("node"));
                  li.remove();
                  return false;
              });
              
              this.execute();
         },
         execute: function(){
             var leaf = this.leaf = this.concept_pk+"_"+this.viewset.leaf;
             var folder = this.folder = this.concept_pk+"_"+this.viewset.folder;
             var results = this.results;
             var ds = this.ds;
             ds[leaf] = [];
             ds[folder] = [];
             
             // Setup the browser
             this.reloadBrowser('');

             // Setup the search 
             this.search.autocomplete2({
                 success: function(query, resp) {
                     results.empty();
                     resp = (typeof resp == "string") || (resp instanceof String) ? $.parseJSON(resp) : resp; 
                     $.each(resp, function(index, value){
                         if (value.id === -1) {
                               results.html("<div>No matches.</div>");
                               return;
                         }

                         var $li = $($.jqote(VocabBrowser.searchResultsTemplate, value));
                         $li.data("node", value);                        

                         if (value.child_ref) {
                             $li.addClass('folder');

                             if ($.inArray(value.id, ds[folder]) != -1)
                                 $li.addClass("added");
                         } else {
                             if ($.inArray(value.id,ds[leaf]) != -1)
                                 $li.addClass("added");
                         }
                         results.append($li);
                     });                 
                 }
             });
         },
         updateDS: function(evt, new_ds) {
             var objRef = this;
             var operator = /operator$/;
             var hotelVocab = new FrontDesk();
             hotelVocab.onEmpty($.proxy(this.refreshBrowser,this));

             if (!$.isEmptyObject(new_ds)){
                 // Add items
                 for (key in new_ds){
                     // ignore the operator
                     if (operator.test(key)) continue;
                     // concept doesn't matter here
                     var field = key.split("_")[1];
                     $.each(new_ds[key], function(index,instance_id){
                         hotelVocab.checkIn();
                         $.ajax({url:"vocab/" + this.viewset.vocab_index + "?field="+field+"&instance="+instance_id, 
                              success: function(node) {
                                   objRef.addNode(node);
                                   hotelVocab.checkOut();
                              },
                              dataType:"json",
                              error:function(){
                                   hotelVocab.checkOut();
                              }
                         });
                     });
                 }   
             }
         },
         updateElement: function(evt, element) {},
         elementChanged: function(evt,element) {},
         reloadBrowser: function(category) {
             var objRef = this;
             var basenode = {child_ref: '', name: 'All'}; 
             $.getJSON(VocabBrowser.prefix + "/" + this.viewset.vocab_index + '/browse/'+category, function(data){
                 data.path.unshift(basenode);
                 objRef.choices.empty();
                 for (var index = 0; index < data.nodes.length; index++) {
                     var $li = $($.jqote(VocabBrowser.browseTemplate,data.nodes[index]));
                     $li.data("node",data.nodes[index]);

                     // Check to see if the item has been selected
                     if (data.nodes[index].child_ref){
                         if ($.inArray(data.nodes[index].id, objRef.ds[objRef.folder])!=-1){
                             $li.addClass("added");
                         }
                     } else {
                         if ($.inArray(data.nodes[index].id, objRef.ds[objRef.leaf])!=-1){
                             $li.addClass("added");
                         }
                     }
                     objRef.choices.append($li);                   
                 }
                 objRef.breadcrumbs.empty().html($.jqote(VocabBrowser.breadcrumbsTemplate,data));
             }); 
         },
         addNode : function(node){
             var isFolder = !!node.child_ref;
             var ds = this.ds;
             var leaf = this.leaf;
             var folder = this.folder;
             
             var $new_node = $('<li><button class="button-remove">-</button>'+node.name+'</li>');
             
             $new_node.data('node', node);
             if (isFolder){
                 if ($.inArray(node.id,this.ds[folder])!=-1){
                     return;
                 }
                 $new_node.addClass('folder');
                 this.selected.prepend($new_node);
                 ds[folder].unshift(node.id);
                 this.dom.trigger("ElementChangedEvent", [{name:folder, value:ds[folder]}]);
             }else{
                 if ($.inArray(node.id, ds[leaf])!=-1){
                       return;
                 }
                 this.selected.prepend($new_node);
                 ds[leaf].unshift(node.id);
                 this.dom.trigger("ElementChangedEvent", [{name:leaf, value:ds[leaf]}]);
             }   
        },
        // Remove a previously selected node..
        removeNode : function(node){
            var index;
            var ds = this.ds;
            var leaf = this.leaf;
            var folder = this.folder;
            var dom = this.dom;
            
            if (node.child_ref){
                index = $.inArray(node.id, ds[folder]);
                ds[folder].splice(index,1);
                dom.trigger("ElementChangedEvent", [{name:folder, value:ds[folder].length > 0 ? ds[folder]:undefined}]);
            }else{
                index = $.inArray(node.id, this.ds[this.leaf]);
                ds[this.leaf].splice(index,1);
                dom.trigger("ElementChangedEvent", [{name:leaf, value:ds[leaf].length > 0 ? ds[leaf]:undefined}]);
            }
            this.refreshBrowser();
        },
        
        // Make sure the currently displayed nodes are correctly colored
        // as to whether they are selected for the query.
        refreshBrowser : function(){
            var ds = this.ds;
            var leaf = this.leaf;
            var folder = this.folder;
            
            $('li', this.choices).removeClass("added");
            $('button', this.choices).attr("disabled", false);

            $('li', this.results).removeClass('added');
            $('button', this.results).attr('disabled', false); 

            $('li', this.choices).add('li', this.results).each(function(index, element) {
                element = $(element);
                if (element.data('node').child_ref){
                    if ($.inArray(element.data('node').id, ds[folder]) !=-1){
                        element.addClass("added");
                        element.find("button").attr("disabled","disabled");
                    } 
                } else {
                    if ($.inArray(element.data('node').id, ds[leaf]) !=-1){
                        element.addClass("added");
                        element.find("button").attr("disabled","disabled");
                   }
                }
            });
        }
    },
    {
        breadcrumbsTemplate : $.jqotec([ 
            '<% for (var index = 0; index < this.path.length; index++) {%>',
                '<% if (index === (this.path.length-1)) {%>',
                    '&raquo; <b><%=this.path[index].name%></b>',
                '<% } else { %>',
                    '&raquo; <a href="#" data-catid="<%=this.path[index].child_ref%>"><%=this.path[index].name%></a>',
                '<% } %>',
            '<% } %>'].join('')),
        browseTemplate : $.jqotec([
            '<% if (this.child_ref) { %>',
                '<li class="folder">',
                    '<button class="button-add">+</button>',
                    '<span><%= this.name %></span>',
                '</li>',
            '<% } else { %>',
                '<li class="leaf">',
                    '<button class="button-add">+</button>',
                    '<div>',
                        '<span><%= this.name %></span>',
                        '<div class="meta">',
                            '<% if (this.attributes.icd9) { %>',
                                'ICD-9 : <%= this.attributes.icd9 %>',
                            '<% } %>',
                            '<% if (this.attributes.clinibase) { %>',
                                ' Clinibase ID : <%= this.attributes.clinibase %>',
                            '<% } %>',
                        '</div>',
                    '</div>',
                '</li>',
            '<% } %>'].join('')),
        searchResultsTemplate : $.jqotec([
            '<li class="search-item">',
                '<% if (this.child_ref) {%>',
                    '<button class="button-add folder" id="folder<%=this.id%>">+</button>',
                '<% } else {%>',
                    '<button class="button-add leaf" id="leaf<%=this.id%>">+</button>',
                '<% } %>',

                '<div>',
                    '<span>',
                        '<%= this.name %>',
                    '</span>',
                    '<div class="meta">',
                        '<% if (this.attributes.icd9) { %>',
                            'ICD-9 : <%= this.attributes.icd9 %>',
                        '<% } %>',
                        '<% if (this.attributes.clinibase) { %>',
                            ' Clinibase ID : <%= this.attributes.clinibase %>',
                        '<% } %>',

                        '<div class="node_path">',
                            '<% for (index = 0; index < this.path.length; index++){ %>',
                                '<div pathid="<%=index%>" class="path_node" style="display:inline;"><%=this.path[index].name%></div>',
                                '<% if (index != this.path.length -1){%> &raquo <%}%>',
                            '<% } %>',
                        '</div>',

                    '</div>',
                '</div>',
            '</li>'
            ].join('')),
        vocabBrowserTemplate : [
            '<div id="browser" class="container">',

                '<div class="toolbar header tabs">',
                    '<a id="showBrowse" class="tab" href="#browseTab">Browse <%=this.viewset.title%></a>',
                    '<a class="tab" href="#searchTab">Search Diagnoses</a>',
                '</div>',

                '<div class="content">',

                    '<div id="browseTab">',
                        '<div id="browser-breadcrumbs"></div>',
                        '<ul id="browser-choices" class="browser-content"></ul>',
                    '</div>',

                    '<div id="searchTab">',
                        '<form method="get" action="/vocab/search/">',
                            '<input type="text" class="search" id="browser-search" name="q" size="25" placeholder="Search terms..">',
                        '</form>',
                        '<div>',
                            '<ul id="browser-results" class="browser-content"></ul>',
                        '</div>',
                    '</div>',

                    '<b>Patient diagnosed  with one or more of the following:</b>',

                    '<ul id="browser-selected" class="browser-content"></ul>',

                '</div>',
            '</div>'
        ].join(''),
        prefix : "/cardiodb/vocab"
    });
    return VocabBrowser;
});
