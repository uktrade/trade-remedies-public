from django.test import TestCase

from core.utils import validate
from core.validators import (
    registration_validators,
    base_registration_validators,
)


class TestEmailValidation(TestCase):

    test_cases = [
        # (email, is_valid, description)
        ("email@domain.com", True, "Basic"),  # /PS-IGNORE
        ("eMail@dOmain.cOm", True, "Capitals allowed anywhere"),  # /PS-IGNORE
        ("e本ail@d本main.c本m", True, "Unicode allowed anywhere"),  # /PS-IGNORE
        ("eMai1l@dOmai9n.c0m", True, "Digits allowed"),  # /PS-IGNORE
        ("email.domain.com", False, "No @"),  # /PS-IGNORE
        ("email@domain.com.", False, "Symbol at end"),  # /PS-IGNORE
    ]

    def test_email_validator(self):
        for email, is_valid, description in self.test_cases:
            with self.subTest(email=email, is_valid=is_valid, description=description):
                errors = validate(data={"email": email}, validators=base_registration_validators)
                email_errors = errors.get("email")
                if is_valid:
                    self.assertIsNone(email_errors, description)
                else:
                    self.assertIsNotNone(email_errors, description)
