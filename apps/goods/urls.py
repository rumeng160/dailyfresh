
from django.conf.urls import  url

from apps.goods.views import IndexView,DetailView,ListView
urlpatterns = [

    url(r'^index$',IndexView.as_view(),name='index'),

    url(r'^goods/(\d+)$',DetailView.as_view(),name='detail'),

    url(r'^list/(\d+)/(\d+)',ListView.as_view(),name='list'),


]
