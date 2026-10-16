from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MinimumDigitCountValidator:
    def __init__(self, min_digits=4):
        self.min_digits = min_digits

    def validate(self, password, user=None):
        digit_count = sum(character in "0123456789" for character in password)
        if digit_count < self.min_digits:
            raise ValidationError(
                _("This password must contain at least %(min_digits)d digits."),
                code="password_too_few_digits",
                params={"min_digits": self.min_digits},
            )

    def get_help_text(self):
        return _("Your password must contain at least %(min_digits)d digits.") % {
            "min_digits": self.min_digits
        }
