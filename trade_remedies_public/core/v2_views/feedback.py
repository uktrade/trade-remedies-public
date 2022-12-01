from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.base import View
from v2_api_client.mixins import APIClientMixin


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


class CollectFeedbackView(APIClientMixin, TemplateView):
    template_name = "v2/feedback/collect_feedback.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if feedback_id := kwargs.get("feedback_id"):
            context["feedback_object"] = self.client.feedback(feedback_id)
        return context

    def post(self, request, *args, **kwargs):
        feedback_dictionary = {
            "what_didnt_work_so_well": request.POST.getlist("what_didnt_work_so_well"),
            "what_didnt_work_so_well_other": request.POST["what_didnt_work_so_well_other"],
            "how_could_we_improve_service": request.POST["how_could_we_improve_service"],
            "rating": request.POST[
                "rating"
            ],  # keep this here as maybe they want to update the rating
        }

        if existing_feedback_id := request.POST.get("existing_feedback_id"):
            # we are updating an existing feedback object, just add the previously unseen data
            feedback_object = self.client.feedback(existing_feedback_id).update(feedback_dictionary)
        else:
            # this is a new, organic piece of feedback, construct from scratch
            feedback_dictionary.update(
                {
                    "logged_in": request.user.is_authenticated,
                    "url": request.GET.get("previous_url", "N/A"),
                    "url_name": request.GET.get("previous_url_name", "N/A"),
                    "journey": request.GET.get("journey", "N/A"),
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
