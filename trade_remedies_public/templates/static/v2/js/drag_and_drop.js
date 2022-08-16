function file_upload(upload_container, files, submission_id) {
    // First remove all previous error states (if applicable)
    upload_container.find('.waiting_for_upload').removeClass('govuk-form-group--error')
    upload_container.find('.govuk-error-message').hide()

    if (files.length > 1) {
        // More than 1 file
        return false;
    }

    const input_element = upload_container.find("input[type='file']")
    input_element.files = files;

    const action = `${window.location.origin}/documents/document/`
    const form_data = new FormData();
    const file_data = input_element.files[0];
    form_data.append('files', file_data);
    form_data.append('type', upload_container.data("type"));
    form_data.append('submission_id', submission_id);
    form_data.append('unique_id', upload_container.attr('id'));
    if (upload_container.attr('data-parent-document')) {
        form_data.append('parent', upload_container.attr('data-parent-document'));
    }
    if (upload_container.attr('data-submission-document-type')) {
        form_data.append('submission_document_type', upload_container.attr('data-submission-document-type'));
    }
    $.ajax(action, {
        type: 'POST',
        data: form_data,
        headers: {
            'X-CSRFToken': upload_container.data("csrf"),
        },
        cache: false,
        contentType: false,
        processData: false,
        beforeSend: function () {
            let file_name = file_data.name
            if (file_name.length > 35) {
                // Truncate the file name as it looks ugly when it's so long
                file_name = `${file_name.substring(0, 18)}...${file_name.substring(file_name.length - 18, file_name.length)}`
            }
            upload_container.find(".file_name").html(file_name)
        },
        xhr: function () {
            // Progressing the progress bar as the upload happens
            var xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener('loadstart', function () {
                upload_container.find(".file_upload_indicator").hide()
                upload_container.find(".uploading_file").show()
            });
            xhr.upload.addEventListener('progress', function (e) {
                if (e.lengthComputable) {
                    const percentageComplete = (e.loaded / e.total) * 100;
                    if (percentageComplete === 100) {
                        // Once complete, show the virus scanning indicator. This has technically already happened in
                        // the backend.
                        upload_container.find('.file_upload_indicator').hide()
                        upload_container.find('.scanning_file').show()
                    } else {
                        upload_container.find('.progress').val(percentageComplete)
                        upload_container.find('.upload_percentage').html(`${Math.round(percentageComplete)}%`)
                    }
                }
            });
            return xhr;
        },
        success: function (data) {
            upload_container.find(".file_upload_indicator").hide()
            upload_container.find(".upload_file_complete").show()
            upload_container.find(".uploaded_file").show()
            upload_container.find('.delete_document_link').data('document-id', data['uploaded_files'][0]['id']).attr('data-document-id', data['uploaded_files'][0]['id']);

            const part_of_pair = upload_container.closest('.confidential_and_non_confidential_file_row')
            if (part_of_pair) {
                // If this file was uploaded as part of a pair of confidential and non-confidential files, we need
                // to update the data-parent-document attribute of the other file upload field in the pair, so the
                // backend is able to associate and link the 2 files together
                const type_of_document = upload_container.data('type')
                const type_reverse = {
                    'confidential': 'non_confidential',
                    'non_confidential': 'confidential'
                }
                const reversed_type = type_reverse[type_of_document]
                const other_file_upload_container = part_of_pair.find(`.${reversed_type}_file_row`).find('.upload_container')
                other_file_upload_container.data('parent-document', data['uploaded_files'][0]['id']).attr('data-parent-document', data['uploaded_files'][0]['id'])
            }
        },
        error: function (xhr) { // if error occurred
            // There was an error uploading the file, display them
            upload_container.find('.file_upload_indicator').hide()
            upload_container.find('.waiting_for_upload').show()
            $.each(xhr.responseJSON["errors"]["file"], function (index, error) {
                upload_container.find('.file_error_message').text(error)
            })
            upload_container.find('.waiting_for_upload').addClass('govuk-form-group--error')
            upload_container.find('.govuk-error-message').show()


        },
        complete: function () {
        },
    })
}

