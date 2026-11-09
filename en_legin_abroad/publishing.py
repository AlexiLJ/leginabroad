import json
from pathlib import Path

from django.conf import settings
from django.urls import reverse

with Path(__file__).with_suffix(".json").open(encoding="utf-8") as manifest:
    CONTENT = json.load(manifest)


def public_site_settings(request):
    return {
        "site_origin": settings.SITE_ORIGIN,
        "adsense_publisher_id": settings.ADSENSE_PUBLISHER_ID,
        "analytics_measurement_id": settings.GOOGLE_ANALYTICS_MEASUREMENT_ID,
    }


def tool_link(key):
    tool = CONTENT["tools"].get(key)
    if tool is None:
        return None
    return {**tool, "url": reverse(f"en_legin_abroad:{tool['route']}")}
