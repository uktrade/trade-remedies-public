"""trade_remedies_public URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import (
    include,
    path,
)
from django.views.generic import TemplateView

from cases.v2_views import active_investigations
from cases.views import CasesView
from cookies import views as cookie_views
from core import views as core_views
from core.v2_views import feedback, manage_users
from login import views as login_views
from password import views as password_views
from registration import views as register_views

# todo - config/urls.py should not contain anything, put these URLs in their relevant apps
urlpatterns = [
    path("", login_views.LandingView.as_view(), name="landing"),
    path("health/", core_views.HealthCheckView.as_view(), name="healthcheck"),
    path("holding_page/", core_views.HoldingView.as_view(), name="holdingpage"),
    # path('start/', core_views.StartView.as_view(), name='start'),
    path("twofactor/", login_views.TwoFactorView.as_view(), name="two_factor"),
    path(
        "request_new_two_factor/",
        login_views.RequestNewTwoFactorView.as_view(),
        name="request_new_two_factor",
    ),
    path("email/verify/", core_views.EmailVerifyView.as_view(), name="email_verify"),
    path("organisation/set/", core_views.SetOrganisationView.as_view()),
    path("organisation/set/<uuid:organisation_id>/", core_views.SetOrganisationView.as_view()),
    path("case/", include("cases.urls")),
    path("cases/", CasesView.as_view(), name="cases"),
    path("accounts/register/", register_views.RegisterView.as_view(), name="register"),
    path(
        "accounts/register/<uuid:code>/<uuid:case_id>/",
        register_views.RegisterView.as_view(),
        name="register_invite",
    ),
    path(
        "accounts/register/2/",
        register_views.RegisterOrganisationCountryView.as_view(),
        name="register2",
    ),
    path(
        "accounts/register/2/<uuid:code>/<uuid:case_id>/",
        register_views.RegisterOrganisationCountryView.as_view(),
        name="register2",
    ),
    path(
        "accounts/register/3/", register_views.RegisterOrganisationView.as_view(), name="register3"
    ),
    path(
        "accounts/register/3/<uuid:code>/<uuid:case_id>/",
        register_views.RegisterOrganisationView.as_view(),
        name="register3",
    ),
    path(
        "accounts/register/4/",
        register_views.RegisterContactAddressView.as_view(),
        name="register4",
    ),
    path(
        "accounts/register/4/<uuid:code>/<uuid:case_id>/",
        register_views.RegisterContactAddressView.as_view(),
        name="register4",
    ),
    path("accounts/register/5/", register_views.RegisterIdsView.as_view(), name="register5"),
    path(
        "accounts/register/5/<uuid:code>/<uuid:case_id>/",
        register_views.RegisterIdsView.as_view(),
        name="register5",
    ),
    path(
        "invitation/<uuid:code>/for/<uuid:org_id>/",
        register_views.RegistrationCompletionView.as_view(),
    ),
    path(
        "invitation/<uuid:code>/<uuid:case_id>/", core_views.InvitationView.as_view(), name="start"
    ),
    path(
        "invitation/<uuid:code>/<uuid:case_id>/confirm_organisation",
        core_views.InvitationConfirmOrganisation.as_view(),
        name="invitation_confirm_organisation",
    ),
    path(
        "termsofuse-privacypolicy/",
        register_views.TermsAndConditionsView.as_view(),
        name="terms_and_conditions_and_privacy",
    ),
    path("cookies/", cookie_views.CookieSettingsView.as_view(), name="cookie_preferences"),
    path("cookiepolicy/", cookie_views.CookiePolicyView.as_view(), name="Cookie policy"),
    path(
        "accessibilitystatement/",
        register_views.AccessibilityStatementView.as_view(),
        name="accessibility_statement",
    ),
    path("accounts/login/", login_views.LoginView.as_view(), name="login"),
    path(
        "accounts/login/<uuid:code>/<uuid:case_id>/",
        login_views.LoginView.as_view(),
        name="login_invite",
    ),
    path(
        "accounts/contact/update/",
        register_views.UpdateUserDetailsView.as_view(),
        name="update_details",
    ),
    path("accounts/logout/", login_views.logout_view, name="logout"),
    path(
        "accounts/forgotpassword/done",
        password_views.ForgotPasswordRequested.as_view(),
        name="forgot_password_requested",
    ),
    path(
        "accounts/forgotpassword/",
        password_views.ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
    path(
        "accounts/password/reset/<uuid:request_id>/<str:token>/",
        password_views.ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "accounts/password/reset/success/",
        password_views.ResetPasswordSuccessView.as_view(),
        name="reset_password_success",
    ),
    path("accounts/info/", core_views.AccountInfo.as_view(), name="account_info"),
    path(
        "accounts/info/user/", core_views.TeamUserView.as_view(self_details=True), name="user_view"
    ),
    path(
        "accounts/info/user/<str:section>/",
        core_views.TeamUserView.as_view(self_details=True),
        name="user_view",
    ),
    path("accounts/info/edit/", core_views.AccountEditInfo.as_view(), name="account_edit"),
    path("accounts/team/", core_views.TeamView.as_view(), name="team_view"),
    path("accounts/team/user/", core_views.TeamUserView.as_view(), name="new_user"),
    path("accounts/team/user/<uuid:user_id>/", core_views.TeamUserView.as_view(), name="user_view"),
    path(
        "accounts/team/<uuid:organisation_id>/user/",
        core_views.TeamUserView.as_view(),
        name="user_view",
    ),
    path(
        "accounts/team/<uuid:organisation_id>/user/<uuid:user_id>/",
        core_views.TeamUserView.as_view(),
        name="user_view",
    ),
    path(
        "accounts/team/<uuid:organisation_id>/user/<uuid:user_id>/<str:section>/",
        core_views.TeamUserView.as_view(),
        name="user_view",
    ),
    path(
        "accounts/team/invite/<uuid:invitation_id>/",
        core_views.UserInviteView.as_view(),
        name="user_invite",
    ),
    path(
        "accounts/team/<uuid:organisation_id>/invite/<uuid:invitation_id>/<str:section>/",
        core_views.TeamUserView.as_view(),
        name="user_view",
    ),
    path(
        "accounts/team/<uuid:organisation_id>/user/<str:section>/",
        core_views.TeamUserView.as_view(),
        name="user_view",
    ),
    # User assignment to cases
    path(
        "accounts/team/assign/<uuid:user_id>/",
        core_views.AssignUserToCaseView.as_view(),
        name="assign_user_to_case",
    ),
    path(
        "accounts/team/assign/<uuid:user_id>/submission/<uuid:submission_id>/",
        core_views.AssignUserToCaseView.as_view(),
        name="assign_user_to_case_sub",
    ),
    path(
        "accounts/team/assign/<uuid:user_id>/case/<uuid:case_id>/",
        core_views.AssignUserToCaseView.as_view(),
        name="assign_user_to_specific_case",
    ),
    path(
        "accounts/team/assign/<uuid:user_id>/case/<uuid:case_id>/remove/",
        core_views.AssignUserToCaseView.as_view(remove=True),
        name="remove_user_from_case",
    ),
    path(
        "accounts/team/assign/<uuid:user_id>/case/<uuid:case_id>/submission/<uuid:submission_id>/",
        core_views.AssignUserToCaseView.as_view(),
        name="assign_user_to_specific_case_sub",
    ),
    path(
        "accounts/team/assign/<uuid:user_id>/case/<uuid:case_id>/contact/",
        core_views.AssignUserToCaseContactView.as_view(),
        name="assign_user_to_case_contact",
    ),
    path(
        "accounts/team/assign/<uuid:user_id>/case/<uuid:case_id>"
        "/submission/<uuid:submission_id>/contact/",
        core_views.AssignUserToCaseContactView.as_view(),
        name="assign_user_to_case_contact_inv",
    ),
    path("dashboard/", core_views.DashboardView.as_view(), name="dashboard"),
    path("stub/", core_views.StubView.as_view(), name="stub"),
    path(
        "companieshouse/search/", core_views.CompaniesHouseSearch.as_view(), name="companieshouse"
    ),
    path(
        "register/confirm_existing_org",
        register_views.V2RegistrationViewConfirmExistingOrganisation.as_view(),
        name="v2_confirm_existing_org",
    ),
    path(
        "register/how_to_get_account",
        TemplateView.as_view(template_name="v2/registration/how_to_get_account.html"),
        name="v2_how_to_get_account",
    ),
    path(
        "register/start", register_views.V2RegistrationViewStart.as_view(), name="v2_register_start"
    ),
    path(
        "register/set_password",
        register_views.V2RegistrationViewSetPassword.as_view(),
        name="v2_register_set_password",
    ),
    path(
        "register/2fa_choice",
        register_views.V2RegistrationView2FAChoice.as_view(),
        name="v2_register_2fa_choice",
    ),
    path(
        "register/your_employer",
        register_views.V2RegistrationViewYourEmployer.as_view(),
        name="v2_register_your_employer",
    ),
    path(
        "register/your_uk_employer",
        register_views.V2RegistrationViewUkEmployer.as_view(),
        name="v2_register_your_uk_employer",
    ),
    path(
        "register/your_non_uk_employer",
        register_views.V2RegistrationViewNonUkEmployer.as_view(),
        name="v2_register_your_non_uk_employer",
    ),
    path(
        "register/organisation_further_details",
        register_views.V2RegistrationViewOrganisationFurtherDetails.as_view(),
        name="v2_register_organisation_further_details",
    ),
    path(
        "register/verify_email/<uuid:user_pk>",
        register_views.RequestEmailVerifyCode.as_view(),
        name="request_email_verify_code",
    ),
    path(
        "register/verify_email/<uuid:user_pk>/<str:email_verify_code>",
        register_views.VerifyEmailVerifyCode.as_view(),
        name="email_verify_code",
    ),
    path("documents/", include("documents.urls")),
]

urlpatterns += [
    path("collect_feedback", feedback.CollectFeedbackView.as_view(), name="collect_feedback"),
    path(
        "collect_feedback_second_step/<uuid:feedback_id>",
        feedback.CollectFeedbackView.as_view(),
        name="collect_feedback_second_step",
    ),
    path("collect_rating", feedback.CollectRatingView.as_view(), name="collect_rating"),
    path(
        "feedback_sent/<uuid:feedback_id>",
        feedback.FeedbackSentView.as_view(),
        name="feedback_sent",
    ),
]

# Manage team urls
urlpatterns += [
    path("manage_users_home", manage_users.ManageUsersView.as_view(), name="manage_users_home"),
    path(
        "view_user/<uuid:organisation_user_id>/", manage_users.ViewUser.as_view(), name="view_user"
    ),
    path(
        "view_user/<uuid:user_id>/<uuid:organisation_id>/",
        manage_users.ViewUser.as_view(),
        name="view_user_organisation_user",
    ),
    path(
        "edit_user/<uuid:organisation_user_id>/", manage_users.EditUser.as_view(), name="edit_user"
    ),
    path(
        "edit_user/<uuid:organisation_user_id>/change_permissions",
        manage_users.ChangeOrganisationUserPermissionsView.as_view(),
        name="change_organisation_user_permissions",
    ),
    path(
        "edit_user/<uuid:organisation_user_id>/change_user_active",
        manage_users.ChangeUserActiveView.as_view(),
        name="change_organisation_user_active",
    ),
    path(
        "edit_user/<uuid:organisation_user_id>/change_case_role/<uuid:user_case_id>/",
        manage_users.ChangeCaseRoleView.as_view(),
        name="change_case_role",
    ),
    path(
        "edit_user/<uuid:organisation_user_id>/remove_from_case/<uuid:user_case_id>/",
        manage_users.RemoveFromCaseView.as_view(),
        name="remove_from_case",
    ),
    path(
        "edit_user/<uuid:organisation_user_id>/assign_to_case/",
        manage_users.AssignToCaseView.as_view(),
        name="assign_to_case",
    ),
]

# public active investigations page
urlpatterns += [
    path(
        "public/case/<str:case_number>/submission/<uuid:submission_id>"
        "/document/<uuid:document_id>/",
        core_views.PublicDownloadView.as_view(),
        name="legacy_public_case_submission_document",
    ),
    path(
        "public/cases/",
        active_investigations.ActiveInvestigationsView.as_view(),
        name="public_cases",
    ),
    path(
        "public/case/<str:case_number>/",
        active_investigations.SingleCaseView.as_view(),
        name="public_case",
    ),
    path(
        "public/case/<str:case_number>/submission/<uuid:submission_id>/",
        active_investigations.SingleSubmissionView.as_view(),
        name="public_submission",
    ),
]
