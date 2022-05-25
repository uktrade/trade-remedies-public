$("#password").keyup(function () {
    if ($(this).val().length >= 8) {
        // It's 8 characters or more
        $("#length").addClass("valid")
    } else {
        $("#length").removeClass("valid")
    }

    if ($(this).val().match(/[a-z]/)) {
        // There are lowercase characters
        $("#letter").addClass("valid")
    } else {
        $("#letter").removeClass("valid")
    }

    if ($(this).val().match(/[A-Z]/)) {
        // There are uppercase characters
        $("#capital").addClass("valid")
    } else {
        $("#capital").removeClass("valid")
    }

    if ($(this).val().match(/[0-9]/)) {
        // There are uppercase characters
        $("#number").addClass("valid")
    } else {
        $("#number").removeClass("valid")
    }

    if ($(this).val().match(/[!"$%&\'#()*+,-./:;<=>?\\@[\]^_`{|}~]/)) {
        // There are special characters
        $("#special").addClass("valid")
    } else {
        $("#special").removeClass("valid")
    }
})