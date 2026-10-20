from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Everything lives under /api/v1/solar/ so the gateway can send that whole path to this service.
urlpatterns = [
    path("api/v1/solar/admin-site/", admin.site.urls),
    path("api/v1/solar/", include("solar.urls")),
    path("api/v1/solar/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/solar/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
