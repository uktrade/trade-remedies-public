from django import forms

from config.forms import ValidationForm


class FeedbackForm(ValidationForm):
    rating = forms.MultipleChoiceField(choices=(
        ("1", "Very dissatisfied"),
        ("2", "Dissatisfied"),
        ("3", "Neither satisfied or dissatisfied"),
        ("4", "Satisfied"),
        ("5", "Very satisfied"),
    ), error_messages={
        "required": "feedback_no_rating"
    })
