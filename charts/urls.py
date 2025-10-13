from django.urls import path

from charts import views

urlpatterns = [
    path("", views.index, name="charts"),
]