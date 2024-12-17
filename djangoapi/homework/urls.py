from django.urls import path
from .QuanLyBaiTap import ManageBaiTap, GradeBaiTap, SubmitBaiTap

urlpatterns = [
    path('ManageBaiTap', ManageBaiTap.as_view()),
    path('GradeBaiTap', GradeBaiTap.as_view()),
    path('SubmitBaiTap', SubmitBaiTap.as_view()),
]