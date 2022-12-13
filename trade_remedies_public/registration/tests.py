import json

from django.test import TestCase
from django.urls import reverse

from .forms.forms import (
    RegistrationStartForm,
    TwoFactorChoiceForm,
    UkEmployerForm,
    YourEmployerForm,
    PasswordForm,
    NonUkEmployerForm,
    OrganisationFurtherDetailsForm,
)


class TestRegistrationStartForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "email": "test@example.com",  # /PS-IGNORE
            "name": "test",
            "terms_and_conditions_accept": "yes",
        }

    def test_start_form_email(self):
        form = RegistrationStartForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_start_form_wrong_email(self):
        self.mock_data.update({"email": "test.com"})
        form = RegistrationStartForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_start_form_no_name(self):
        self.mock_data.update({"name": ""})
        form = RegistrationStartForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_start_form_terms_and_conditions(self):
        self.mock_data.update({"terms_and_conditions_accept": ""})
        form = RegistrationStartForm(data=self.mock_data)
        self.assertFalse(form.is_valid())


class TestPasswordForm(TestCase):
    def test_password_valid(self):
        form = PasswordForm(data={"password": "J438jfd!@£xfk1:)"})  # /PS-IGNORE
        self.assertTrue(form.is_valid())

    def test_password_invalid_no_uppercase(self):
        form = PasswordForm(data={"password": "asdasf!!@dd53"})
        self.assertFalse(form.is_valid())

    def test_password_invalid_no_special(self):
        form = PasswordForm(data={"password": "asdsDAFSDF34334"})
        self.assertFalse(form.is_valid())

    def test_password_invalid_no_numbers(self):
        form = PasswordForm(data={"password": "ASDSDsdsdsd!!@£!@"})
        self.assertFalse(form.is_valid())

    def test_password_invalid_no_lowercase(self):
        form = PasswordForm(data={"password": "ADSFSDF!@£!@£43242"})
        self.assertFalse(form.is_valid())


class TestTwoFactorChoiceForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "two_factor_choice": "mobile",
            "mobile_country_code": "GB",
            "mobile": "02072222222",
        }

    def test_valid_form(self):
        form = TwoFactorChoiceForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_valid_email_selected(self):
        self.mock_data.update(
            {
                "two_factor_choice": "email",
            }
        )
        self.mock_data.pop("mobile_country_code")
        self.mock_data.pop("mobile")
        form = TwoFactorChoiceForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_invalid_no_mobile_provided(self):
        self.mock_data.pop("mobile")
        form = TwoFactorChoiceForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_no_mobile_country_code_provided(self):
        self.mock_data.pop("mobile_country_code")
        form = TwoFactorChoiceForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_mobile_number_max_length(self):
        self.mock_data["mobile"] = "073737213771723728"
        form = TwoFactorChoiceForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_mobile_number_incorrect_formatting(self):
        self.mock_data["mobile"] = "sd020722222222"
        form = TwoFactorChoiceForm(data=self.mock_data)
        self.assertFalse(form.is_valid())


class TestYourEmployerForm(TestCase):
    def test_valid(self):
        form = YourEmployerForm(data={"uk_employer": "no"})
        self.assertTrue(form.is_valid())

    def test_invalid_required(self):
        form = YourEmployerForm(data={})
        self.assertFalse(form.is_valid())

    def test_invalid_wrong_choice(self):
        form = YourEmployerForm(data={"uk_employer": "asd"})
        self.assertFalse(form.is_valid())


class TestUkEmployerForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "company_data": json.dumps(
                {
                    "address": {
                        "postal_code": "NNN NNN",
                        "locality": "London",
                        "address_line_1": "1 TEST ROAD",
                        "country": "United Kingdom",
                        "premises": "1",
                    },
                    "kind": "searchresults#company",
                    "title": "TEST COMPANY",
                    "address_snippet": "1 TEST ROAD, LONDON, UNITED KINGDOM, NNN NNN",
                    "company_number": "000000",
                }
            )
        }

    def test_valid_form(self):
        form = UkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())
        self.assertEqual("GB", form.cleaned_data["country"])
        self.assertEqual(
            "1 TEST ROAD, LONDON, UNITED KINGDOM", form.cleaned_data["address_snippet"]
        )
        self.assertEqual("000000", form.cleaned_data["company_number"])
        self.assertEqual("TEST COMPANY", form.cleaned_data["company_name"])

    def test_invalid_form_not_selected(self):
        self.mock_data["input-autocomplete"] = "trying to search for test"
        self.mock_data.pop("company_data")
        form = UkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_form_required(self):
        self.mock_data.pop("company_data")
        form = UkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())


class TestNonUkEmployerForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "company_name": "test company",
            "address_snippet": "1 test road, london, nnnnnn",
            "post_code": "nnnnnnn",
            "company_number": "000000",
            "country": "GB",
        }

    def test_valid(self):
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_name(self):
        self.mock_data.pop("company_name")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_missing_address(self):
        self.mock_data.pop("address_snippet")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_missing_post_code(self):
        self.mock_data.pop("post_code")
        self.mock_data.pop("company_number")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_valid_missing_company_number(self):
        # should still be valid as post code is present
        self.mock_data.pop("company_number")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_valid_missing_post_code(self):
        # should still be valid as company number is present
        self.mock_data.pop("post_code")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_country(self):
        self.mock_data.pop("country")
        form = NonUkEmployerForm(data=self.mock_data)
        self.assertFalse(form.is_valid())


class TestOrganisationFurtherDetailsForm(TestCase):
    def setUp(self) -> None:
        self.mock_data = {
            "organisation_website": "www.example.com",
            "vat_number": "UK00000000",
            "eori_number": "UK00000000",
            "duns_number": "000000000",
        }

    def test_valid_form(self):
        form = OrganisationFurtherDetailsForm(data=self.mock_data)
        self.assertTrue(form.is_valid())

    def test_invalid_website(self):
        self.mock_data["company_website"] = "example"
        form = OrganisationFurtherDetailsForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_company_eori_number(self):
        self.mock_data["company_eori_number"] = "4223"
        form = OrganisationFurtherDetailsForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_invalid_company_duns_number(self):
        self.mock_data["company_duns_number"] = "12"
        form = OrganisationFurtherDetailsForm(data=self.mock_data)
        self.assertFalse(form.is_valid())

    def test_valid_all_optional(self):
        self.mock_data = {}
        form = OrganisationFurtherDetailsForm(data=self.mock_data)
        self.assertTrue(form.is_valid())


class TestV2BaseRegisterView(TestCase):
    def test_session_update(self):
        self.assertNotIn("registration", self.client.session)
        post_data = {
            "email": "test@example.com",  # /PS-IGNORE
            "name": "test",
            "terms_and_conditions_accept": True,
        }
        self.client.post(reverse("v2_register_start"), data=post_data)
        self.assertIn("registration", self.client.session)
        self.assertEqual(self.client.session["registration"], post_data)

    def test_V2RegistrationViewYourEmployer_next_url(self):
        response = self.client.post(
            reverse("v2_register_your_employer"), data={"uk_employer": "yes"}
        )
        self.assertEqual(response.url, reverse("v2_register_your_uk_employer"))

        response = self.client.post(
            reverse("v2_register_your_employer"), data={"uk_employer": "no"}
        )
        self.assertEqual(response.url, reverse("v2_register_your_non_uk_employer"))