$(document).on('change', 'input[type="file"]', function () {
    const upload_container = $(this).closest('.upload_container')
    const submission_id = upload_container.attr("data-submission-id")
    file_upload(upload_container, this.files, submission_id)
})

$(document).on('drop dragdrop', '.upload_container', function (e) {
    $(this).closest('.upload-card').removeClass('upload-card-hover')
    const submission_id = $(this).data("submission-id")
    const original_event = e.originalEvent
    e.preventDefault()
    e.stopPropagation()

    file_upload($(this), original_event.dataTransfer.files, submission_id)
})

$(document).on('dragover', '.upload_container', function (e) {
    e.preventDefault()
    e.stopPropagation()
    $(this).closest('.upload-card').addClass('upload-card-hover')
})

$(document).on('dragleave', '.upload_container', function (e) {
    e.preventDefault()
    e.stopPropagation()
    $(this).closest('.upload-card').removeClass('upload-card-hover')
})

$(document).on('click', '.delete_document_link', function (e) {
    e.preventDefault()
    e.stopPropagation()

    const upload_container = $(this).closest(".upload_container")
    const document_id = $(this).data('document-id')
    const action = `${window.location.origin}/documents/document/?document_to_delete=${document_id}`


    $.ajax(action, {
        type: 'DELETE',
        headers: {
            'X-CSRFToken': upload_container.data("csrf"),
        },
        cache: false,
        contentType: false,
        processData: false,
        success: function (data) {
            upload_container.find(".file_upload_indicator").hide()
            upload_container.find('.waiting_for_upload').show()
        },
        error: function (xhr) { // if error occured
            alert("Error occurred.please try again");
        },
        complete: function () {
        },
    })
})

$('#add_document_button').click(function (e) {
    // Cloning the last document field
    const new_document_field = $(".document_field").last().clone()
    new_document_field.appendTo("#registration_documents");
    new_document_field.find(".govuk-form-group--error").removeClass("govuk-form-group--error")
    new_document_field.find(".file_error_message").html("")

    $.each(new_document_field.find('.upload_container'), function () {
        // For each of the upload containers in the new row, we want to change the ID and clear any previously
        // set attributes
        let new_upload_container_id = Math.random().toString(36).slice(2, 7);
        $(this).prop("id", new_upload_container_id)
        $(this)[0].removeAttribute('data-parent-document')
        $(this).find('.delete_document_link').data('document-id', null).attr('data-document-id', null)
    })

    // Creating 2 new random strings to set as the ID for each of the confidential and non-confidential file fields
    const random_1 = Math.random().toString(36).slice(2, 7);
    const random_2 = Math.random().toString(36).slice(2, 7);

    new_document_field.find('input[type="file"][data-type="non_confidential"]').prop("id", `file-${random_1}`).prop("name", `file-non_confidential-${random_1}`)
    new_document_field.find('input[type="file"][data-type="non_confidential"]').parent().find("label").prop("for", `file-${random_1}`)
    new_document_field.find('input[type="file"][data-type="confidential"]').prop("id", `file-${random_2}`).prop("name", `file-confidential-${random_2}`)
    new_document_field.find('input[type="file"][data-type="confidential"]').parent().find("label").prop("for", `file-${random_2}`)


    new_document_field.find(".file_upload_indicator").hide()
    new_document_field.find('.waiting_for_upload').show()

    new_document_field.appendTo("#registration_documents");
    show_remove_document_buttons()
})

function show_remove_document_buttons() {
    $('.remove_document_panel').hide()
    $('.remove_document_panel:not(:first)').show()
}

show_remove_document_buttons()

$(document).on("click", ".remove_document_link", function (e) {
    e.preventDefault()
    e.stopPropagation()

    $(this).closest(".document_field").find(".delete_document_link:visible").click() // Deleting documents
    $(this).closest(".document_field").remove()  // Deleting the document panel from DOM
})
