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
                <h3 title="<%= b.name %>"><%= b.name %></h3>
            <% } else { %>
                &raquo; <a href="<%= b.uri %>" title="<%= b.name %>"><%= b.name %></a>
            <% } %>
        <% } %>
    '''

    # Single browsable item. If the item contains children, it will be
    # clickable to descend to the next level
    browseTemplate = '''
        <li data-id="<%= id %>" data-uri="<%= uri %>" <% if (!terminal) { %>class="folder"<% } %>>
            <button class="button-add">+</button>
            <span><%= name %>
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
    selectedTemplate = '''
        <li data-id="<%= id %>" <% if (!terminal) { %>class="folder"<% } %>>
            <button class="button-remove">-</button>
            <% if (search_only) { %>
                <span><%= name %></span>
            <% } else { %>
                <a href="<%= parent.uri %>"><%= name %></a>
            <% } %>
        </li>
    '''

    # Container for all components. Includes the tabs for switching between
    # browse and search modes.
    vocabBrowserTemplate = '''
        <div class="browser">
            <% if (!search_only) { %>
                <div class="tabs">
                    <a class="tab" href="#browse-tab-<%= pk %>">Browse <%= title %></a>
                    <a class="tab" href="#search-tab-<%= pk %>">Search <%= title %></a>
                </div>
            <% } %>
            <div>
                <% if (!search_only) { %>
                    <div id="browse-tab-<%= pk %>">
                        <div class="breadcrumbs"></div>
                        <ul class="list choices"></ul>
                    </div>
                <% } %>

                <div id="search-tab-<%= pk %>">
                    <form method="get" action="<%= directory %>">
                        <input type="text" class="search" name="q" placeholder="Search...">
                        <em>Note: only the first 100 results are displayed</em>
                    </form>
                    <div>
                        <ul class="list results">
                            <li class="start">Enter search terms above. Results can be clicked to go to their location in the Browse tab.</li>
                        </ul>
                    </div>
                </div>

                <h2>Selected <%= title %></h2>
                <small>Note: this query is currently limited to getting results having at least ONE of these <%= title.toLowerCase() %>.</small>
                <ul class="list selected"></ul>
            </div>
        </div>
    '''

    ViewElement.extend
        constructor: (viewset, concept_pk) ->
            @base viewset, concept_pk
            @ds = []

        render: ->
            addItem = (evt) ->
                target = $(this).parent()
                objRef.addNode target.data()
                false

            linkItem = (evt) ->
                item = $(this)
                li = item.parents('li')
                tabs.tabs 'toggle', 0
                objRef.reloadBrowser item.attr('href'), ->
                    target = $('[data-id=' + li.data('id') + ']', objRef.choices)
                    objRef.choices.scrollTo target, 500,
                        offset: -150
                        onAfter: ->
                            target.effect 'highlight', null, 2000

                false
            objRef = this
            pk = @pk = @concept_pk + '_' + @viewset.pk
            dom = @dom = $ _.template vocabBrowserTemplate, @viewset
            tabs = $('.tabs', dom)
            choices = @choices = $('.choices', dom)
            selected = @selected = $('.selected', dom)
            search = @search = $('.search', dom)
            results = @results = $('.results', dom)
            breadcrumbs = @breadcrumbs = $('.breadcrumbs', dom)
            tabs.tabs false, (evt, tab) ->
                siblings = tabs.find('.tab')
                siblings.each (i, o) ->
                    $(o.hash, objRef.dom).hide()

                $(tab.prop('hash'), objRef.dom).show()

            breadcrumbs.delegate 'a', 'click', ->
                objRef.reloadBrowser $(this).attr('href')
                false

            choices.delegate 'button', 'click', addItem
            results.delegate 'button', 'click', addItem
            results.delegate 'a', 'click', linkItem
            selected.delegate 'a', 'click', linkItem
            choices.delegate '.folder', 'click', ->
                objRef.reloadBrowser $(this).data('uri')
                false

            selected.delegate 'button', 'click', ->
                target = $(this)
                li = target.parent()
                objRef.removeNode li.data()
                li.remove()
                false

            @execute()

        execute: ->
            objRef = this
            results = @results
            @reloadBrowser()
            @search.autocomplete2
                start: ->
                    results.block()

                success: (query, resp) ->
                    results.empty()
                    unless resp.length
                        results.html '<li class="empty">No results found.</li>'
                        return
                    $.each resp, (i, o) ->
                        li = objRef.renderListElement(o, searchResultsTemplate)
                        results.append li

                    objRef.refreshBrowser()
                    results.unblock()

        updateDS: (evt, new_ds) ->
            objRef = this
            operator = /operator$/
            @refreshBrowser()
            unless $.isEmptyObject(new_ds)
                for key of new_ds
                    continue    if operator.test(key)
                    $.each new_ds[key], (index, instance_id) ->
                        $.ajax
                            url: objRef.viewset.directory + instance_id + '/'
                            success: (node) ->
                                objRef.addNode node

        updateElement: (evt, element) ->

        elementChanged: (evt, element) ->

        reloadBrowser: (url, callback) ->
            url = url or @viewset.directory
            callback = callback or ->

            objRef = this
            breadcrumbs = [name: 'All', uri: @viewset.directory]
            @choices.block()
            $.getJSON url, (data) ->
                objRef.choices.empty()
                objRef.breadcrumbs.empty()
                unless $.isArray(data)
                    nodes = data.children
                    breadcrumbs = breadcrumbs.concat((if data.ancestors.length then data.ancestors else []))
                    breadcrumbs.push name: data.name
                else
                    nodes = data
                li = undefined
                n = undefined
                i = 0

                while i < nodes.length
                    n = nodes[i]
                    li = objRef.renderListElement(n, browseTemplate)
                    objRef.choices.append li
                    i++

                tmpl = _.template breadcrumbsTemplate, breadcrumbs: breadcrumbs
                objRef.breadcrumbs.html tmpl
                objRef.refreshBrowser()
                callback()
                objRef.choices.unblock()

        renderListElement: (node, template) ->
            unless node.parent
                if not node.ancestors or node.ancestors.length is 0
                    node.parent = uri: @viewset.directory
                else
                    node.parent = uri: node.ancestors[0].uri
            node.search_only = @viewset.search_only
            li = $ _.template template, node
            li.data node
            li

        addNode: (node) ->
            if @ds.indexOf(node.id) < 0
                @ds.push node.id
                li = @renderListElement(node, selectedTemplate)
                @selected.append li
            @dom.trigger 'ElementChangedEvent', [name: @pk, value: @ds]
            @refreshBrowser()

        removeNode: (node) ->
            i = undefined
            @ds.splice i, 1    if (i = @ds.indexOf(node.id)) > -1
            @dom.trigger 'ElementChangedEvent', [name: @pk, value: (if @ds.length > 0 then @ds else 'undefined')]
            @refreshBrowser()

        refreshBrowser: ->
            $('li', @choices).removeClass 'added'
            $('button', @choices).attr 'disabled', false
            $('li', @results).removeClass 'added'
            $('button', @results).attr 'disabled', false
            id = undefined
            li = undefined
            i = @ds.length

            while i--
                id = @ds[i]
                $('li[data-id=' + id + ']', @choices).addClass('added').find('button').attr 'disabled', true
                $('li[data-id=' + id + ']', @results).addClass('added').find('button').attr 'disabled', true
