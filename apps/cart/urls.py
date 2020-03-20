
from django.conf.urls import  url
from apps.cart.views import AddCartView,CartInfoView,UpdateCartView,DeleteCartView
from apps.cart import views
urlpatterns = [
    url(r'^add$',AddCartView.as_view(),name='addcart'),

    url(r'^$',CartInfoView.as_view(),name='cart'),

    url(r'^update$',UpdateCartView.as_view(),name='updatecart'),

    url(r'^delete$',DeleteCartView.as_view(),name='deletecart'),

]
