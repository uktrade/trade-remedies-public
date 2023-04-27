from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.base import View
from v2_api_client.mixins import APIClientMixin

from config.base_views import FormInvalidMixin
from config.utils import get_item_default_if_empty_or_none
from core.v2_forms.feedback import FeedbackForm


class CollectRatingView(APIClientMixin, View):
    def post(self, request, *args, **kwargs):
        if existing_feedback_id := request.POST.get("existing_feedback_id"):
            # We are updating a feedback object that already exists
            feedback_object = self.client.feedback(existing_feedback_id).update(
                {"rating": request.POST["rating"]}
            )
        else:
            # This is fresh, let's create a new one
            feedback_object = self.client.feedback(
                {
                    "logged_in": request.user.is_authenticated,
                    "rating": request.POST["rating"],
                    "url": request.POST["url"],
                    "url_name": request.POST["url_name"],
                    "journey": request.POST.get("journey"),
                }
            )
        return JsonResponse(
            data={
                "second_step_url": reverse(
                    "collect_feedback_second_step", kwargs={"feedback_id": feedback_object.id}
                ),
                "feedback_id": feedback_object.id,
            }
        )


class CollectFeedbackView(APIClientMixin, FormInvalidMixin):
    template_name = "v2/feedback/collect_feedback.html"
    form_class = FeedbackForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if feedback_id := self.kwargs.get("feedback_id"):
            context["feedback_object"] = self.client.feedback(feedback_id)
        return context

    def form_valid(self, form):
        feedback_dictionary = {
            "what_didnt_work_so_well": self.request.POST.getlist("what_didnt_work_so_well"),
            "what_didnt_work_so_well_other": self.request.POST["what_didnt_work_so_well_other"],
            "how_could_we_improve_service": self.request.POST["how_could_we_improve_service"],
            # keep this here as maybe they want to update the rating
            "rating": form.cleaned_data["rating"],
        }

        if existing_feedback_id := self.request.POST.get("existing_feedback_id"):
            # we are updating an existing feedback object, just add the previously unseen data
            feedback_object = self.client.feedback(existing_feedback_id).update(feedback_dictionary)
        else:
            # this is a new, organic piece of feedback, construct from scratch
            feedback_dictionary.update(
                {
                    "logged_in": self.request.user.is_authenticated,
                    "url": get_item_default_if_empty_or_none(
                        self.request.GET, "previous_url", "N/A"
                    ),
                    "url_name": get_item_default_if_empty_or_none(
                        self.request.GET, "previous_url_name", "N/A"
                    ),
                    "journey": get_item_default_if_empty_or_none(
                        self.request.GET, "journey", "N/A"
                    ),
                }
            )
            feedback_object = self.client.feedback(feedback_dictionary)
        return redirect(reverse("feedback_sent", kwargs={"feedback_id": feedback_object.id}))


class FeedbackSentView(APIClientMixin, TemplateView):
    template_name = "v2/feedback/feedback_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback_object = self.client.feedback(kwargs["feedback_id"], fields=["url"])
        context["previous_url"] = feedback_object.url
        return context
