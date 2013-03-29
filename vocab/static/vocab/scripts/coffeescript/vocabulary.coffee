define [
    'cilantro'
    'cilantro/ui',
    'tpl!templates/vocab-browser/breadcrumbs.html'
    'tpl!templates/vocab-browser/browse.html'
    'tpl!templates/vocab-browser/search-results.html'
    'tpl!templates/vocab-browser/staged.html'
    'tpl!templates/vocab-browser/vocab-browser.html'
], (c, ui,
    breadcrumbsTemplate, 
    browseTemplate, 
    searchResultsTemplate, 
    stagedTemplate, 
    vocabBrowserTemplate) ->

    DEFAULT_OPERATOR = 'in'
    EXCLUDE_OPERATOR = '-in'

    class VocabForm extends c.ui.ConceptForm
        className: 'vocab-browser'

        regions:
            search: '.search'
            browser: '.browser'
            optional: '.vocab-optional'
            require: '.vocab-require'
            exlcude: '.vocab-exclude'

        template: vocabBrowserTemplate

        onRender: ->
            # Renders and attaches event handlers the various sections of
            # the fragment
            @_renderSearch
            @_renderStaging

            if not @model.search_only
                @_renderBrowse
                @loadBrowseList

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
        _renderBrowse:  ->
            results = @browseResults = @$('.vocab-browse-results')

            results.on 'click', 'button', (event) =>
                target = $(event.currentTarget).parent()
                @stageItem target.data()
                return false

            results.on 'click', '.folder', (event) =>
                @loadBrowseList $(event.currentTarget).data('uri')
                return false

            # Tabs to switch between "browse" and "search" mode
            @tabs = tabs = @$('.vocab-tabs')
            tabs.tabs false, (evt, tab) ->
                siblings = tabs.find('.tab')
                siblings.each (i, o) -> @$(o.hash).hide()
                @$(tab.prop('hash')).show()

            # Displays the browse stack which enables returning to a previous
            # level. Delegate click events to breadcrumb anchors
            @browseBreadcrumbs = @$('.vocab-breadcrumbs').on 'click', 'a', (event) =>
                @loadBrowseList event.target.href
                return false

        # Renders the search interface
        _renderSearch:  ->
            search = @$('.vocab-search')
            results = @searchResults = @$('.vocab-search-results')

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
        _renderStaging:  ->
            stagedItems = @$('.vocab-staging')

            self = @
            sortOptions =
                placeholder: 'placeholder'
                forcePlaceholderSize: true
                forceHelperSize: true
                containment: @dom
                opacity: 0.5
                cursor: 'move'
                connectWith: '.vocab-staging > ul'
                receive: (event, ui) ->
                    target = $(@)

                    if target.children().length == 1
                        target.removeClass('placeholder')

                    if ui.sender.children().length == 0
                        ui.sender.addClass('placeholder')

                    # Move from one list to another, remove previous operator
                    id = ui.item.data('id')
                    self.datasource[id].push(target.data('operator'))

                    idx = self.datasource[id].indexOf(ui.sender.data('operator'))
                    self.datasource[id].splice(idx, 1)

            optionalTarget = @$('#vocab-optional').sortable sortOptions
            optionalTarget.data('operator', 'in')

            excludeText = @$('#vocab-exclude-operator h3')
            @excludeSelect = excludeSelect = @$('#vocab-exclude-operator select').on 'change', ->
                excludeText.text(excludeSelect.find(':selected').text())

            excludeTarget = @$('#vocab-exclude').sortable sortOptions
            excludeTarget.data('operator', '-x')

            requireTarget = @$('#vocab-require').sortable sortOptions
            requireTarget.data('operator', 'all')

            @targets =
                'in': optionalTarget
                'all': requireTarget
                '-x': excludeTarget

            # Remove this item altogether
            stagedItems.on 'click', 'li button', (event) =>
                item = $(event.target).parent()
                @unstageItem(item.data('id'), item.parent().data('operator'))
                if item.siblings().length == 0
                    item.parent().addClass('placeholder')
                item.remove()
                @refreshResultState()

            # Link to in-browse mode
            stagedItems.on 'click', 'a', (event) =>
                @_showItemBrowser(event.currentTarget)
                return false

        stageItem: (node, operator=DEFAULT_OPERATOR) ->
            # Map to generic exclude operator
            if operator in ['-all', '-in']
                operator = '-x'

            # Assume this is already present in the datasource
            if typeof node is Number
                id = node
            else
                id = node.id
                # Does not exist in any bucket,
                if not @datasource[id]
                    @datasource[id] = []
                li = @renderListElement node, stagedTemplate, true
                target = @targets[operator]
                target.removeClass('placeholder')
                target.append li
            @datasource[id].push operator
            @refreshResultState()

        unstageItem: (id, operator) ->
            idx = @datasource[id].indexOf(operator)
            # Splice out the operator for this id
            if idx > -1
                @datasource[id].splice(idx, 1)
                # Delete the key, so a second check for an empty array does not
                # need to be performed elsewhere
                if not @datasource[id].length
                    delete @datasource[id]
                @refreshResultState()

        # Constructs the query that gets passed up to the main View class.
        # The `custom` property is set to bypass validation in the View, thus
        # ensure this structure is valid!
        constructQuery: ->
            operators =
                '-x': []
                'all': []
                'in': []

            data = concept_id: @concept_pk, custom: true

            if c._.isEmpty(@datasource)
                event = $.Event 'InvalidInputEvent'
                event.ephemeral = true
                event.message = 'No value has been specified.'
                @dom.trigger event
                return

            # Iterate over the datasource hash and populate an object of
            # operator arrays
            for key, ops of @datasource
                for op in ops
                    operators[op].push(key)

            # Clean up unused operator arrays
            _.each operators, (values, key) ->
                if not values.length then delete operators[key]

            # Excluded terms, swap in the real operator
            if operators['-x']
                operators[@excludeSelect.val()] = operators['-x']
                delete operators['-x']

            # Single operator
            if (keys = _.keys(operators)).length is 1
                data.id = @viewset.pk
                data.value = operators[keys[0]]
                data.operator = keys[0]

            # Multiple operators require nesting
            else
                children = []
                for key, value of operators
                    children.push id: @viewset.pk, value: value, operator: key, concept_id: @concept_pk
                data.type = 'and'
                data.children = children

            @dom.trigger 'ConstructQueryEvent', [data]

        # Updates itself given some external datasource
        updateDS: (evt, data) ->
            self = @
            @refreshResultState()
            unless c._.isEmpty(data)
                # Contains more than one operator lists
                if data.children
                    for child in data.children
                        self._updateDS(child.value, child.operator)
                else
                    self._updateDS(data.value, data.operator)

        _updateDS: (ids, operator) ->
            if operator in ['-in', '-all']
                @excludeSelect.val(operator)
                @excludeSelect.siblings().text(@excludeSelect.find(':selected').text())

            self = @
            $.each ids, (index, id) ->
                $.ajax
                    url: self.viewset.directory + id + '/'
                    success: (node) ->
                        self.stageItem node, operator

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
                for node in nodes
                    li = @renderListElement node, browseTemplate
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
        renderListElement: (node, template) ->
            unless node.parent
                if not node.ancestors or node.ancestors.length is 0
                    node.parent = uri: @viewset.directory
                else
                    node.parent = uri: node.ancestors[0].uri
            node.search_only = @viewset.search_only

            return $(_.template template, node).data(node)

        # Updates the various lists with the current state
        refreshResultState: ->
            # Return to default state (enabled)
            if not @model.search_only
                $('li', @browseResults).removeClass 'added'
                $('button', @browseResults).attr 'disabled', false
            $('li', @searchResults).removeClass 'added'
            $('button', @searchResults).attr 'disabled', false

            # Disable items that have been staged
            for id of @datasource
                if not @viewset.search_only
                    @browseResults.find('li[data-id=' + id + ']').addClass('added')
                        .find('button').attr('disabled', true)
                @searchResults.find('li[data-id=' + id + ']').addClass('added')
                    .find('button').attr('disabled', true)
