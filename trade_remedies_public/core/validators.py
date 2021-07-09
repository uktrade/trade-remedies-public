#  RFC 2822 validator
email_validator = "(?:[\\w!#$%&'*+/=?^_`{|}~-]+(?:\\.[\\w!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[\\w](?:[\\w-]*[\\w])?\\.)+[\\w](?:[\\w-]*[\\w])?|\\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[\\w-]*[\\w]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\\])$"  # noqa: E501

review_form_validators = [
    {"key": "reference_case", "message": "You must select a case", "re": ".+"},
    {"key": "review_type", "message": "You must select a review type", "re": ".+"},
]
company_form_validators = [
    {"key": "organisation_name", "message": "The company name is required", "re": ".+"},
    {"key": "organisation_address", "message": "The company address is required", "re": ".+"},
    {
        "key": "duns_number",
        "message": "The duns number should be exactly 9 digits",
        "re": "^(?:\\d{9})?$",
    },
    {
        "key": "organisation_website",
        "message": "Your website should be a complete, valid URL.",
        "re": "^((?:http(s)?:\\/\\/|)[\\w.-]+(?:\\.[\\w\\.-]+)+[\\w\\-\\._~:/?#[\\]@!\\$&'\\(\\)\\*\\+,;=.]+)?$",  # noqa: E501
    },
]

registration_validators = [
    {"key": "name", "message": "Name is mandatory", "re": ".+"},
    {"key": "email", "message": "Email address is mandatory", "re": ".+"},
    {"key": "email", "message": "Email address is invalid", "re": email_validator},
    {"key": "country", "message": "You must select your country", "re": ".+"},
    {"key": "password", "message": "You must provide a password", "re": ".+"},
    {
        "key": "password",
        "message": "The password is too short. It must contain at least 8 characters",
        "re": "^\\S{8}",
    },
    {
        "key": "password",
        "message": "Password must include both upper and lowercase characters",
        "re": "(?=.*[a-z])(?=.*[A-Z])",
    },
    {"key": "password", "message": "Password must include at least one digit", "re": "(?=.*[0-9])"},
    {
        "key": "password",
        "message": "Password must include at least one special character (!\"$%&'()*+,-./:;<=>?@[\\]^_`{|}~])",  # noqa: E501
        "re": "(?=.*[!\"$%&'#()*+,-./:;<=>?@[\\\\\\]^_`{|}~])"
        # 're': '(?=.*[^a-zA-Z0-9\\s])'
    },
    {"key": "password_confirm", "message": "You must provide a password confirmation", "re": ".+"},
    {
        "key": "phone",
        "message": "Your phone number is invalid",
        "re": "^([0|\\+[0-9\s]{1,5})?([0-9\s]{4,13})?$",  # noqa: W605
    },
    {"key": "terms", "message": "You must agree to the terms and conditions", "re": ".+"},
]

base_registration_validators = [
    {"key": "email", "message": "You must enter your email address", "re": ".+"},
    {"key": "email", "message": "Your email address is invalid", "re": email_validator},
    {"key": "password", "message": "You must enter your password", "re": ".+"},
]

user_create_validators = [
    {"key": "name", "message": "You must enter a name", "re": ".+"},
    {"key": "email", "message": "You must enter an email address", "re": ".+"},
    {"key": "email", "message": "This email address is invalid", "re": email_validator},
    {"key": "phone", "message": "You must enter a mobile phone number", "re": ".+"},
    {"key": "address", "message": "Address is required", "re": ".+"},
    {
        "key": "phone",
        "message": "This phone number is invalid",
        "re": "^([0|\\+[0-9\s]{1,5})?([0-9\s]{4,13})?$",  # noqa: W605
    },
    {
        "key": "selected_country_code",
        "message": "You must select a country",
        "re": ".+",
    },
]

third_party_validators_base = [
    {"key": "name", "message": "You must enter a name", "re": ".+"},
    {"key": "email", "message": "You must enter an email address", "re": ".+"},
    {"key": "email", "message": "This email address is invalid", "re": email_validator},
    {"key": "organisation_name", "message": "Company name is required", "re": ".+"},
    {"key": "organisation_address", "message": "Company address is required", "re": ".+"},
]

third_party_validators_uk = [
    {"key": "companies_house_id", "message": "Company number is required", "re": ".+"},
]

third_party_validators_non_uk = [
    {"key": "country_code", "message": "You must select a country", "re": ".+"},
]
