from collections import defaultdict

from django.http import HttpRequest


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

    request.session["form_errors"][field] = error_text
    request.session["form_errors"]["error_summaries"].append([field, error_summary])
    request.session.modified = True

    return True
