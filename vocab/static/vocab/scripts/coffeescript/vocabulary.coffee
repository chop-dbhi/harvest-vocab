define [
    'jquery'
    'underscore'
    'cilantro/define/viewelement'
], ($, _, ViewElement) ->

    # Breadcrumbs navigation while in the browse mode
    breadcrumbsTemplate = '''
        <% for (var b, i = 0; i < breadcrumbs.length; i++) { %>
            <% b = breadcrumbs[i]; %>
            <% if (i === (breadcrumbs.length-1)) {%>
                <span title="<%= b.name %>"><%= b.name %></span>
            <% } else { %>
                <a href="<%= b.uri %>" title="<%= b.name %>"><%= b.name %></a> <span class="breadcrumb-arrow">&rarr;</span>
            <% } %>
        <% } %>
    '''

    # Single browsable item. If the item contains children, it will be
    # clickable to descend to the next level
    browseTemplate = '''
        <li data-id="<%= id %>" data-uri="<%= uri %>" <% if (!terminal) { %>class="folder"<% } %>>
            <button class="button-add">+</button>
            <span class="name"><%= name %>
                <% if (attrs) { %>
                    <br><small class="info"><% for (var k in attrs) { %>
                        <%= k %>: <%= attrs[k] %>
                    <% } %></small>
                <% } %>
            </span>
        </li>
    '''

    # Single search result. Each item links to it's parent view in the browse
    # mode. This allows for quickly finding items via the search, but then be
    # able to see where it exists within the hierarchy
    searchResultsTemplate = '''
        <li data-id="<%= id %>" <% if (!terminal) { %>class="folder"<% } %>>
            <button class="button-add">+</button>
            <span>
                <% if (search_only) { %>
                    <span><%= name %></span>
                <% } else { %>
                    <a href="<%= parent.uri %>"><%= name %></a>
                <% } %>
                <% if (attrs) { %>
                    <br><small class="info"><% for (var k in attrs) { %>
                        <%= k %>: <%= attrs[k] %>
                    <% } %></small>
                <% } %>
            </span>
        </li>
    '''

    # Single selected item. These are represented in the selected items list
    # below the browse/search mode container. These items link, like the search
    # results, to the parent view in the browse mode
    stagedTemplate = '''
        <li data-id="<%= id %>" <% if (!terminal) { %>class="folder"<% } %>>
            <span class="icon">optional</span>
            <% if (search_only) { %>
                <span class=text><%= name %></span>
            <% } else { %>
                <a class=text href="<%= parent.uri %>"><%= name %></a>
            <% } %>
            <span class="clear">X</span>
    '''

    # Container for all components. Includes the tabs for switching between
    # browse and search modes.
    vocabBrowserTemplate = '''
        <div id="vocab-browser-<%= pk %>" class="vocab-browser">
            <% if (!search_only) { %>
                <div class="vocab-tabs tabs">
                    <a class="tab" href="#browse-tab-<%= pk %>">Browse <%= title %></a>
                    <a class="tab" href="#search-tab-<%= pk %>">Search <%= title %></a>
                </div>
            <% } %>
            <div>
                <% if (!search_only) { %>
                    <div id="browse-tab-<%= pk %>">
                        <div class=vocab-breadcrumbs></div>
                        <ul class="vocab-browse-results list"></ul>
                    </div>
                <% } %>

                <div id="search-tab-<%= pk %>">
                    <form method="get" action="<%= directory %>">
                        <input type="text" class="vocab-search" name="q" placeholder="Search...">
                        <em>Note: only the first 100 results are displayed</em>
                    </form>
                    <div>
                        <ul class="vocab-search-results list">
                            <li class="start">Enter search terms above. Results can be clicked to go to their location in the Browse tab.</li>
                        </ul>
                    </div>
                </div>

                <h2>Selected <%= title %></h2>

                <ul class=vocab-staging-operations>
                    <li class="optional">optional</li>
                    <li class="require">require</li>
                    <li class="exclude">exclude</li>
                </ul>

                <ul class=vocab-staging></ul>

            </div>
        </div>
    '''

    OPERATIONS =
        require: 'all'
        exclude: '-all'
        optional: 'in'
        'all': 'require'
        '-all': 'exclude'
        'in': 'optional'

    objectIsEmpty = (obj) ->
        for key of obj
            return false
        return true

    ViewElement.extend
        constructor: (viewset, concept_pk) ->
            @base viewset, concept_pk
            @datasource = {}

        # Shows (toggles to) the item browser usually from an in-app link. Only
        # applicable if the browser is rendered to begin with
        _showItemBrowser: (target) ->
            browseResults = @browseResults
            item = $(target)
            li = item.parents('li')

            # Toggle the browse tab
            @tabs.tabs 'toggle', 0

            # Reload the browser and then scroll down to the target item
            @loadBrowseList item.attr('href'), ->
                target = browseResults.find("[data-id=#{ li.data('id') }]")
                browseResults.scrollTo target, 500,
                    offset: -150
                    onAfter: -> target.effect 'highlight', null, 2000
            return false

        # Renders the browseable hierarchy
        _renderBrowse: (dom) ->
            results = @browseResults = $('.vocab-browse-results', dom)

            results.on 'click', 'button', (event) =>
                target = $(event.currentTarget).parent()
                @stageItem target.data()
                return false

            results.on 'click', '.folder', (event) =>
                @loadBrowseList $(event.currentTarget).data('uri')
                return false

            # Tabs to switch between "browse" and "search" mode
            @tabs = tabs = $('.vocab-tabs', dom)
            tabs.tabs false, (evt, tab) ->
                siblings = tabs.find('.tab')
                siblings.each (i, o) -> $(o.hash, dom).hide()
                $(tab.prop('hash'), dom).show()

            # Displays the browse stack which enables returning to a previous
            # level. Delegate click events to breadcrumb anchors
            @browseBreadcrumbs = $('.vocab-breadcrumbs', dom).on 'click', 'a', (event) =>
                @loadBrowseList event.target.href
                return false

        # Renders the search interface
        _renderSearch: (dom) ->
            search = $('.vocab-search', dom)
            results = $('.vocab-search-results', dom)

            results.on 'click', 'button', (event) =>
                target = $(event.currentTarget).parent()
                @stageItem target.data()
                false

            results.on 'click', 'a', (event) =>
                @_showItemBrowser(event.currentTarget)
                return false

            search.autocomplete2
                start: ->
                    results.block()

                success: (query, resp) =>
                    results.empty()
                    unless resp.length
                        results.html '<li class="empty">No results found.</li>'
                        return
                    $.each resp, (i, o) =>
                        li = @renderListElement(o, searchResultsTemplate)
                        results.append li

                    @refreshResultState()
                    results.unblock()

        # Render the staging area
        _renderStaging: (dom) ->
            vocabOperations = $('.vocab-staging-operations', dom)
            @stagedItems = stagedItems = $('.vocab-staging', dom)

            self = @
            stagedItems.on 'click', 'li .icon', (event) ->
                # Remove any previous bound event handlers
                vocabOperations.off()

                icon = $(@)
                item = icon.parent()

                # Temporarily bind the operation list for the duration the focus
                vocabOperations.on 'click', 'li', (event) ->
                    operation = $(@)
                    icon.text(operation.text())
                    item.removeClass('optional require exclude')
                    item.addClass(operation.prop('className'))
                    self.datasource[item.data('id')] = OPERATIONS[operation.prop('className')]
                    vocabOperations.hide()

                # Position the operation list relative to the current item
                position = item.position()
                vocabOperations.css
                    top: position.top - item.height() + 1
                    left: position.left + 1
                .show()

            stagedItems.on 'click', 'li .clear', (event) =>
                item = $(event.target).parent()
                item.hide()
                @unstageItem(item.data('id'))
                @refreshResultState()

                # Remove from data source...

            stagedItems.on 'click', 'a', (event) =>
                @_showItemBrowser(event.currentTarget)
                return false

        render: ->
            # Complete document fragment that contains all elements for the
            # vocab browser
            @dom = dom = $ _.template vocabBrowserTemplate, @viewset

            # Renders and attaches event handlers the various sections of
            # the fragment
            @_renderSearch(dom)
            @_renderStaging(dom)
            if not @viewset.search_only
                @_renderBrowse(dom)
                @loadBrowseList()

        stageItem: (node, operator=OPERATIONS.optional) ->
            if not @datasource[node.id]
                li = @renderListElement(node, stagedTemplate, operator)
                @stagedItems.append li
            @datasource[node.id] = operator
            @refreshResultState()

        unstageItem: (id) ->
            # Remove from the datasource
            delete @datasource[id]
            @refreshResultState()

        constructQuery: ->
            ops = {}
            data = concept_id: @concept_pk, custom: true

            # Iterate over the datasource hash and populate an object of
            # operation arrays
            for key, value of @datasource
                if not ops[value] then ops[value] = []
                ops[value].push(key)

            # Clear the value
            if (len = _.keys(ops).length) is 0
                data.value = undefined
            else if len is 1
                data.id = @viewset.pk
                data.value = ops[value]
                data.operator = value
            # Multiple operations require nesting
            else
                children = []
                for key, value of ops
                    children.push id: @viewset.pk, value: value, operator: key, concept_id: @concept_pk
                data.type = 'and'
                data.children = children

            @dom.trigger 'ConstructQueryEvent', [data]

        # Updates itself given some external datasource
        updateDS: (evt, data) ->
            self = @
            @refreshResultState()
            unless objectIsEmpty(data)
                # Contains more than one operator lists
                if data.children
                    for child in data.children
                        self._updateDS(child.value, child.operator)
                else
                    self._updateDS(data.value, data.operator)

        _updateDS: (ids, operator) ->
            self = @
            $.each ids, (index, id) ->
                $.ajax
                    url: self.viewset.directory + id + '/'
                    success: (node) ->
                        self.stageItem node, operator

        updateElement: (evt, element) ->

        elementChanged: (evt, element) ->

        # Loads a list of items relative to the hierarchy URL. This applies
        # to the browsable list hiearchy
        loadBrowseList: (url, callback) ->
            @browseResults.block()

            # Default to the root endpoint
            url = url or @viewset.directory
            breadcrumbs = [name: 'All', uri: @viewset.directory]

            $.getJSON url, (data) =>
                @browseResults.empty()
                @browseBreadcrumbs.empty()

                unless _.isArray data
                    nodes = data.children
                    breadcrumbs = breadcrumbs.concat((if data.ancestors.length then data.ancestors else []))
                    breadcrumbs.push name: data.name
                else
                    nodes = data

                # Render each node
                for n in nodes
                    li = @renderListElement(n, browseTemplate)
                    @browseResults.append li

                # Update the breadcrumbs to reflect the hierarchy state
                tmpl = _.template breadcrumbsTemplate, breadcrumbs: breadcrumbs
                @browseBreadcrumbs.html tmpl
                # Update the state of all results
                @refreshResultState()
                callback?()
                @browseResults.unblock()

        # Handles some standard logic for determing the appropriate parent
        # node (and uri) for the template
        renderListElement: (node, template, operator=OPERATIONS.optional) ->
            unless node.parent
                if not node.ancestors or node.ancestors.length is 0
                    node.parent = uri: @viewset.directory
                else
                    node.parent = uri: node.ancestors[0].uri
            node.search_only = @viewset.search_only
            li = $ _.template template, node
            optext = OPERATIONS[operator]
            li.addClass(optext).find('.icon').text(optext)
            li.data node
            return li

        # Updates the various lists with the current state
        refreshResultState: ->
            # Return to default state (enabled)
            $('li', @browseResults).removeClass 'added'
            $('button', @browseResults).attr 'disabled', false
            $('li', @searchResults).removeClass 'added'
            $('button', @searchResults).attr 'disabled', false

            # Disable items that have been staged
            for id of @datasource
                $('li[data-id=' + id + ']', @browseResults).addClass('added').find('button').attr 'disabled', true
                $('li[data-id=' + id + ']', @searchResults).addClass('added').find('button').attr 'disabled', true
