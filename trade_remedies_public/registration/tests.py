from django.test import TestCase

# from registration.views import RegisterView
from core.utils import validate
from core.validators import (
    registration_validators,
    base_registration_validators,
)


class TestPasswordValidation(TestCase):

    password_validation_test_cases = [
        # (password, is_valid, description)
        ("MyR£4lly$ecure_Pa$sw0rD", True, "Good password"),
        ("", False, "Blank not allowed"),
        ("2_$h0rT", False, "Too short (minimum 8 characters)"),
        ("L0ng£nuf", False, "Long enough (pound is not a special character)"),
        ("L0ng$nuf", True, "Long enough (minimum 8 characters)"),
        # Allow extremely long passwords.
        # Guidance is to have no max (design-system.service.gov.uk/patterns/passwords/)
        (
            "MyR£4lly$ecure_Pa$sw0rD".zfill(1000 - len("MyR£4lly$ecure_Pa$sw0rD")),
            True,
            "Good password 1000 characters",
        ),
        ("MyR£ally$ecure_Pa$sworD", False, "Must contain a digit"),
        ("my4£4lly$ecure_pa$sw0rd", False, "Must contain an uppercase letter"),
        ("MYR£4LLY$ECURE_PA$SW0RD", False, "Must contain a lowercase letter"),
        ("MyRe4llysecurePassw0rD", False, "Must contain a special character"),
        (
            "MyR本4lly本ecurePa本sw0rD",
            False,
            "Unicode characters allowed (but do not count as special characters)",
        ),
        (
            "MyR本4lly本ecurePa本sw0rD$",
            True,
            "Unicode characters allowed (but do not count as special characters)",
        ),
    ]

    def test_password_validator(self):
        for password, is_valid, description in self.password_validation_test_cases:
            with self.subTest(password=password, is_valid=is_valid, description=description):
                errors = validate(data={"password": password}, validators=registration_validators)
                password_errors = errors.get("password")
                if is_valid:
                    self.assertIsNone(password_errors)
                else:
                    self.assertIsNotNone(password_errors)


class TestEmailValidation(TestCase):

    test_cases = [
        # (email, is_valid, description)
        ("email@domain.com", True, "Basic"),
        ("eMail@dOmain.cOm", True, "Capitals allowed anywhere"),
        ("e本ail@d本main.c本m", True, "Unicode allowed anywhere"),
        ("eMai1l@dOmai9n.c0m", True, "Digits allowed"),
        ("email.domain.com", False, "No @"),
        ("email@domain.com.", False, "Symbol at end"),
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
