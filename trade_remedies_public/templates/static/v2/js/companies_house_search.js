/* globals accessibleAutocomplete: true */

function clearCompany() {
  "use strict";

  $('[name=company_data]').val("");
  $('#selected_company_wrapper').hide();
  $('#selected_company').text("");
}

$(document).on("keyup", '[name="input-autocomplete"]', function () {
  "use strict";

  if ($(this).val().trim().length === 0) {
    clearCompany();
  }
});

let proposed_names = {};

accessibleAutocomplete({
  element: document.querySelector('#company_search_container'),
  placeholder: "Enter a registered company name or number",
  id: 'my-autocomplete',
  autoselect: true,
  minLength: 3,
  confirmOnBlur: false,
  source: function (query, populateResults) {
    "use strict";

    if (query.trim().length < 3) {
      populateResults([]);
      clearCompany();
    } else {
      $.ajax({
        type: "GET", url: `/companieshouse/search?term=${query}`, success: function (data) {
          if (data) {
            let names = data.map(result => `${result.title} (${result.company_number})`);
            proposed_names = Object.fromEntries(data.map(result => [`${result.title} (${result.company_number})`, result]));
            populateResults(names);
            if (names.length === 0) {
              clearCompany();
            }
          }
        }, error: function () {

        }
      })
        .fail(function () {
          if (!document.getElementById('companies-house-error')) {
            $('main.govuk-main-wrapper').prepend(`
              <div class="govuk-error-summary" id="companies-house-error" aria-labelledby="error-summary-title"
                role="alert" data-module="govuk-error-summary" tabindex="-1">
                <h2 class="govuk-error-summary__title" id="error-summary-title">
                  There is a problem
                </h2>
                <div class="govuk-error-summary__body">
                  <ul class="govuk-list govuk-error-summary__list">
                    <li>
                      <a href="#company_data">Companies House search is currently not working</a>
                    </li>
                  </ul>
                </div>
              </div>
            `);
            $('div.govuk-form-group').addClass('govuk-form-group--error');
            $('div.govuk-hint').after(`
              <p id="uk_employer-error" class="govuk-error-message">
                <span class="govuk-visually-hidden">Error:</span> The Companies House search is currently not working.
                Try again shortly, or <a class="govuk-link" href="../no">enter your organisation details manually</a>.
              </p>
            `);
            $('button.govuk-button').after('<a class="govuk-button" href="../no">Add company details manually</a>').remove();
          }
        });
    }
  },
  onConfirm: function (confirmed_name) {
    "use strict";

    if (typeof (confirmed_name) !== "undefined") {
      const selected_company_wrapper = $('#selected_company_wrapper');
      const selected_company = $('#selected_company');

      if (confirmed_name in proposed_names) {
        let company_data = proposed_names[confirmed_name];

        $('[name=company_data]').val(JSON.stringify(company_data));

        selected_company_wrapper.show();
        selected_company.text(`${company_data.title} (${company_data.company_number}) ${company_data.address_snippet}`);
        return true;
      }
      selected_company_wrapper.hide();
      selected_company.text('');
    }
  }
});
