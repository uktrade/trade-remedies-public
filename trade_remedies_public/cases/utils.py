import datetime
from core.utils import deep_index_items_by


def min_nn(a, b):
    """
    Return the minimum of a and b excluding Nones
    """
    if a:
        if b:
            return min(a, b)
        return a
    return b


def decorate_due_status(due_str):
    """
    Decoration for due_dates to render styles and icons
    """
    try:
        if due_str:
            due = datetime.datetime.strptime(due_str[0:19], "%Y-%m-%dT%H:%M:%S")
            date_delta = due - datetime.datetime.now()
        return {
            "due_at": due_str,
            "due_soon": date_delta.days < 14,
            "due_very_soon": date_delta.days < 7,
            "days_remaining": date_delta.days,
        }
    except Exception as exception:
        return {}


def decorate_submission_updated(submission):
    """
    Decoration for submissions
    """

    def later_date(update_date, test_date):
        if update_date is None or (test_date and (test_date > update_date)):
            return test_date
        return update_date

    update_date = None
    for date_key in ["created_at", "sent_at", "received_at", "deficiency_sent_at", "last_modified"]:
        update_date = later_date(update_date, submission.get(date_key))

    # set colour for lozenge depending on status
    status = submission.get("status", {})
    status_type = status.get("type", {})
    status_class = "grey"
    if not status.get("locking"):
        status_class = "red" if status_type.get("direction") == 2 else "amber"

    return {"updated_at": update_date, "status_class": status_class}


def decorate_rois(interests, date_warnings=None):
    """
    A utility for dashboard rendering
    Given a list of registrations of interest,
    we consolidate into cases with a list of organisations beneath.
    The cases and all orgs within are decorated with a count and latest due-date.
    """
    interest_cases = {}
    for interest in interests or []:
        case = interest.get("case") or {}
        case_id = case.get("id")
        organisation = interest.get("organisation") or {}
        organisation_case_role = interest.get("organisation_case_role") or {}
        alert_count = 1 if (interest.get("status") or {}).get("deficiency_notice") else 0
        interest_cases[case_id] = interest_cases.get(case_id) or {
            "case_id": case.get("id"),
            "name": case.get("name"),
            "reference": case.get("reference"),
            "user_organisations": [],
            "due_state": {"submission_count": 0, "due_at": interest.get("due_at")},
            "organisation_case_role": organisation_case_role.get("key"),
        }
        if date_warnings:
            interest_cases[case_id]["due_state"] = decorate_due_status(interest.get("due_at"))

        interest_cases[case_id]["user_organisations"].append(
            {
                "submission_id": interest.get("id"),
                "id": organisation.get("id"),
                "name": organisation.get("name"),
                "org_state": {"submission_count": alert_count, "due_at": interest.get("due_at")},
            }
        )
        # update pending count if deficient
        if alert_count:
            interest_cases[case_id]["due_state"]["submission_count"] += alert_count
            interest_cases[case_id]["due_state"]["due_at"] = min_nn(
                interest_cases[case_id]["due_state"]["due_at"], interest.get("due_at")
            )
    return interest_cases


def structure_documents(documents):
    """
    Take a load of respondant documents and return a conf/non-conf structure
    including parent/child relationships
    """

    type_idx = deep_index_items_by(documents, "type/key")
    conf_idx = deep_index_items_by(type_idx.get("respondent") or [], "confidential")
    doc_idx = deep_index_items_by(documents, "id")
    for document in documents:
        parent_id = document.get("parent_id")
        if parent_id:
            parent = doc_idx.get(parent_id)
            parent = parent and parent[0]  # remove list wrapper
            if parent:
                parent["child"] = document
    return (
        {
            "confidential": conf_idx.get("true", []),
            "non_confidential": conf_idx.get("false", []),
            "loa": type_idx.get("loa") or [],
        },
        doc_idx,
    )


def validate_hs_code(code):
    """
    validate HS Code is the right length
    """
    if code and (len(code) not in (6, 8, 10) or not str(code).isdigit()):
        return False
    return True


def get_org_parties(_client, user):
    """
    Return a list of organisations that the user's organisation (law firm) has access to
    """
    user_org_id = user.organisation.get("id")
    org_parties = {}
    user_org_cases = _client.get_user_cases(outer=True)
    for case in user_org_cases:
        representing = case.get("representing")
        if representing:
            representing_id = representing.get("id")
            if representing_id != user_org_id:
                org_parties[representing.get("id")] = representing
    all_interests = _client.get_registration_of_interest(all_interests=False)
    for roi in all_interests:
        org = roi.get("organisation")
        if org:
            org_parties[org.get("id")] = org
    return sorted(org_parties.values(), key=lambda p: p.get("name"))
