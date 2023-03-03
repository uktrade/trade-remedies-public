$('#show_password').click(function () {
  'use strict';

  if ($(this).attr('aria-checked') === 'false') {
    $(this).attr('aria-checked', 'true');
    $('#password').attr('type', 'text');
    $(this).find('span').html('Hide <span class="govuk-visually-hidden">password</span>');
    $("#password-text").html("Password shown.");
  } else {
    $(this).attr('aria-checked', 'false');
    $('#password').attr('type', 'password');
    $(this).find('span').html('Show <span class="govuk-visually-hidden">password</span>');
    $("#password-text").html("Password hidden.");
  }
});
