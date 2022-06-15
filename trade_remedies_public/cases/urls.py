from django.urls import path
from cases import views as case_views


urlpatterns = [
    path("", case_views.TaskListView.as_view(), name="tasklist"),
    # interest in a case
    path(
        "interest/",
        case_views.TaskListView.as_view(submission_type_key="interest"),
        name="interest",
    ),
    path(
        "interest/draft/continue/",
        case_views.InterestDraftContinueView.as_view(),
        name="interest_draft_continue",
    ),
    path(
        "interest/draft/delete/",
        case_views.InterestDraftDeleteView.as_view(),
        name="interest_draft_delete",
    ),
    path(
        "interest/<uuid:case_id>/",
        case_views.TaskListView.as_view(submission_type_key="interest"),
        name="interest_case",
    ),
    path(
        "interest/<uuid:case_id>/company/",
        case_views.CompanyView.as_view(submission_type_key="interest"),
        name="interest_org",
    ),
    path(
        "interest/<uuid:case_id>/submission/<uuid:submission_id>/company/",
        case_views.CompanyView.as_view(submission_type_key="interest"),
        name="interest_org_sub",
    ),
    # Invite 3rd party
    path("invite/", case_views.CaseInviteView.as_view(), name="invite_top"),
    path("invite/<uuid:case_id>/", case_views.CaseInviteView.as_view(), name="invite_case"),
    path(
        "invite/<uuid:case_id>/submission/<uuid:submission_id>/",
        case_views.CaseInviteView.as_view(),
        name="invite_submission",
    ),
    path(
        "invite/<uuid:case_id>/people/",
        case_views.CaseInvitePeopleView.as_view(),
        name="invite_people",
    ),
    path(
        "invite/<uuid:case_id>/<uuid:submission_id>/people/",
        case_views.CaseInvitePeopleView.as_view(),
        name="invite_people_sub",
    ),
    path(
        "invite/<uuid:case_id>/<uuid:submission_id>/people/remove/<uuid:invite_id>/",
        case_views.CaseInvitePeopleView.as_view(),
        name="remove_people",
    ),
    # Reviews
    path("review/", case_views.CaseReviewView.as_view(), name="case_review"),
    # Case Selector
    path("select/", case_views.SelectCaseView.as_view(), name="select_case"),
    path(
        "select/organisation/",
        case_views.SelectOrganisationCaseView.as_view(),
        name="select_organisation_cases",
    ),
    path(
        "select/organisation/for/<uuid:for_user_id>/",
        case_views.SelectOrganisationCaseView.as_view(),
        name="select_organisation_cases_for_user",
    ),
    # case organisation select
    path(
        "<uuid:case_id>/organisation/select/",
        case_views.CaseOrganisationSelectView.as_view(),
        name="select_case_org",
    ),
    # Name
    path(
        "<uuid:case_id>/submission/<int:submission_type_id>/meta/",
        case_views.SubmissionMetaView.as_view(),
        name="meta_submission_by_type",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/meta/",
        case_views.SubmissionMetaView.as_view(),
        name="meta_submission",
    ),
    path("<uuid:case_id>/", case_views.CaseView.as_view(), name="case"),
    path(
        "<uuid:case_id>/organisation/<uuid:organisation_id>/",
        case_views.CaseView.as_view(),
        name="case_org",
    ),
    path(
        "<uuid:case_id>/organisation/<uuid:organisation_id>/submission/<uuid:submission_id>/",
        case_views.TaskListView.as_view(),
        name="tasklist",
    ),
    path(
        "<uuid:case_id>/organisation/<uuid:organisation_id>/submission/create/",
        case_views.CreateSubmissionView.as_view(),
        name="create_submission",
    ),
    path(
        "<uuid:case_id>/organisation/<uuid:organisation_id>/submission/create/<int:submission_type_id>/",  # noqa: E501
        case_views.CreateSubmissionView.as_view(),
        name="create_submission_by_type",
    ),
    path(
        "<uuid:case_id>/organisation/<uuid:organisation_id>/submission/create/file/",
        case_views.CreateSubmissionView.as_view(),
        name="create_submission_file",
    ),
    path(
        "<uuid:case_id>/organisation/<uuid:organisation_id>/set/primary/",
        case_views.SetPrimaryContactView.as_view(),
        name="set_primary_contact",
    ),
    path(
        "<uuid:case_id>/submissions/", case_views.CaseSubmissionsView.as_view(), name="submissions"
    ),
    path(
        "company/",
        case_views.CompanyView.as_view(submission_type_key="application"),
        name="company",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/company/",
        case_views.CompanyView.as_view(submission_type_key="application"),
        name="sub_company",
    ),
    # Product
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/product/",
        case_views.ProductView.as_view(),
        name="product_new",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/product/<uuid:product_id>/",
        case_views.ProductView.as_view(),
        name="product",
    ),
    # Export source
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/source/",
        case_views.SourceView.as_view(),
        name="source_new",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/source/<uuid:export_source_id>/",
        case_views.SourceView.as_view(),
        name="source",
    ),
    path(
        "<uuid:case_id>/availablereviewtypes/",
        case_views.AvailableReviewTypesView.as_view(),
        name="available_reviews",
    ),
    # Submit for review
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/review/",
        case_views.ReviewView.as_view(),
        name="review",
    ),
    # Documents
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/upload/",
        case_views.UploadDocumentsView.as_view(),
        name="sub_upload",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/upload/<str:public_str>/",
        case_views.UploadDocumentsView.as_view(),
        name="upload_type",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/remove/document/<uuid:document_id>/",
        case_views.RemoveDocumentView.as_view(),
        name="removedoc",
    ),
    # Document download
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/download/",
        case_views.ApplicationFormsView.as_view(),
        name="download",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/download/<str:document_type>/",
        case_views.ApplicationFormsView.as_view(),
        name="download_type",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/document/<uuid:document_id>/download/",
        case_views.DocumentDownloadStreamView.as_view(),
        name="download_stream",
    ),
    # Review
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/review_documents/",
        case_views.ReviewDocumentsView.as_view(),
        name="document_review",
    ),
    # Submit
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/submit/",
        case_views.SubmitApplicationView.as_view(),
        name="submit",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/remove/",
        case_views.RemoveSubmissionView.as_view(),
        name="remove",
    ),
    # Tasklist and view
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/",
        case_views.TaskListView.as_view(),
        name="sub_tasklist",
    ),
    path(
        "<uuid:case_id>/submission/<uuid:submission_id>/<str:public_str>/",
        case_views.TaskListView.as_view(),
        name="sub_tasklist_type",
    ),
    # Admin summary
    path(
        "<uuid:case_id>/organisation/<uuid:organisation_id>/summary/",
        case_views.CaseSummaryView.as_view(),
        name="case_summary",
    ),
]
