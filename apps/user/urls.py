
from django.conf.urls import  url

# from user import views
from django.contrib.auth.decorators import login_required
from apps.user.views import RegisterView,ActiveView,LoginView,UserAddrView,UserOrderView,UserInfoView,LogoutView
urlpatterns = [
    url(r'^register$',RegisterView.as_view(),name='register'),

    # url(r'^register_handle$',views.register_handle,name='register_handle'),

    # url(r'^active/(?P<id>\.*)$')
    url(r'^active/(.*)$',ActiveView.as_view()),

    url(r'^login$',LoginView.as_view(),name='login'),

    url(r'^logout$',LogoutView.as_view(),name='logout'),

    # url(r'^$',login_required(UserInfoView.as_view()),name ='user'),
    #
    # url(r'^order$',login_required(UserOrderView.as_view()),name='order'),
    #
    # url(r'^address$',login_required(UserAddrView.as_view()),name='address'),
    url(r'^$',UserInfoView.as_view(),name ='user'),

    url(r'^order/(\d+)$',UserOrderView.as_view(),name='order'),

    url(r'^address$',UserAddrView.as_view(),name='address'),
]
