define(

    ["/static/plugins/vb/js/frontdesk.js"],

    function(FrontDesk) {
    // browser refers to the div on screen where the concept will be displayed
    var prefix = "/vocab";
    
    var breadcrumbsTemplate = $.jqotec([ 
        '<% for (var index = 0; index < this.path.length; index++) {%>',
            '<% if (index === (this.path.length-1)) {%>',
                '&raquo; <b><%=this.path[index].name%></b>',
            '<% } else { %>',
                '&raquo; <a href="#" data-catid="<%=this.path[index].child_ref%>"><%=this.path[index].name%></a>',
            '<% } %>',
        '<% } %>'].join(''));
    
    var browseTemplate = $.jqotec([
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
        '<% } %>'].join(''));
    
    var searchResultsTemplate = $.jqotec([
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
        '</li>',
        ].join(''));
    
    var vocabBrowserTemplate = [
        '<div id="browser" class="container">',

            '<div class="toolbar header tabs">',
                '<a id="showBrowse" class="tab" href="#browseTab">Browse Diagnoses</a>',
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
    ].join('');
    
    // Make sure the currently displayed nodes are correctly colored
    // as to whether they are selected for the query.
    var refreshBrowser = function(){
        $('li', choices).removeClass("added");
        $('button', choices).attr("disabled",false);
        
        $('li', results).removeClass('added');
        $('button', results).attr('disabled', false); 
        
        $('li', choices).add('li', results).each(function(index, element) {
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

    };
    
    // Remove a previously selected node..
    var removeNode = function($node){
        var index;
        if ($node.data("node").child_ref){
            index = $.inArray($node.data("node").id,ds[folder]);
            ds[folder].splice(index,1);
            browser.trigger("ElementChangedEvent", [{name:folder, value:ds[folder].length > 0 ?ds[folder]:undefined}]);
        }else{
            index = $.inArray($node.data("node").id,ds[leaf]);
            ds[leaf].splice(index,1);
            browser.trigger("ElementChangedEvent", [{name:leaf, value:ds[leaf].length > 0 ? ds[leaf]:undefined}]);
        }
        $node.remove();
        refreshBrowser();
    };


    var addNode = function(node){
       var isFolder = !!node.child_ref ? true : false;

       var $new_node = $('<li><button class="button-remove">-</button>'+node.name+'</li>');

       $new_node.find("button").click(function(){
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
           $new_node.addClass('folder');
           selected.prepend($new_node);
           ds[folder].unshift(node.id);
           browser.trigger("ElementChangedEvent", [{name:folder, value:ds[folder]}]);
       }else{
            if ($.inArray(node.id, ds[leaf])!=-1){
                  return;
            }
            selected.prepend($new_node);
            ds[leaf].unshift(node.id);
            browser.trigger("ElementChangedEvent", [{name:leaf, value:ds[leaf]}]);
       }
    };
    
    var reloadBrowser = function(category) {
        var basenode = {child_ref: '', name: 'All'}; 

        $.getJSON(prefix+'/browse/'+category.toString().replace("#",""), function(data){

            data.path.unshift(basenode);
            
            choices.empty();

            for (var index = 0; index < data.nodes.length; index++) {
                var $li = $($.jqote(browseTemplate,data.nodes[index]));
                $li.data("node",data.nodes[index]);
                   
                // Check to see if the item has been selected
                if (data.nodes[index].child_ref){
                    if ($.inArray(data.nodes[index].id, ds[folder])!=-1){
                        $li.addClass("added");
                    }
                } else {
                    if ($.inArray(data.nodes[index].id, ds[leaf])!=-1){
                        $li.addClass("added");
                    }
                }

                choices.append($li);                   
            }
 
            breadcrumbs.empty().html($.jqote(breadcrumbsTemplate,data));

        }); 
    };
    
    var ds = {};
    var that = {};
    var leaf;
    var folder;

    var browser = $(vocabBrowserTemplate),
        tabs = $('.tabs', browser),
        choices = $('#browser-choices', browser),
        selected = $('#browser-selected', browser),
        search = $('#browser-search', browser),
        results = $('#browser-results', browser),
        breadcrumbs = $('#browser-breadcrumbs', browser);

    // enable tabs, we use a very barebones tabs implementation
    // the core code only adds the appropriate classes to selected
    // and non-selected tabs, represented by <a> elements.
    tabs.tabs(false, function (evt, $tab){
        refreshBrowser();
        var $siblings = $tab.siblings('.tab');
        browser.find($tab.attr('hash')).show();
        $siblings.each(function(index, neighbor){
            browser.find($(neighbor).attr('hash')).hide();
        });
    });

    // breadcrumb navigation
    breadcrumbs.delegate('a', 'click', function(){
        reloadBrowser($(this).data("catid"));
        return false;
    });

    // add item from available choices
    choices.delegate('button', 'click', function(evt) {
        var target = $(this);
            li = target.parent();

        target.attr("disabled", "disabled");

        addNode(li.data("node"));
        li.addClass("added");

        return false;
    });

    results.delegate('button', 'click', function(evt) {
        var target = $(this);
            li = target.parent();

        target.attr("disabled", "disabled");

        addNode(li.data("node"));
        li.addClass("added");

        return false;
    });

    // descend in hierarchy
    choices.delegate('.folder', 'click', function() {
        reloadBrowser($(this).data("node").child_ref);
        return false;
    });

    // remove item from selected items
    selected.delegate('button', 'click', function() {
        $(this).trigger("removeItemEvent"); 
    });


    var execute = function($content_div, concept_id, data){
        leaf = concept_id+"_"+data.leaf;
        folder = concept_id+"_"+data.folder;
        ds[leaf] = [];
        ds[folder] = [];
        
        // Setup the browser
        reloadBrowser('');
        
        // Setup the search 
        
        search.autocomplete2({
            success: function(query, resp) {

                results.empty();

                $.each(resp, function(index, value){
                    if (value.id === -1) {
                          results.html("<div>No matches.</div>");
                          return;
                    }
                    var $li = $($.jqote(searchResultsTemplate, value));
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
        
        browser.bind("UpdateDSEvent", function(evt, new_ds){
            var operator = /operator$/;
            var hotelVocab = new FrontDesk();
            hotelVocab.onEmpty(refreshBrowser);
            
            if (!$.isEmptyObject(new_ds)){
                // Add items
                for (key in new_ds){
                    // ignore the operator
                    if (operator.test(key)) continue;
                    
                    // key = "concept_field"
                    // concept doesn't matter here
                    var field = key.split("_")[1];
                    $.each(new_ds[key], function(index,instance_id){
                        hotelVocab.checkIn();
                        $.ajax({url:"/vocab?field="+field+"&instance="+instance_id, 
                                success: function(node) {
                                     addNode(node);
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
        });
        
       browser.bind("UpdateQueryButtonClicked", function(event){
              browser.trigger("ConstructQueryEvent");
       });
       
       $content_div.trigger("ViewReadyEvent", [browser]);
 };
 that.execute = execute;
 return that;
});
