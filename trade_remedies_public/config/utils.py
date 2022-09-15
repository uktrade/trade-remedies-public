from collections import defaultdict
from typing import Union

from django.http import HttpRequest
from django.conf import settings
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

    if [field, error_summary] not in request.session["form_errors"]["error_summaries"]:
        # We don't want to add the exact same error summary in twice
        request.session["form_errors"]["error_summaries"].append([field, error_summary])
    request.session.modified = True

    return True


def get_loa_document_bundle() -> Union[dict, None]:
    """Helper function to retrieve the LOA document application bundle from the API.

    Returns the LOA document bundle in a dict if it exists, else None"""
    client = TRSAPIClient(token=settings.HEALTH_CHECK_TOKEN)
    trs_document_bundles = client.document_bundles.all()

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
            return loa_document["document"]
    return None
