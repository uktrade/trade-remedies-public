// Progressive enhancement produces lightbox with list of organisations
define(function() {
    "use strict";
	var constructor = function(el) {
        var self = this;
        this.el = el;
        this.a_tag = el.closest('li').find('a')
        this.a_tag.on('click', _.bind(showLightbox,this));
	}

    function showLightbox(evt) {
        evt.preventDefault();
        var content = this.el.html();
        var csrfmiddlewaretoken = window.dit.csrfToken;
        require(['modules/Lightbox'], function(Lightbox) {
            var title = "Choose an organisation";
            var message = renderForm(content);
            var lb = new Lightbox({title:title, message:message, buttons:{ok:{txt: "Submit"}}});
            lb.getContainer().find('button[value="ok"]').removeClass('dlg-close').on('click', function(){
                var $form = $('body').find('.overlay.active form') || {};
                var $field = $('[name="organisation_id"]:checked, [name="next"]:checked');
                return $field.length > 0 ? $form.submit() : showErrors($form);
            });
        });
    }

    function showErrors($form) {
        $form
            .find('.form-group')
            .addClass('form-group-error')
            .find('.error-message')
            .css('display', 'block')
            .focus();
        return false;
    }

    function renderForm(content) {
        var html = '\
            <form method="POST" action="/organisation/set/">\
                <div class="form-group">\
                    <fieldset>\
                        <legend class="sr-only">\
                            <h1 class="heading-medium">Choose an organistion</h1>\
                        </legend>\
                        <span class="error-message" style="display:none;">\
                            Choose an organisation\
                        </span>';
        html += content;
        html += '</fieldset></div></form>';
        return html;
    }

    return constructor;
});
