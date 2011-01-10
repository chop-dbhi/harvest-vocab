require.def(['define/conceptmanager'], function(ConceptManager) {
    var equivalent = function(x,y)
    {   var p = null;
        for(p in y)
        {
            if(typeof(x[p])=='undefined') {return false;}
        }
        
        for(p in y)
        {
            if (y[p])
            {
                var objectType = typeof(y[p]);
                if ((objectType === "object")  && (y[p].constructor === Array)){
                    objectType = 'array';
                }
                
                switch(objectType)
                {       case 'array':
                                var otherObjectType = typeof(x[p]);
                                if (!((otherObjectType === "object") && (x[p].constructor === Array))){
                                   // not an array
                                   return false;
                                }
                                if (x[p] === undefined || y[p].length !== x[p].length){
                                    return false;
                                }
 
                                for (var i = 0; i < y[p].length; i++){
                                    var found = false;
                                    for (var j = 0; j < x[p].length; j++){
                                        if (equivalent(y[p][i],x[p][j])) found = true;
                                    }
                                    if (!found){
                                        return false;
                                    }
                                }
                                break;
                        case 'object':
                                if (!equivalent(y[p],x[p])) { return false; } break;
                        case 'function':break;
                               // if (typeof(x[p])=='undefined' || (p != 'equals' && y[p].toString() != x[p].toString())) { return false; }; break;
                        default:
                                if (y[p] != x[p]) { return false; }
                }
            }
            else
            {
                if (x[p])
                {
                    return false;
                }
            }
        }
        
        for(p in x)
        {
            if(typeof(y[p])=='undefined') {return false;}
        }
        
        return true;
    };
   
   var $dom_dummy = $("<div></div>");
   
   var api = { concept:"/api/criteria" };
   var criteria = {  
       vocabulary:{
           js:null,
           id:6,
           views:[{
                
                'elements':[{
                    'type': 'custom', 
                    'js'  :'static/js/vocabulary',
                    'css' :'../static/css/vocabulary.css',
                    'directory':'/browser/concept',
                    'folder' : 4,
                    'leaf' : 3,
                    'title': "Vocabulary",
                    'datatype': "string"
                }]
            }],
          'join_by': "or",
          'name' : "Browser"
       }
   };
   
   module("Vocabulary Browser");
   test("Load Vocab Browser.",1, function(){
        ConceptManager.show(criteria["vocabulary"]);
        ok(true,"Loaded");
    });
    
    
   // There is some odd behavior here when use requireJS with QUnit.
   // QUnit uses a Window Load event to fire the code that calls
   // QUnit.start(). Under more normal circumstances, by time
   // the event fires all of the test modules have run and been
   // added to QUnit.config.queue, so when QUnit.start() is called
   // all those test run. But when we use requireJS, the test
   // code does not run until after, and therefore the queue is empty
   // when QUnit.start is first called, so we call it here manually.
   QUnit.start();
});
