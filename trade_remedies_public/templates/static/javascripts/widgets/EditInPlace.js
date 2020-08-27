// widget to upload a file
define(function() {
    "use strict";

    var sbWidth;
	var constructor = function(el) {
		this.el = el;
        this.container = this.el.closest('.well, .section');
        this.sources = this.container.find('.editable');
        if(this.sources) {
		  el.on('click',_.bind(startEdit,this));
        }
	}

    function scrollBarWidth() {
        if(sbWidth) return sbWidth
        var el = $('<div></div>').css({width: '100px',height: '100px', overflow: 'scroll', 'position': 'absolute'}).appendTo(document.body);
        sbWidth = el[0].offsetWidth - el[0].clientWidth;
        el.remove();
        return sbWidth
    }

    function stopEdit(save) {
        if(this.fields) {
            _.each(this.fields, function(field) {
                if(save) {
                    field.source.html(field.editElement.val().replace(/\n/g,'<br>'));
                // TODO: save goes here
                }
                field.editElement.remove();
             })
            this.fields = null;
            this.saveCancel.remove();
            this.el.removeClass('js-hidden');
            this.container.off('focusout');
        }
    }

    function focusBack(evt) {
        var self = this;
        var ok = false;
        var to = evt.relatedTarget;
        ok = $(to).parents('.well, .section').is(this.container);


        /* _.each(this.fields, function(field) {
            // create an input for each item
            ok = ok || field.editElement[0] === to;
        }); */
        //console.log('OK',ok);
        //setTimeout(function() {self.editElement.focus(); return false},0);
        if(!ok) {
            setTimeout(function() {self.saveCancel.find('button').first().focus()},0);
        } else {
            console.log('related',to);
        }
    }

	function startEdit(state) {
        var self = this;
        if(!this.editElement) {
            // create save/cancel buttons
            this.saveCancel = $('<div class="edit-buttons"><button class="save"><img class="icon icon-tick"></button><button class="cancel"><img class="icon icon-cross"></button></div>');
            this.el.before(this.saveCancel);
            // attach handlers
            this.saveCancel.find('.save').on('click', function(){ stopEdit.call(self,true)});
            this.saveCancel.find('.cancel').on('click', function(){ stopEdit.call(self)});

            this.el.addClass('js-hidden');
            this.container.on('focusout',_.bind(focusBack,self));
            this.fields = [];
            this.sources.each(function(idx) {
                // create an input for each item
                var source = $(this);
                var editElement = $('<textarea class="inplaceEdit"/>')
                    //.on('focusout',bStopEdit);
                    //.on('focusout',_.bind(focusBack,self));
                source.css({'position':'relative'});
                var width = source.width();
                editElement.css({width:(scrollBarWidth()+width)+'px',height:'100%',position:'absolute',top:'-1px',left:'-1px',border:'none',resize:'none',zIndex:'1',overflowY:'scroll'/*,minHeight:'200px'*/});
                editElement.val(source.html().replace(/\<br\>/g,'\n'));
                source.append(editElement);
                if(idx == 0) {
                    editElement.focus();  /// focus the first one
                }
                self.fields.push({source:source,editElement:editElement});
            });
        }
	}

	
	return constructor;
});
