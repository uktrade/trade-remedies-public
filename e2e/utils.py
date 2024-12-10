import os
import random
import string
import inspect
import re
import time
import pytest

from functools import wraps

def get_base_url():
    return os.getenv("BASE_FRONTEND_TESTING_URL", "http://localhost:8002/")

def clean_full_url(url):
    """Clean a URL by removing multiple slashes and trailing slash."""

    # Split the URL into protocol and the rest.
    if "://" in url:
        protocol, rest = url.split("://", 1)
        # Clean the 'rest' part of the URL by replacing multiple slashes with a single one.
        rest = re.sub(r"/+", "/", rest)
        # Remove trailing slash if present
        if rest.endswith('/'):
            rest = rest[:-1]
        # Concatenate the protocol and the cleaned part back together.
        cleaned_url = f"{protocol}://{rest}"
    else:
        # If there's no protocol, just clean the URL directly.
        cleaned_url = re.sub(r"/+", "/", url)
        # Remove trailing slash if present
        if cleaned_url.endswith('/'):
            cleaned_url = cleaned_url[:-1]
    return cleaned_url


def retry(tries=3, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff."""

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            # Get argument names of the function
            arg_names = inspect.getfullargspec(f).args

            # Run the function with retries
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except TimeoutError as e:
                    msg = f"{e}, Retrying in {mdelay} seconds..."
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff

            # Final attempt
            return f(*args, **kwargs)

        # If the function expects a fixture named 'request', assume it's a pytest test
        if "request" in inspect.getfullargspec(f).args:
            # Use pytest's request fixture to modify the function with retry logic
            @pytest.fixture
            def wrapper(request, *args, **kwargs):
                # Modify the test function by injecting the retry decorator
                return f_retry(*args, **kwargs)

            return wrapper
        else:
            return f_retry

    return deco_retry


def generate_test_name():
    """Generate a random sample user name."""
    prefix = "user_"
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return prefix + suffix


def generate_test_email():
    """Generate a random sample email address."""
    prefix = "test_"
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    name = ".".join([prefix, suffix])
    domain = "@gov.uk"
    return name + domain


def generate_test_password():
    """Generate a random sample password with at least 8 characters."""
    # password needs to be in the format
    # capital letter, lowercase letter, number, special character
    password = ''.join(random.choices(string.ascii_uppercase, k=1))
    password += ''.join(random.choices(string.ascii_lowercase, k=1))
    password += ''.join(random.choices(string.digits, k=1))
    password += ''.join(random.choices(string.punctuation, k=1))
    password += ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=4))
    return password


def generate_test_address():
    """Generate a random address."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


def genetrate_test_postcode():
    """Generate a random postcode."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
