define(["cilantro/define/viewelement"],
    function(ViewElement) {


    // browser refers to the div on screen where the concept will be displayed
    var VocabBrowser = ViewElement.extend({

        constructor: function(viewset, concept_pk) {
            this.base(viewset, concept_pk);
            this.ds =  [];
        },

        render: function(){
            var objRef = this;

            var pk = this.pk = this.concept_pk + '_' + this.viewset.pk;
            var dom = this.dom = $($.jqote(VocabBrowser.vocabBrowserTemplate, this.viewset));
            var tabs = $('.tabs', dom);
            var choices = this.choices = $('.choices', dom);
            var selected = this.selected = $('.selected', dom);
            var search = this.search = $('.search', dom);
            var results = this.results = $('.results', dom);
            var breadcrumbs = this.breadcrumbs = $('.breadcrumbs', dom);

            // enable tabs, we use a very barebones tabs implementation
            // the core code only adds the appropriate classes to selected
            // and non-selected tabs, represented by <a> elements.
            tabs.tabs(false, function (evt, tab) {
                var siblings = tabs.find('.tab')
                // hide everything
                siblings.each(function(i, o) {
                    $(o.hash, objRef.dom).hide();
                });

                // get the current on and show it
                $(tab.attr('hash'), objRef.dom).show();
            });

            // breadcrumb navigation
            breadcrumbs.delegate('a', 'click', function(){
                objRef.reloadBrowser($(this).attr('href'));
                return false;
            });

            function addItem(evt) {
                var target = $(this).parent();
                objRef.addNode(target.data());
                return false;
            }

            // add item from available choices
            choices.delegate('button', 'click', addItem);
            results.delegate('button', 'click', addItem);

                    
            function linkItem(evt) {
                var item = $(this);
                var li = item.parents('li');

                // switch to the browse tab
                tabs.tabs('toggle', 0);

                // reload the browser with the item's url
                objRef.reloadBrowser(item.attr('href'), function() {

                    // get the corresponding list item in the browser
                    var target = $('[data-id='+li.data('id')+']', objRef.choices);

                    // scroll down to the referenced item since this page
                    // represents this item's parent.
                    objRef.choices.scrollTo(target, 500, {
                        offset: -150,
                        onAfter: function() {
                            // add highlight effect to ensure the user sees the
                            // location of the item
                            target.effect('highlight', null, 2000); 
                        }
                    });

                });
                return false;
            };

            // handler for clicking on search results, they take the user
            // to the location of the item in the browser since to provide
            // more context
            results.delegate('a', 'click', linkItem);
            selected.delegate('a', 'click', linkItem);


            // descend in hierarchy
            choices.delegate('.folder', 'click', function() {
                objRef.reloadBrowser($(this).data('uri'));
                return false;
            });

            // remove item from selected items
            selected.delegate('button', 'click', function() {
                var target = $(this);
                var li = target.parent();
                objRef.removeNode(li.data());
                li.remove();
                return false;
            });

            this.execute();
        },

        execute: function(){
            var objRef = this;
            var results = this.results;

            // Setup the browser
            this.reloadBrowser();

            // Setup the search
            this.search.autocomplete2({
                start: function() {
                    results.block();
                },
                success: function(query, resp) {
                    results.empty();

                    // no results
                    if (!resp.length) {
                        results.html('<li class="empty">No results found.</li>');
                        return;
                    }

                    // show results
                    $.each(resp, function(i, o){
                        var li = objRef.renderListElement(o, VocabBrowser.searchResultsTemplate);
                        results.append(li);
                    });

                    objRef.refreshBrowser();
                    results.unblock();
                }
            });
        },

        updateDS: function(evt, new_ds) {
            var objRef = this;
            var operator = /operator$/;
            this.refreshBrowser();

            if (!$.isEmptyObject(new_ds)){
                // Add items
                for (key in new_ds){

                    // ignore the operator
                    if (operator.test(key)) continue;

                    $.each(new_ds[key], function(index, instance_id){
                        $.ajax({
                            url: objRef.viewset.directory + instance_id + '/',
                            success: function(node) {
                                objRef.addNode(node);
                            },
                        });
                    });
                }
            }
        },

        updateElement: function(evt, element) {},

        elementChanged: function(evt, element) {},

        reloadBrowser: function(url, callback) {
            url = url || this.viewset.directory;
            callback = callback || function() {};

            var objRef = this;
            var breadcrumbs = [{name: 'All', uri: this.viewset.directory}];

            this.choices.block();
            $.getJSON(url, function(data){
                objRef.choices.empty();
                objRef.breadcrumbs.empty()

                if (!$.isArray(data)) {
                    nodes = data.children
                    breadcrumbs = breadcrumbs.concat(data.ancestors.length ? data.ancestors : []);
                    breadcrumbs.push({name: data.name});
                } else {
                    nodes = data;
                }

                for (var li, n, i = 0; i < nodes.length; i++) {
                    n = nodes[i];
                    li = objRef.renderListElement(n, VocabBrowser.browseTemplate);
                    objRef.choices.append(li);
                }

                // update breadcrumbs
                var tmpl = $.jqote(VocabBrowser.breadcrumbsTemplate, {breadcrumbs: breadcrumbs});
                objRef.breadcrumbs.html(tmpl);

                // ensure the new list of items reflect the current state
                objRef.refreshBrowser();

                // execute caller-defined callback
                callback();

                objRef.choices.unblock();

            });
        },

        renderListElement: function(node, template) {
            // always ensure there is a reference to the parent node
            if (!node.parent) {
                if (!node.ancestors || node.ancestors.length == 0)
                    node.parent = {uri: this.viewset.directory}
                else
                    node.parent = {uri: node.ancestors[0].uri}
            }

            var li = $($.jqote(template, node));
            // bind data locally to element since this may be used to render
            // another template
            li.data(node);

            return li;

        },

        addNode : function(node) {
            // ensure this is not redundant
            if (this.ds.indexOf(node.id) < 0) {
                this.ds.push(node.id);
                var li = this.renderListElement(node, VocabBrowser.selectedTemplate);
                this.selected.append(li);
            }

            // ensure everything is synced up
            this.dom.trigger("ElementChangedEvent", [{name: this.pk, value: this.ds}]);
            this.refreshBrowser();
        },

        // Remove a previously selected node..
        removeNode : function(node) {
            // remove this ID from the list
            var i;
            if ((i = this.ds.indexOf(node.id)) > -1)
                this.ds.splice(i, 1);

            this.dom.trigger("ElementChangedEvent", [{name: this.pk,
                value: this.ds.length > 0 ? this.ds : undefined}]);
            this.refreshBrowser();
        },

        // Make sure the currently displayed nodes are correctly colored
        // as to whether they are selected for the query.
        refreshBrowser : function() {
            $('li', this.choices).removeClass("added");
            $('button', this.choices).attr("disabled", false);

            $('li', this.results).removeClass("added");
            $('button', this.results).attr("disabled", false);

            for (var id, li, i = this.ds.length; i--; ) {
                id = this.ds[i];

                $('li[data-id='+id+']', this.choices)
                    .addClass('added')
                    .find('button').attr('disabled', true);

                $('li[data-id='+id+']', this.results)
                    .addClass('added')
                    .find('button').attr('disabled', true);
            }

        }
    },

    {
        breadcrumbsTemplate : $.jqotec([
            '<% for (var b, i = 0; i < this.breadcrumbs.length; i++) {%>',
                '<% b = this.breadcrumbs[i]; %>',
                '<% if (i === (this.breadcrumbs.length-1)) {%>',
                    '<h3 title="<%= b.name %>"><%= b.name %></h3>',
                '<% } else { %>',
                    '&raquo; <a href="<%= b.uri %>" title="<%= b.name %>"><%= b.name %></a>',
                '<% } %>',
            '<% } %>'].join('')),

        browseTemplate : $.jqotec([
            '<li data-id="<%= this.id %>" data-uri="<%= this.uri %>" <% if (!this.terminal) { %>class="folder"<% } %>>',
                '<button class="button-add">+</button>',
                '<span><%= this.name %>',
                    '<% if (this.attrs) { %>',
                        '<br><small style="color: #999">',
                            '<% for (var k in this.attrs) { %>',
                                '<%= k %>: <%= this.attrs[k] %>',
                            '<% } %>',
                        '</small>',
                    '<% } %>',
                '</span>',
            '</li>'].join('')),

        searchResultsTemplate : $.jqotec([
            '<li data-id="<%= this.id %>" <% if (!this.terminal) { %>class="folder"<% } %>>',
                '<button class="button-add">+</button>',
                '<span><a href="<%= this.parent.uri %>"><%= this.name %></a>',
                    '<% if (this.attrs) { %>',
                        '<br><small style="color: #999">',
                            '<% for (var k in this.attrs) { %>',
                                '<%= k %>: <%= this.attrs[k] %>',
                            '<% } %>',
                        '</small>',
                    '<% } %>',
                '</span>', 
            '</li>'].join('')),

        selectedTemplate : $.jqotec([
            '<li data-id="<%= this.id %>" <% if (!this.terminal) { %>class="folder"<% } %>>',
                '<button class="button-remove">-</button>',
                '<a href="<%= this.parent.uri %>"><%= this.name %></a>',
            '</li>'].join('')),

        vocabBrowserTemplate : $.jqotec([
            '<div class="browser">',

                '<div class="tabs">',
                    '<a class="tab" href="#browse-tab-<%= this.pk %>">Browse <%= this.title %></a>',
                    '<a class="tab" href="#search-tab-<%= this.pk %>">Search <%= this.title %></a>',
                '</div>',

                '<div>',

                    '<div id="browse-tab-<%= this.pk %>">',
                        '<div class="breadcrumbs"></div>',
                        '<ul class="list choices"></ul>',
                    '</div>',

                    '<div id="search-tab-<%= this.pk %>">',
                        '<form method="get" action="<%= this.directory %>">',
                            '<input type="text" class="search" name="q" placeholder="Search...">',
                            ' <em>Note: only the first 100 results are displayed</em>',
                        '</form>',
                        '<div>',
                            '<ul class="list results"><li class="start">Enter search terms above.',
                                ' Results can be clicked to go to their location in the Browse tab.</li></ul>',
                        '</div>',
                    '</div>',

                    '<h2>Selected <%= this.title %></h2>',
                    '<small>Note: this query is currently limited to getting results having ',
                    'at least ONE of these <%= this.title.toLowerCase() %>.</small>',
                    '<ul class="list selected"></ul>',

                '</div>',
            '</div>'
        ].join(''))
    });

    return VocabBrowser;
});

