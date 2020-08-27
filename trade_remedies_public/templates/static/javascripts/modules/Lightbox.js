define(['modules/overlay'],function(overlay) {

    var requestAnimationFrame = window.requestAnimationFrame ||
        window.mozRequestAnimationFrame ||
        window.webkitRequestAnimationFrame ||
        function (fn) {
            return window.setTimeout(fn, 20);
        };

    function focusChange(e) {
        if($(e.target).closest('.pop-up').length == 0) {
            this.$el.focus();
        }
    }

    var template = _.template('<% if(title) { %><div class="title"><h1><%= title %></h1></div><% } %><div class="outer"><span><%= (message && (typeof(message) == "function" ? message(obj.data) : message)) || "" %></span></div>\
        <div class="button-container">\
        <% if(buttons.ok){ %><button type="button" value="ok" class="button dlg-close"><%=buttons.ok.txt || "OK" %></button><% } %>\
        <% if(buttons.cont){ %><button type="button" value="continue" class="button dlg-close" <%=buttons.cont=="disabled" ? "disabled=\'disabled\'" : \'\' %>>Continue</button><% } %>\
        <% if(buttons.cancel){ %><button type="button" value="" class="button btn-default dlg-close"><%=buttons.cancel.txt || "Cancel" %></button><% } %>\
        <% if(buttons.close){ %><button type="button" value="" class="button btn-default dlg-close">Close</button><% } %>\
        <% if(buttons.yes){ %><button type="button" value="yes" class="button dlg-close pull-left"><%=buttons.yes.txt || "Yes" %></button><% } %>\
        <% if(buttons.no){ %><button type="button" value="no" class="button btn-default pull-right dlg-close"><%=buttons.no.txt || "No" %></button><% } %>\
        </div>');

    var constructor = function(options) {
        // Options can contain:
        // content - the content to put in the box.  If not supplied, it uses the standard dialogue content
        // title - optional
        // data - optional.  rendered by the message if it's a template.
        // buttons - optional e.g. {ok:1,cancel:1}

        var self = this,
            bsClass = '';
        this.options = options || {};
        this.options.type = this.options.type || {};
        if(!this.options.content) {  // build a dialoge from the templates
            this.options = _.extend({buttons:{ok:1},type:{infonly:1}},options);
            this.options.addClose = 1;
            this.options.content = template(this.options);
        }

        if(options && options.type && options.type.infonly) this.options.type.infonly = this.options.options.type.infonly || null; // what?

        //if type infonly, we need to insert the bootstrap class for the required width
        if(this.options.type.infonly) bsClass = ' col-sm-6';
        
        this.$el = $('<div aria-live="assertive" role="alert" class="pop-up'+bsClass+'" tabindex="-1"></div>');
        this.$outer = $('<div class="outer"></div>');

        this.$overlay = overlay.createOverlay();

        if (this.options.addClose) {
            this.$header = $('<div class="pop-up-header"></div>');
            this.$el.append(this.$header);
            this.$header.append('<button class="dlg-close"><span class="icon icon-cross"></span><span class="sr-only">Close the dialogue</span></button>')
        }
        this.$el.append(this.$outer);
        this.$outer.append(this.options.content);
        // Dont think this is needed right now..
        // if(_.isElement(content)) {
        //     this.$el.append(content);
        // } else {
        //     this.$el.html(content);
        // };
        this.$overlay.addClass('overlay').append(this.$el).prependTo(document.body);

        this.centreBnd = _.bind(this.centre,this);
        //if type infonly, we need to let this.centre know not to compute hight/width styles
        if(this.options.type.infonly) {
            this.centre({infonly:this.options.type.infonly});
        } else {
            this.centre();
        }

        $(window).on('resize',this.centreBnd);

        this.$el.on('click', function(e) {
            e.stopPropagation();
            if($(e.target).closest('.dlg-close').length > 0) {
                self.close();
            }
        }).on('keyup',function(e) {
            if(e.keyCode === 27) {
                self.close();
            }
        });
        $('html').on('focusin', _.bind(focusChange, this));
        _.defer(function() {
            self.$el.focus();
        });
        this.resizeMonitor = _.bind(this.resizeMonitor,this);
        this.resizeMonitor();
        if(this.options.buttons) {
            deferred = $.Deferred();
            this.$el.find('button').on('click',function() {
                deferred.resolve(this.value,self);
            });
            this.promise = deferred.promise();
        }
    }

    constructor.prototype = {
        close: function() {
            this.$el.remove();
            overlay.destroyOverlay(this.$overlay);
            $(window).off('resize',this.centreBnd);
        },
        show: function() {
        },
        getContainer: function() {
            return this.$el;
        },
        centre: function(options) {
            var gap = 20;
                this.options = _.extend(this.options || {} ,options);
            if(this.options.infonly) this.$el.css({top:'auto',left:'auto'});
            if(!this.options.infonly) this.$el.css({height:'auto',width:'auto',top:'auto',left:'auto'});

            if(this.$el.height() > this.$overlay.height()-gap) {
                this.$el.css({height:(this.$overlay.height()-gap)+'px',overflow:'auto'});
            }
            if(this.$el.width() > this.$overlay.width()-gap) {
                this.$el.css({width:(this.$overlay.width()-gap)+'px',overflow:'auto'});
            }
            this.$el.css({left:(this.$overlay.width() - this.$el.width())/2, top:(this.$overlay.height() - this.$el.height())/2});
            this.size = {height:this.$el.height(), width:this.$el.width()};            
        },
        resizeMonitor: function() {
            var size = {height:this.$el.height(), width:this.$el.width() };
            this.size = this.size || size;
            if(this.size.height != size.height || this.size.width != size.width) {
                this.size = size;
                this.centre();
            }
            requestAnimationFrame(this.resizeMonitor);
        }
    }
    return constructor;
});



