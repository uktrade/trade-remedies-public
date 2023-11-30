import dpath
import datetime
from django.conf import settings
from django.http import StreamingHttpResponse
from django.shortcuts import redirect
from django.utils.http import is_safe_url  # D3 - url_has_allowed_host_and_scheme
import re


def split_public_documents(documents):
    templates = []
    public = []
    for doc in documents:
        if doc.get("confidential"):
            continue

        if doc.get("block_from_public_file"):
            continue

        if doc.get("is_tra"):
            templates.append(doc)
            continue

        public.append(doc)

    return templates, public


def deep_index_items_by(items, key):
    """
    Index a list of dicts by a given key.
    Returns a dict of the items based on the value of `key` in each item.
    """
    index = {}
    for item in items or []:
        try:
            _key = dpath.get(item, key)
            index_key = str((_key if _key is not None else "")).lower()
        except KeyError:
            # NOTE: on key missing, this indexes as '', same as a None value.
            index_key = ""
        index.setdefault(index_key, [])
        index[index_key].append(item)
    return index


def to_word(word):
    """
    Convert an underscored key name into a capitalised word
    """
    return word.replace("_", " ").capitalize()


def pluck(dict_, attr_list):
    """
    Return a dict containing the attributes listed, plucked from the given dict.
    """
    out = {}
    for key in attr_list:
        if key in dict_:
            out[key] = dict_[key]
    return out


def get(item, key, default=None):
    """
    Safe get to find a value based on a path
    """
    val = default
    try:
        val = dpath.get(item, key)
    except KeyError:
        pass
    return val


def first(list):
    """
    Return the first thing from a list without crashing if the list is empty or not a list
    """
    if list and len(list) > 0:
        return list[0]
    return list


def proxy_stream_file_download(stream, filename, mime_type=None, chunk_size=None):
    """
    Send a file back as a streamed response
    :param path: Full path to the file
    :param mime_type: The file's mime type
    :param chunk_size: Optional chunk size for sending the file [Default: 8192]
    :return: A StreamingHttpResponse streaming the file
    """
    response = StreamingHttpResponse(stream, content_type=stream.headers.get("Content-Type"))
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def validate(data, validators):
    """
    Run a set of validators against a dict (typically post parameters)
    :data: dictionary to be validated
    :validators: array of validators
    :return: dict of errors - keyed with the fieldnames
    """
    errors = {}
    for validator in validators:
        key = validator["key"]
        value = data.get(key) or ""
        if key not in errors:  # we only want one error per field
            if not re.compile(validator.get("re", ".+")).match(value):
                errors[key] = validator["message"]
    return errors


def parse_redirect_params(redirect_str):
    """
    Parse a redirect string into it's url reverse key and optional kwargs
    """
    if not redirect_str:
        return None, None
    redirect_key = redirect_str
    redirect_kwargs = {}
    redirect_key_parts = redirect_str.split("|")
    if len(redirect_key_parts) == 2:
        redirect_key, redirect_kwargs_spec = redirect_key_parts
        redirect_kwargs = dict([redirect_kwargs_spec.split("=")])
    return redirect_key, redirect_kwargs


def set_cookie(response, key, value, days_expire=365):
    max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )
    response.set_cookie(key, value, max_age=max_age, expires=expires)


def internal_redirect(url, default_path):
    """
    Redirect to the specified URL after checking that
    host is in the allowed hosts list
    :param url: URL to redirect to
    :param default_path: Default path to redirect to if url is unsafe
    """
    if not is_safe_url(url, settings.ALLOWED_HOSTS):
        return redirect(default_path)

    return redirect(url)
