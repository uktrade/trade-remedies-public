from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView
from v2_api_client.mixins import APIClientMixin

from config.constants import (
    SECURITY_GROUP_ORGANISATION_OWNER,
    SECURITY_GROUP_ORGANISATION_USER,
)
from core.base import GroupRequiredMixin


class BaseAnonymousPublicTemplateView(APIClientMixin, TemplateView):
    """Template view used to anonymous users who do not need to be logged in."""

    pass


class BasePublicView(LoginRequiredMixin, GroupRequiredMixin, APIClientMixin):
    """A base view used to provide common mixins and attributes to public views.

    Forces the user to be logged in and belong to and own an organisation.
    Also mixes in the V2 API Client which can be called with self.client()
    """

    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]


class FormInvalidMixin(FormView):
    """Adds a mixin to the FormView for assigning form errors to a request if invalid"""

    exclude_fields = []  # A list of fields you want to exclude from the instantiated form_class
    form_class = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["exclude_fields"] = self.exclude_fields
        return kwargs

    def form_invalid(self, form):
        form.assign_errors_to_request(self.request)
        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if self.success_url or self.__class__.get_success_url != FormView.get_success_url:
                # If we have a success_url defined OR have overridden get_success_url(),
                # then don't return form_valid, just run it and prioritise the success_url instead
                self.form_valid(form)
                return redirect(self.get_success_url())
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class BasePublicFormView(BasePublicView, FormInvalidMixin):
    """The same as BasePublicView, but adds the FormView generic mixin and a form_invalid
    function which will assign the form errors to the request session so they can be properly
    rendered in the front-end.
    """


# Ideally this page is never cached, so the status of each step is always up-to-date
@method_decorator(never_cache, name="dispatch")
class TaskListView(BasePublicView, TemplateView):
    """ABC view used to provide children with the basic functionality to act as a task list.

    Deals with instantiation of the task list, moving from step to step, and deciding which steps
    are available for completion.
    """

    def get_task_list(self):
        raise NotImplementedError()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        steps = self.get_task_list()
        for number, step in enumerate(steps):
            for sub_step_index, sub_step in enumerate(step["sub_steps"]):
                if "ready_to_do" not in sub_step:
                    try:
                        previous_step = steps[number - 1]
                        if len(
                            [
                                sub_step
                                for sub_step in previous_step["sub_steps"]
                                if sub_step["status"] == "Complete"
                            ]
                        ) == len(previous_step["sub_steps"]):
                            # All sub-steps in the previous step have been completed,
                            # the next state is now open
                            for sub_step in step["sub_steps"]:
                                sub_step["ready_to_do"] = True
                        else:
                            for sub_step in step["sub_steps"]:
                                sub_step["ready_to_do"] = False
                                sub_step["status"] = "Cannot Start Yet"

                    except IndexError:
                        raise Exception(
                            "The first step in a tasklist should always define a 'ready_to_do' key"
                        )
        context["steps"] = steps
        return context
