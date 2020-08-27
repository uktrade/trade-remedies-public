// widget to upload a file
define(function() {
    "use strict";

    var constructor = function(el) {
        var self = this;
        this.el = el;
        el.on('change',_.bind(onChange,self));
        el.on('click',function(evt){trigger.call(self,evt)});
        this.container = el.closest('.file-panel');
        this.progressBar = this.container.find('.progress-bar > div');
        this.uploadProgress = _.bind(uploadProgress, this);
        this.replaceFileId = this.container.find('input[name="replace-file"]');
        //this.form = this.container.parents('form');
        this.container.on('click',_.bind(onClick,this));
        this.updateFileTable = _.bind(updateFileTable,this);
        this.dragTarget = this.container.find('.upload-target');
        this.uploader = this.container.find('.uploader');
        this.killDrag = _.bind(killDrag,this);
        this.dragTarget.on('dragenter',_.bind(onDragOver,this));
        this.dragTarget.on('dragover',_.bind(onDragOver,this));
        this.dragTarget.on('dragstart',_.bind(onDragOver,this));
        this.dragTarget.on('dragend',_.bind(endDrag,this));
        this.bodyDragOver = _.bind(bodyDragOver,this);

        this.onDrop = _.bind(onDrop,this);
    }

    constructor.prototype = {
        form: function() {
                this._form = this._form || this.el.closest('form');
            return this._form;
        }
    }

    function trigger(evt) {
        var self = this;
        var target = $(evt.target);
        var replaceFileId = target.closest('a').attr('data-replace-file');
        if(target.hasClass('file-upload') || replaceFileId) {
            self.replaceFileId.val(replaceFileId);
            if(!self.input) {
                self.input = this.container.find('input[type="file"]');
                self.input.on('change',function(evt) {
                    onChange.call(self,evt);
                });
            }
            self.input.trigger('click');
        }
    }

    function getDetails() {
        var outerForm = $('form.dd-form');
        return {
            csrfmiddlewaretoken: outerForm.find('input[name=csrfmiddlewaretoken]').val(),
            instance: outerForm.find('input[name=instance]').val(),
            page: outerForm.find('input[name=page]').val(),
            id: this.container.attr('data-id')
        }
    }
    function buildFileTable() {
        var self = this;
    }

    function updateFileTable(content) {
        var newEl = $(content);
        this.fileTable = this.fileTable || this.container.find('table.file-list');
        var old = this.container.find('table.file-list');
        old.after(newEl.find('table.file-list'));
        old.remove();
    }

    // Click on a delete icon
    function onClick(evt) {
        var target = $(evt.target);
        var aTag = target.closest('a.file-delete');
        var fileId = aTag.attr('data-fileid');
        if(fileId) {
            evt.preventDefault();
            var details = getDetails.call(this);
            details.fileId = fileId;
            details.action = 'delete';
            var data = [];
            _.each(details,function(value, key) {
                data.push({name:key, value:value});
            })
            $.ajax({
                url: 'file/',
                type: 'POST',
                contentType: "application/json",
                dataType: "json",
                data: data
            }).then(function(result) {
                aTag.closest('tr').remove();
            })
        }
    }

    function bodyDragOver(evt) {
        var target = $(evt.target);
        var over = target.closest('.drag-over')[0] === this.dragTarget[0];
        if(!over) {
            endDrag.call(this);
        }
    };

    function startDrag(evt) {
        this.dragging = true;
        $(document.body).on('dragover', this.bodyDragOver);
        $(document.body).on('', this.bodyDragOver);
        var dt = evt.originalEvent.dataTransfer
        var files = dt.items || dt.files;
        if(files.length > 1) {
            this.dragTarget.addClass('drag-bad');
            this.dragTarget.on('drop', this.killDrag);
            return;
        }
        this.dragTarget.removeClass('drag-bad');
        this.dragTarget.addClass('drag-over');
        this.dragTarget.on('drop', this.onDrop);
    };

    function endDrag() {
        this.dragging = false;
        this.dragTarget.removeClass('drag-over');
        this.dragTarget.removeClass('drag-bad');
        $(document.body).off('dragover',this.bodyDragOver);
        this.dragTarget.off('drop', this.onDrop);
    }

    function killDrag(evt) {
        endDrag.call(this);
        evt.preventDefault();
    }

    function onDragOver(evt) {
        evt.stopPropagation();
        evt.preventDefault();
        if(!this.dragging) {
            startDrag.call(this, evt);
        }
        evt.preventDefault();
        return true;
    };

    function addLine(file) {  // add a new line to the file table
        var html = this.lineTemplate;
        this.fileTable.removeClass('hidden');
        var row = this.files[file.name] = {name:file.name, size: file.size}
        _.each(this.files[file.name], function(val, key) {
            html = html.replace(new RegExp('{'+key+'}','g'), val);
        });
        var el = row.row = $(html);
        el.removeClass('hidden');
        this.fileTable.append(el);
        return row;
    }

    function setLoader(count) {
        this.uploader.addClass('uploading');
        this.container.find('.document-count').text(count);
        this.container.find('.document-s')[count == 1 ? 'hide' : 'show']();
    }

    function uploadFiles(files) {
        var self = this;
        if(files) {
            setLoader.call(this, files && files.length);
        }
        var details = getDetails.call(this);
        var action = this.form().attr('action');
        var formData = new FormData(this.form()[0]);
        _.each(files, function(file) {
            formData.append('file', file);
        });
        $.ajax(action, {
            type: 'POST',
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            xhr: function(){
                var xhr = $.ajaxSettings.xhr();
                xhr.upload.onprogress = self.uploadProgress;
                xhr.upload.onload = function(){ console.log('DONE!') } ;
                return xhr ;
            }
        }).then( function(content) {
            if (content.redirect_to) {
                document.location.replace(content.redirect_to);
            } else {
                document.open();
                document.write(content);
                document.close();
            }
        },
            function(error,type) {
                console.error(error);
                alert('An error occurred:'+(error || {}).statusText);
                document.location.reload()
            }
        );
    }

    function onDrop(evt) {
    // If files are dropped,we can't populate a file input, so we need to send them by Ajax.
    // We will post them all to the url in the form, then redirect on completion.
        endDrag.call(this);
        evt.preventDefault();
        var files = evt.originalEvent.dataTransfer.files;
        if(files.length > 1) {
            this.dragTarget.addClass('drag-bad');
            return;
        } else {
            uploadFiles.call(this, files)
        }
    };

    function uploadProgress(evt) {
        this.progressBar.css({'width':(evt.loaded/evt.total*100)+'%'});
        this.progressBar.closest('.upload-indicator').setClass('processing',evt.loaded==evt.total);
        this.progressBar.closest('.upload-indicator').setClass('loading',evt.loaded<evt.total);
    }

    function onChange(evt) {
    // Called when files are selected from a file element
        //var files = this.form().find('input[type="file"]')[0].files;
        var files = evt.target.files;
        setLoader.call(this, files && files.length);
        uploadFiles.call(this);  // note we don't send the file to upload as it's already in the form
    }
    return constructor;
});
