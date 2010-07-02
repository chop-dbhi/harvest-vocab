// Initiate the main screen of the vocabulary browser
// The first thing to be displayed is always the root category
(function(){  // $target refers to the div on screen where the concept will be displayed
    var $target = $(document.createElement("div"));
    
    var prefix = "/static/plugins/vb";
    
    var reloadBrowser = function(category){
       $.get(prefix+'/browse/'+category.replace("#",""), function(data){
               $target.find("#browser").empty().append($("#browse-template").jqote({nodes:data.nodes}));
               $target.find('#nav').empty().html($("#breadcrumbs-template").jqote({path:data.path}));
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
    $target.find('a[href]').live("click", function(){
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
                $receiver.append($("#results_template").jqote(value));
            });
        },
        error: function(){
            $input.removeClass("searchAjax").addClass("searchIdle");
        }
    }, 'Search criteria...').helptext('Search criteria...');
    
    $("body").trigger("widgetLoadedEvent", $target);
})();