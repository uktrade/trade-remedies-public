from collections import defaultdict
from typing import Union

import dpath
from django.conf import settings
from django.http import HttpRequest
from v2_api_client.client import TRSAPIClient


def add_form_error_to_session(
    error_summary: str, request: HttpRequest, field: str = None, error_text: str = None
) -> bool:
    """
    Utility function to add a form (validation) error to the request.session
    Parameters
    ----------
    field : the 'name' attribute of the input that caused the error
    error_text : The error text
    error_summary : The error summary to be displayed at the top of the page
    request : the request object containing the session

    Returns
    -------
    bool - True if the error message has been added to the session
    """

    if "form_errors" not in request.session:
        request.session["form_errors"] = defaultdict(list)

    if field:
        request.session["form_errors"][field] = error_text

    try:
        if [field, error_summary] not in request.session["form_errors"]["error_summaries"]:
            # We don't want to add the exact same error summary in twice
            request.session["form_errors"]["error_summaries"].append([field, error_summary])
    except TypeError:
        # if "error_summaries" is not in the form_errors dict, this will raise a TypeError, pass
        request.session["form_errors"]["error_summaries"].append([field, error_summary])
    request.session.modified = True

    return True


def get_loa_document_bundle() -> Union[dict, None]:
    """Helper function to retrieve the LOA document application bundle from the API.

    Returns the LOA document bundle in a dict if it exists, else None"""
    client = TRSAPIClient(token=settings.HEALTH_CHECK_TOKEN)
    trs_document_bundles = client.document_bundles()

    # We've got all the TRS document bundles, let's find the LOA
    loa_document_bundle = next(
        filter(
            lambda document_bundle: document_bundle["submission_type"] == "Letter of Authority"
            and document_bundle["status"] == "LIVE",
            trs_document_bundles,
        ),
        None,
    )
    return loa_document_bundle


def get_uploaded_loa_document(submission: dict) -> Union[dict, None]:
    """Helper function to retrieve the LOA document uploaded by a user given a submission.

    Returns the LOA document in a dict if it exists, else None."""
    if submission_documents := submission.get("submission_documents"):
        # Getting the uploaded LOA document if it exists
        loa_document = next(
            filter(
                lambda document: document["type"]["key"] == "loa",
                submission_documents,
            ),
            None,
        )
        if loa_document:
            return loa_document
    return None


def remove_duplicates_from_list_by_key(
    list_object: list, key: str, raise_exception: bool = False
) -> list:
    """
    Removes duplicates from a list of dictionaries by a key.

    e.g. Removes all duplicate user_case objects by their case_id.
    Parameters
    ----------
    list_object : the list to remove duplicates from
    key : the key in a dpath glob format. e.g x["a"]["s"] == "/a/s/"
    raise_exception : if you want to raise an exception if the key cannot be found in the element

    Returns
    -------
    list_object with all the duplicates removed according to key
    """
    seen_elements = []
    no_duplicates = []

    for element in list_object:
        try:
            value = dpath.util.get(element, key)
            if value not in seen_elements:
                seen_elements.append(value)
                no_duplicates.append(element)
        except KeyError:
            if raise_exception:
                raise
            pass
    return no_duplicates


def get_item_default_if_empty_or_none(dictionary: dict, item: str, default: str):
    """
    Returns the default if the value in the dict is empty, None, or the key doesn't exist
    Parameters
    ----------
    dictionary: the dictionary to search
    item : the key to check
    default : the default to return if the item is empty or None or doesn't exist
    """
    value = dictionary.get(item, default)
    if not value:
        return default
    return value
