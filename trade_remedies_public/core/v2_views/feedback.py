from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from v2_api_client.mixins import APIClientMixin


class CollectFeedbackView(APIClientMixin, TemplateView):
    template_name = "v2/feedback/collect_feedback.html"

    def post(self, request, *args, **kwargs):
        new_feedback_object = self.client.feedback(
            {
                "logged_in": request.user.is_authenticated,
                "rating": request.POST["rating"],
                "what_didnt_work_so_well": request.POST.getlist("what_didnt_work_so_well"),
                "what_didnt_work_so_well_other": request.POST["what_didnt_work_so_well_other"],
                "how_could_we_improve_service": request.POST["how_could_we_improve_service"],
                "url": request.POST.get("url"),
                "url_name": request.POST.get("previous_url_name"),
                "journey": request.POST.get("journey"),
            }
        )
        return redirect(reverse("feedback_sent", kwargs={"feedback_id": new_feedback_object.id}))


class FeedbackSentView(APIClientMixin, TemplateView):
    template_name = "v2/feedback/feedback_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback_object = self.client.feedback(kwargs["feedback_id"], fields=["url"])
        context["previous_url"] = feedback_object.url
        return context
