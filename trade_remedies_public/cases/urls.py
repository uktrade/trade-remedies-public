from django.urls import path
from django.views.generic import TemplateView

from cases import views as case_views
from cases.v2_views import (
    accept_own_org_invitation,
    accept_representative_invitation,
    invite,
    registration_of_interest,
)

urlpatterns = [
    path("", case_views.TaskListView.as_view(), name="tasklist"),
    # interest in a case
    path(
        "interest/",
        case_views.TaskListView.as_view(submission_type_key="interest"),
        name="interest",
    ),
    path(
        "interest/<uuid:case_id>/",
        case_views.TaskListView.as_view(submission_type_key="interest"),
        name="interest_case",
    ),
    path(
        "interest/<uuid:case_id>/<uuid:submission_id>/",
        case_views.TaskListView.as_view(submission_type_key="interest"),
        name="interest_case_submission_created",
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
        "<uuid:case_id>/organisation/<uuid:organisation_id>/"
        "submission/create/<int:submission_type_id>/",
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
]

urlpatterns += [
    path(
        "interest/start",
        registration_of_interest.RegistrationOfInterestTaskList.as_view(),
        name="roi",
    ),
    path(
        "interest/submission/<uuid:submission_id>/",
        registration_of_interest.RegistrationOfInterestTaskList.as_view(),
        name="roi_submission_exists",
    ),
    path(
        "v2/select/",
        registration_of_interest.RegistrationOfInterest1.as_view(),
        name="roi_1",
    ),
    path(
        "interest/<uuid:submission_id>/type/",
        registration_of_interest.InterestClientTypeStep2.as_view(),
        name="interest_client_type",
    ),
    path(
        "interest/<uuid:submission_id>/contact/",
        registration_of_interest.InterestPrimaryContactStep2.as_view(),
        name="interest_primary_contact",
    ),
    path(
        "interest/<uuid:submission_id>/<uuid:contact_id>/ch/",
        registration_of_interest.InterestUkRegisteredYesNoStep2.as_view(),
        name="interest_ch",
    ),
    path(
        "interest/<uuid:submission_id>/<uuid:contact_id>/ch/yes/",
        registration_of_interest.InterestIsUkRegisteredStep2.as_view(),
        name="interest_ch_yes",
    ),
    path(
        "interest/<uuid:submission_id>/<uuid:contact_id>/ch/no/",
        registration_of_interest.InterestNonUkRegisteredStep2.as_view(),
        name="interest_ch_no",
    ),
    path(
        "interest/<uuid:submission_id>/<uuid:contact_id>/submit/",
        registration_of_interest.InterestUkSubmitStep2.as_view(),
        name="interest_submit",
    ),
    path(
        "registration_of_interest/<uuid:submission_id>/check_and_submit",
        registration_of_interest.RegistrationOfInterest4.as_view(),
        name="roi_4",
    ),
    path(
        "interest/<uuid:submission_id>/organisation/",
        registration_of_interest.InterestExistingClientStep2.as_view(),
        name="interest_existing_client",
    ),
    path(
        "interest/<uuid:submission_id>/<uuid:organisation_id>/contact/",
        registration_of_interest.InterestPrimaryContactStep2.as_view(),
        name="interest_existing_client_primary_contact",
    ),
    path(
        "interest/<uuid:submission_id>/upload_registration_documentation/",
        registration_of_interest.RegistrationOfInterestRegistrationDocumentation.as_view(),
        name="roi_3_registration_documentation",
    ),
    path(
        "interest/<uuid:submission_id>/upload_loa/",
        registration_of_interest.RegistrationOfInterestLOA.as_view(),
        name="roi_3_loa",
    ),
    path(
        "interest/<uuid:submission_id>/complete/",
        registration_of_interest.RegistrationOfInterestComplete.as_view(),
        name="roi_complete",
    ),
    path(
        "interest/<uuid:submission_id>/already_exists/",
        registration_of_interest.RegistrationOfInterestAlreadyExists.as_view(),
        name="roi_already_exists",
    ),
    path(
        "interest/<uuid:submission_id>/delete/",
        registration_of_interest.DeleteRegistrationOfInterest.as_view(),
        name="roi_delete_roi",
    ),
]

# invites in general
urlpatterns += [
    path(
        "invite/start",
        invite.WhoAreYouInviting.as_view(),
        name="invitation_start",
    ),
    path(
        "invite/<uuid:invitation_id>/cancel/",
        invite.CancelDraftInvitation.as_view(),
        name="cancel_draft_invitation",
    ),
    path(
        "invite/<uuid:invitation_id>/delete/",
        invite.DeleteDraftInvitation.as_view(),
        name="delete_draft_invitation",
    ),
    path(
        "invite/cancelled/",
        TemplateView.as_view(template_name="v2/invite/invite_cancelled.html"),
        name="invite_cancelled",
    ),
    path(
        "invite/deleted/",
        TemplateView.as_view(template_name="v2/invite/invite_deleted.html"),
        name="invite_deleted",
    ),
    path(
        "invite/<uuid:invitation_id>/review_sent/",
        invite.ReviewInvitation.as_view(),
        name="review_sent_invitation",
    ),
]

# own-org invites
urlpatterns += [
    path(
        "invite/<uuid:invitation_id>/start",
        invite.WhoAreYouInviting.as_view(),
        name="invitation_start_existing",
    ),
    path(
        "invite/<uuid:invitation_id>/enter_name_email/",
        invite.TeamMemberNameView.as_view(),
        name="invitation_name_email",
    ),
    path(
        "invite/<uuid:invitation_id>/select_permissions/",
        invite.PermissionSelectView.as_view(),
        name="invitation_select_permissions",
    ),
    path(
        "invite/<uuid:invitation_id>/choose_cases/",
        invite.ChooseCasesView.as_view(),
        name="invitation_choose_cases",
    ),
    path(
        "invite/<uuid:invitation_id>/review_before_send/",
        invite.ReviewInvitationBeforeSend.as_view(),
        name="invitation_review_before_send",
    ),
    path(
        "invite/<uuid:invitation_id>/sent/",
        invite.InvitationSent.as_view(),
        name="invitation_sent",
    ),
]

# rep invites
urlpatterns += [
    path(
        "invite/representative/start/",
        invite.InviteRepresentativeTaskList.as_view(),
        name="invite_representative_task_list",
    ),
    path(
        "invite/representative/<uuid:invitation_id>/task_list/",
        invite.InviteRepresentativeTaskList.as_view(),
        name="invite_representative_task_list_exists",
    ),
    path(
        "invite/representative/select_case/",
        invite.InviteRepresentativeSelectCase.as_view(),
        name="invite_representative_select_case",
    ),
    path(
        "invite/representative/<uuid:invitation_id>/organisation_details/",
        invite.InviteRepresentativeOrganisationDetails.as_view(),
        name="invite_representative_organisation_details",
    ),
    path(
        "invite/representative/<uuid:invitation_id>/details/",
        invite.InviteNewRepresentativeDetails.as_view(),
        name="invite_new_representative_details",
    ),
    path(
        "invite/representative/<uuid:invitation_id>/<uuid:organisation_id>/details/",
        invite.InviteExistingRepresentativeDetails.as_view(),
        name="invite_existing_representative_details",
    ),
    path(
        "invite/representative/<uuid:invitation_id>/loa/",
        invite.InviteRepresentativeLoa.as_view(),
        name="invite_representative_loa",
    ),
    path(
        "invite/representative/<uuid:invitation_id>/check_and_submit/",
        invite.InviteRepresentativeCheckAndSubmit.as_view(),
        name="invite_representative_check_and_submit",
    ),
    path(
        "invite/representative/<uuid:invitation_id>/sent/",
        invite.InviteRepresentativeSent.as_view(),
        name="invite_representative_sent",
    ),
]

# accepting own-org invitations
urlpatterns += [
    path(
        "accept_invite/<uuid:invitation_id>/start/",
        accept_own_org_invitation.AcceptOrganisationInvite.as_view(),
        name="accept_invite_start",
    ),
    path(
        "accept_invite/<uuid:invitation_id>/set_password/",
        accept_own_org_invitation.AcceptOrganisationSetPassword.as_view(),
        name="accept_invite_set_password",
    ),
    path(
        "accept_invite/<uuid:invitation_id>/two_factor_choice/",
        accept_own_org_invitation.AcceptOrganisationTwoFactorChoice.as_view(),
        name="accept_invite_two_factor_choice",
    ),
]

# accepting representative invitations
urlpatterns += [
    path(
        "accept_representative_invite/<uuid:invitation_id>/start/",
        accept_representative_invitation.RegistrationNameAndEmailView.as_view(),
        name="accept_representative_invitation_name_and_email",
    ),
    path(
        "accept_representative_invite/set_password/<uuid:invitation_id>/",
        accept_representative_invitation.SetPassword.as_view(),
        name="accept_representative_invitation_set_password",
    ),
    path(
        "accept_representative_invite/two_factor_choice/<uuid:invitation_id>/",
        accept_representative_invitation.TwoFactorChoice.as_view(),
        name="accept_representative_invitation_two_factor_choice",
    ),
    path(
        "accept_representative_invite/organisation_details/<uuid:invitation_id>/",
        accept_representative_invitation.OrganisationDetails.as_view(),
        name="accept_representative_invitation_organisation_details",
    ),
    path(
        "accept_representative_invite/organisation_further_details/<uuid:invitation_id>/",
        accept_representative_invitation.OrganisationFurtherDetails.as_view(),
        name="accept_representative_invitation_organisation_further_details",
    ),
]
