"""EPA access is separate from general provider staff access."""

EPA_OFFICER_GROUP = "EPA Officers"


def epa_role(user):
    if user.is_superuser or user.groups.filter(name=EPA_OFFICER_GROUP).exists():
        return "officer"
    return "client"
