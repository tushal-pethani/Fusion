from django.urls import path
from .views import *


urlpatterns = [
    path('placement/', PlacementScheduleView.as_view(), name='placement-list'),
    path('statistics/',BatchStatisticsView.as_view()),
    path('generate-cv/',generate_cv ,name='generate_cv'),
]
