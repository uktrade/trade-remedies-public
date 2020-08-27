// Tab controller
define([],function() {

    var constructor = function(el,options) {
        // Options can contain:
        var self = this;
        this.options = options;
        this.tabset = el;
        this.tabset.on('click',_.bind(onClick,this))
    }

    function onClick(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        var aTag = $(evt.target).closest('a');
        var href = aTag.attr('href');
        var tab = aTag.attr('data-tab');
        (this.options.actions[tab] || _.noop)();
    }

    return constructor;
});



