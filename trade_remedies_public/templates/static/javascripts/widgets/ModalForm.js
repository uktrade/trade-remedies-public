// Typeahead - using the jqueryUI autocomplete widget
define(['modules/popUps'], function(popups) {
    "use strict";
	var constructor = function(el) {
        this.el = el;
        el.on('click', _.bind(onClick,this))
        this.url = el.attr('data-url');
        var blockId = el.attr('data-block-id');
        if(blockId) {
            this.element = $('#'+blockId);
        }
	}
    var semaphore;

    function formSubmit(evt) {
//        if(semaphore) return;
        evt.preventDefault();
        var form = evt.target;
        var submitMode = $(form).attr('data-submit-mode');
        if(!(form.validate || _.noop)()) {
            var data = $(form).find('input[type=hidden],:input:not(:hidden)').serializeArray();
            console.log('URL', self.submitMode, $(form).attr('action'), $(form).attr('method'))
            $.ajax({
                method: $(form).attr('method') || 'POST',
                url: $(form).attr('action'),
                data: data
            }).then(function(result) {
                if (result.error) {
                    alert(JSON.stringify(result.error))
                } else if (result.redirect_url) {
                    location.assign(result.redirect_url)
                } else if (result) {
                    $(form).closest('.outer').html(result);
                } else {
                    window.location.reload();
                }
            }, function(error) {
                console.error("ERROR", error)
                alert(JSON.stringify(error));
            })
        }
    }

    function onClick(evt) {
        evt.preventDefault();
        var self = this;
        self.url = self.el.attr('data-url');
        if(self.url) {
            // get the form from t'server
            $.ajax({
                url: self.url,
                method: 'get'
            }).then(function(res) {
                //var split = /\<form[^>]*\>((?:\s|.)*?)\<\/form\>/.exec(res);
                //var form = split && split[1] || 'dud';
                require(['modules/Lightbox'], function(Lightbox) {
                    self.dlg = new Lightbox({
                        title:'',
                        content:res,
                        buttons:{ok:1,cancel:1}
                    });
                    self.dlg.$outer.attachWidgets();
                    if (self.dlg.$outer.find('form').attr('data-submit-mode') != 'browser') {
                        self.dlg.$outer.find('form').on('submit', _.bind(formSubmit,self))
                    }
                });
            },function(res, res2) {
                if(res.status==403) {
                    location.reload(); // If the user is logged out, reload the page which will be redirected to the loging page
                } else {
                    popups.error(res.statusText);
                }
            });
        }
        if(self.element && self.element.length) {
            // grab hidden element
            require(['modules/Lightbox'], function(Lightbox) {
                self.dlg = new Lightbox({
                    title: '',
                    content: self.element.html(),
                    buttons: {ok:1,cancel:1}
                });
            });
        }
    }

	return constructor;
});
