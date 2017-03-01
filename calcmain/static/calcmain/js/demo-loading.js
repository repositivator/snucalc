$(function(){

    /***************************************************************************
        Quick Demo
    ***************************************************************************/
    $("#quick_demo").on("click", function(event){
        $.LoadingOverlay("show");
        setTimeout(function(){
            $.LoadingOverlay("hide");
        }, 3000);
    });



    /***************************************************************************
        Example 1
    ***************************************************************************/
    $("#loading").on("click", function(event){
        $.LoadingOverlay("show");
        // setTimeout(function(){
        //     $.LoadingOverlay("hide");
        // }, 3000);
    });



    /***************************************************************************
        Example 2
    ***************************************************************************/
    var _example2Active = false;
    $("#example2a").on("click", function(event){
        if (_example2Active) return false;
        var element = $(event.currentTarget).parent().prev();
        _example2Active = true;
        element.LoadingOverlay("show", {
            color   : "rgba(165, 190, 100, 0.5)"
        });
        setTimeout(function(){
            element.LoadingOverlay("hide", true);
            _example2Active = false;
        }, 3000);
    });

    $("#example2b").on("click", function(event){
        if (_example2Active) return false;
        var element = $(event.currentTarget).parent().prev();
        var h       = element.height();
        var w       = element.width();
        _example2Active = true;
        element.LoadingOverlay("show", {
            color           : "rgba(165, 190, 100, 0.5)",
            size            : "30%",
            resizeInterval  : 50
        });
        element.animate({
            height  : h * 2,
            width   : w / 2
        }, 2500, function(){
            element.animate({
                height  : h,
                width   : w
            }, 2500, function(){
                element.LoadingOverlay("hide").css({
                    height  : "",
                    width   : ""
                });
                _example2Active = false;
            })
        });
    });



    /***************************************************************************
        Example 3
    ***************************************************************************/
    $("#example3").on("click", function(event){
        $.LoadingOverlay("show", {
            image       : "",
            fontawesome : "fa fa-spinner fa-spin"
        });
        setTimeout(function(){
            $.LoadingOverlay("hide");
        }, 3000);
    });



    /***************************************************************************
        Example 4
    ***************************************************************************/
    $("#example4").on("click", function(event){
        var count           = 5;
        var customElement   = $("<div>", {
            id      : "countdown",
            css     : {
                "font-size" : "50px"
            },
            text    : count
        });

        $.LoadingOverlay("show", {
            image   : "",
            custom  : customElement
        });

        var interval = setInterval(function(){
            count--;
            customElement.text(count);
            if (count <= 0) {
                clearInterval(interval);
                $.LoadingOverlay("hide");
                return;
            }
        }, 1000);
    });



    /***************************************************************************
        Example 6
    ***************************************************************************/
    $("#example6").on("click", function(event){
        $.LoadingOverlay("show", {
             fade  : [2000, 1000]
        });
        setTimeout(function(){
            $.LoadingOverlay("hide");
        }, 5000);
    });



    /***************************************************************************
        Extra Progress 1
    ***************************************************************************/
    $("#extraprogress1").on("click", function(event){
        var progress = new LoadingOverlayProgress();
        $.LoadingOverlay("show", {
            custom  : progress.Init()
        });
        var count     = 0;
        var interval  = setInterval(function(){
            if (count >= 100) {
                clearInterval(interval);
                delete progress;
                $.LoadingOverlay("hide");
                return;
            }
            count++;
            progress.Update(count);
        }, 300);
    });


});
