require.def(function(){
    // This is the beginning of something - JMM
    function FrontDesk(){
        
        var guests = 0;
        var empty = [];
        var full = 0;
        
        this.onEmpty = function(cb){
            empty.push(cb);
        };
        
        this.onFull = function(cb){
            full.push(cb);
        };
        
        this.checkIn = function(){
            guests++;
        };
        
        this.checkOut = function(){
            guests--;
            if (guests === 0){
                $.each(empty, function(index, element){
                    element();
                });
            }
        };   
    }
    return FrontDesk;
});