from unittest import TestCase

from .forms import (
    PrimaryContactForm,
    ClientTypeForm,
    YourEmployerForm,
    UkEmployerForm,
    NonUkEmployerForm,
    ClientFurtherDetailsForm,
)


class TestClientTypeForm(TestCase):
    def test_valid_org_type(self):
        form = ClientTypeForm(data={"org": "new-org"})
        self.assertTrue(form.is_valid())

    def test_invalid_org_type(self):
        form = ClientTypeForm(data={"org": "bad-org"})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"org": [{"message": "Select a valid choice. '
            'bad-org is not one of the available choices.", '
            '"code": "invalid_choice"}]}',
        )

    def test_no_org_type(self):
        form = ClientTypeForm(data={"org": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"org": [{"message": "no_org_chosen", ' '"code": "required"}]}',
        )


class TestPrimaryContactForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "email": "test@example.com",  # /PS-IGNORE
            "name": "test",
        }

    def test_valid_input(self):
        form = PrimaryContactForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        self.mock_data.update({"email": "test.com"})
        form = PrimaryContactForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"email": [{"message": "email_not_valid", ' '"code": "invalid"}]}',
        )

    def test_no_name(self):
        self.mock_data.update({"name": "", "email": "test@example.com"})  # /PS-IGNORE
        form = PrimaryContactForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"name": [{"message": "no_name_entered", ' '"code": "required"}]}',
        )

    def test_no_email(self):
        self.mock_data.update({"email": "", "name": "abc"})
        form = PrimaryContactForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"email": [{"message": "no_email_entered", ' '"code": "required"}]}',
        )


class TestYourEmployerForm(TestCase):
    def test_valid(self):
        form = YourEmployerForm(data={"uk_employer": "no"})
        self.assertTrue(form.is_valid())
        form = YourEmployerForm(data={"uk_employer": "yes"})
        self.assertTrue(form.is_valid())

    def test_invalid_required(self):
        form = YourEmployerForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"uk_employer": [{"message": "organisation_registered_country_not_selected", '
            '"code": "required"}]}',
        )

    def test_invalid_wrong_choice(self):
        form = YourEmployerForm(data={"uk_employer": "asd"})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"uk_employer": [{"message": "Select a valid choice. '
            'asd is not one of the available choices.", '
            '"code": "invalid_choice"}]}',
        )


class TestUkEmployerForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "organisation_post_code": "NNN NNN",
            "organisation_address": "1 TEST ROAD, NNN NNN, LONDON, UNITED KINGDOM",
            "companies_house_id": "000000",
            "organisation_name": "TEST COMPANY",
        }

    def test_valid_form(self):
        self.mock_data["input-autocomplete"] = "TEST"
        form = UkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                "organisation_name": "TEST COMPANY",
                "companies_house_id": "000000",
                "organisation_post_code": "NNN NNN",
                "organisation_address": "1 TEST ROAD, NNN NNN, LONDON, UNITED KINGDOM",
                "company_search_container": "",
            },
        )

    def test_companies_house_searched_but_not_selected(self):
        form = UkEmployerForm(data={"input-autocomplete": "TEST"})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"organisation_name": [{"message": "This field is required.",'
            ' "code": "required"}], '
            '"companies_house_id": [{"message": "This field is required.", '
            '"code": "required"}], '
            '"organisation_post_code": [{"message": "This field is required.",'
            ' "code": "required"}], '
            '"organisation_address": [{"message": "This field is required.",'
            ' "code": "required"}], '
            '"company_search_container": [{"message": "companies_house_not_selected",'
            ' "code": ""}]}',
        )

    def test_companies_house_not_searched(self):
        form = UkEmployerForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"organisation_name": [{"message": "This field is required.",'
            ' "code": "required"}], '
            '"companies_house_id": [{"message": "This field is required.",'
            ' "code": "required"}], '
            '"organisation_post_code": [{"message": "This field is required.",'
            ' "code": "required"}], '
            '"organisation_address": [{"message": "This field is required.",'
            ' "code": "required"}], '
            '"company_search_container": [{"message": "companies_house_not_searched",'
            ' "code": ""}]}',
        )


class TestNonUkEmployerForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "organisation_name": "test company",
            "address_snippet": "1 test road, london, nnnnnn",
            "post_code": "nnnnnnn",
            "company_number": "000000",
            "country": "GB",
        }

    def test_valid(self):
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_missing_name(self):
        self.mock_data.pop("organisation_name")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"organisation_name": [{"message": "no_client_name_entered",' ' "code": "required"}]}',
        )

    def test_missing_address(self):
        self.mock_data.pop("address_snippet")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"address_snippet": [{"message": "no_client_address_entered",'
            ' "code": "required"}]}',
        )

    def test_missing_post_code_and_company_number(self):
        self.mock_data.pop("post_code")
        self.mock_data.pop("company_number")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"company_number": [{"message": "no_client_post_code_or_number_entered", '
            '"code": ""}], '
            '"post_code": [{"message": "no_client_post_code_or_number_entered", '
            '"code": ""}]}',
        )

    def test_missing_company_number(self):
        # should still be valid as post code is present
        self.mock_data.pop("company_number")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_missing_post_code(self):
        # should still be valid as company number is present
        self.mock_data.pop("post_code")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_missing_country(self):
        self.mock_data.pop("country")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"country": [{"message": "no_client_country_selected", "code": "required"}]}',
        )


class TestClientFurtherDetailsForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "company_website": "www.example.com",
            "company_vat_number": "UK00000000",
            "company_eori_number": "UK00000000",
            "company_duns_number": "000000000",
        }

    def test_valid_form(self):
        form = ClientFurtherDetailsForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_invalid_website(self):
        self.mock_data["company_website"] = "example"
        form = ClientFurtherDetailsForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"company_website": [{"message": "incorrect_client_url",' ' "code": "invalid"}]}',
        )

    def test_invalid_company_eori_number(self):
        self.mock_data["company_eori_number"] = "4223"
        form = ClientFurtherDetailsForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"company_eori_number": [{"message": "incorrect_client_eori_format",'
            ' "code": "invalid"}]}',
        )
        self.mock_data["company_eori_number"] = "4223333333333"
        form = ClientFurtherDetailsForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"company_eori_number": [{"message": "incorrect_client_eori_format",'
            ' "code": "invalid"}]}',
        )

    def test_invalid_company_duns_number(self):
        self.mock_data["company_duns_number"] = "12"
        form = ClientFurtherDetailsForm(data=self.mock_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.as_json(),
            '{"company_duns_number": [{"message": "incorrect_client_duns_format",'
            ' "code": "invalid"}]}',
        )

    def test_valid_all_optional(self):
        self.mock_data = {}
        form = ClientFurtherDetailsForm(data=self.mock_data)
        self.assertTrue(form.is_valid())
