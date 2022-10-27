from django.views.generic import TemplateView
from v2_api_client.mixins import APIClientMixin


class CollectFeedbackView(APIClientMixin, TemplateView):
    template_name = "v2/feedback/collect_feedback.html"

    def post(self, request, *args, **kwargs):
        journey = request.GET.get("journey")
        previous_url = request.GET.get("previous_url")
        previous_url_name = request.GET.get("previous_url_name")
        new_feedback_object = self.client.feedback(
            {
                "user": request.user.id if request.user.is_authenticated else "",
                "rating": request.POST["rating"],
                "what_didnt_work_so_well": request.POST.getlist("what_didnt_work_so_well"),
                "what_didnt_work_so_well_other": request.POST["what_didnt_work_so_well_other"],
                "how_could_we_improve_service": request.POST["how_could_we_improve_service"],
                "url": previous_url,
                "url_name": previous_url_name,
                "journey": journey,
            }
        )
        print("asd")
