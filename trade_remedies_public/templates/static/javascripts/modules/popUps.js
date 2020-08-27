define([], function() {

    return {
        confirm:function(message, title) {
            return new Promise(function (resolve, reject) {
                require(['modules/Lightbox'], function(Lightbox) {
                    var lb = new Lightbox({
                        title: title || 'Confirm',
                        message: message,
                        buttons: {ok:1,cancel:1}
                    })
                    lb.getContainer().find('button').on('click',
                        function(evt) {
                            if($(evt.target).val() == 'ok') {
                                resolve()
                            } else {
                                reject();
                            }
                        }
                    );
                });
            })
        },

        alert:function(message, title) {
            return new Promise(function (resolve, reject) {
                require(['modules/Lightbox'], function(Lightbox) {
                    var lb = new Lightbox({
                        title: title || 'Information',
                        message: message,
                        buttons: {ok:1}
                    })
                    lb.getContainer().find('button').on('click',
                        function(evt) {
                            resolve()
                        }
                    );
                });
            })
        },

        error:function(message, title) {
            return new Promise(function (resolve, reject) {
                require(['modules/Lightbox'], function(Lightbox) {
                    var lb = new Lightbox({
                        title: title || 'Error',
                        message: message,
                        buttons: {ok:1}
                    })
                    lb.getContainer().find('button').on('click',
                        function(evt) {
                            resolve()
                        }
                    );
                });
            })
        }         
    }
})