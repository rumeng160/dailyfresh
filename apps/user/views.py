from django.shortcuts import render,redirect
from django.http import HttpResponse
from apps.user.models import User,Address
from django.core.urlresolvers import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.core.mail import send_mail
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login,logout
from utils.mixin import LoginRequiredMixin
from apps.goods.models import GoodsSKU
from redis import StrictRedis
from apps.order.models import OrderGoods,OrderInfo
import re
from django.core.paginator import Paginator

import time
# Create your views here.

# def register(request):
#     if request.method == "GET":
#         return render(request,'register.html')
#     else:
#         username = request.POST.get('user_name')
#         email = request.POST.get('email')
#         password = request.POST.get('pwd')
#         allow = request.POST.get('allow')
#         if not all([username, email, password]):
#             return render(request, 'register.html', {'errmeg': '信息不完整'})
#
#         if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {{'errmeg': '邮箱格式错误'}})
#
#         if allow != 'on':
#             return render(request, 'register.html', {'errmeg': '请遵守我们的协议'})
#
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             user = None
#         if user:
#             return render(request, 'register.html', {'errmeg': '用户名已经存在'})
#
#         user = User.objects.create_user(username, email, password)
#         user.is_active = 0
#         user.save()
#         return redirect(reverse('goods:index'))
# def register_handle(request):
#     username = request.POST.get('user_name')
#     email = request.POST.get('email')
#     password = request.POST.get('pwd')
#     allow = request.POST.get('allow')
#     if not all([username,email,password]):
#         return render(request,'register.html',{'errmeg':'信息不完整'})
#
#     if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
#
#         return render(request,'register.html',{{'errmeg':'邮箱格式错误'}})
#
#     if allow != 'on':
#         return render(request,'register.html',{'errmeg':'请遵守我们的协议'})
#
#     try:
#         user = User.objects.get(username=username)
#     except User.DoesNotExist:
#         user = None
#     if user:
#         return render(request,'register.html',{'errmeg':'用户名已经存在'})
#
#     user = User.objects.create_user(username,email,password)
#     user.is_active = 0
#     user.save()
#     return redirect(reverse('goods:index'))

class RegisterView(View):
    def get(self,request):
        if request.method == "GET":
            return render(request, 'register.html')

    def post(self,request):
        username = request.POST.get('user_name')
        email = request.POST.get('email')
        password = request.POST.get('pwd')
        allow = request.POST.get('allow')
        if not all([username, email, password]):
            return render(request, 'register.html', {'errmeg': '信息不完整'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {{'errmeg': '邮箱格式错误'}})

        if allow != 'on':
            return render(request, 'register.html', {'errmeg': '请遵守我们的协议'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmeg': '用户名已经存在'})

        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        serialzer = Serializer(settings.SECRET_KEY,3600)
        info = {'config':user.id}
        token = serialzer.dumps(info)
        token = token.decode()
        # subject = '天天生鲜欢迎信息'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
        # username, token, token)
        #
        # send_mail(subject, message, sender, receiver, html_message=html_message)
        send_register_active_email.delay(email,username,token)


        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self,request,token):
        serializer = Serializer(settings.SECRET_KEY,3600)

        try:
            info = serializer.loads(token)

            user_id = info['config']

            user = User.objects.get(id=user_id)

            user.is_active = 1

            user.save()

            return redirect(reverse('user:login'))

        except SignatureExpired as e:

            return HttpResponse('链接已经过期')

class LoginView(View):
    def get(self,request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')

            check = 'checked'
        else:
            username = ''
            check = ''
            

        return render(request,'login.html',{'username':username,'check':check})


    def post(self,request):

        username = request.POST.get('username')

        password = request.POST.get('pwd')

        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'信息不完整'})

        user = authenticate(username=username,password=password)

        if user is not None :
            if user.is_active :
                login(request,user)
                url = request.GET.get('next',reverse('user:user'))

                response =  redirect(url)

                remember = request.POST.get('remember')

                if remember == 'on':

                    response.set_cookie('username',username)


                else:
                    response.delete_cookie('username')


                return response

            else:
                return render(request,'login.html',{'errmsg':'该用户未激活'})

        else:
            return render(request,'login.html',{'errmsg':'用户名或密码错误'})

class LogoutView(View):

    def get(self,request):
        logout(request)

        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):

        user = request.user

        address = Address.objects.get_default_address(user)

        from django_redis import get_redis_connection

        conn = get_redis_connection('default')

        history_id = 'history_%s'%user.id

        sku_ids = conn.lrange(history_id,0,4)
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        url = settings.NGINX_URL
        content = {
            'page':'user',
            'address':address,

            'goods':goods_li,

            'url':url




        }


        return render(request,'user_center_info.html',content)
class UserOrderView(LoginRequiredMixin,View):
    def get(self,request,page):
        user = request.user
        if not user.is_authenticated():
            return redirect(reverse('user:login'))
        try:
            orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        except OrderInfo.DoesNotExist:
            return

        for order in orders:
            order_skus = OrderGoods.objects.filter(order=order)
            for order_sku in order_skus:
                amount = order_sku.count*order_sku.price
                order_sku.amount = amount
            order.order_skus = order_skus
            total_price = order.total_price+order.transit_price
            order.price = total_price
            order.status = OrderInfo.ORDER_STATUS[order.order_status]

        paginator = Paginator(orders,1)
        page = int(page)
        if page>paginator.num_pages:
            page = 1

        page_orders = paginator.page(page)


        # if paginator.num_pages<=5:
        #         #     pages = range(1,paginator.num_pages+1)
        #         # elif page<3:
        #         #     pages = range(1,6)
        #         # elif paginator.num_pages-2>page>=3:
        #         #     pages = range(page-2,page+3)
        #         # elif page>=paginator.num_pages-2:
        #         #     pages = range(paginator.num_pages-4,paginator.num_pages+1)
        num_pages = paginator.num_pages

        if num_pages <= 5:
            pages = range(1, num_pages + 1)

        elif page <= 3:
            pages = range(1, 6)
        elif page - num_pages <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)
        url = settings.NGINX_URL
        content = {
            'url':url,
            'pages':pages,
            'page_orders':page_orders

        }



        return render(request,'user_center_order.html',content)

class UserAddrView(LoginRequiredMixin,View):
    def get(self,request):

        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request,'user_center_site.html',{'page':'address','address':address})


    def post(self,request):

        receiver = request.POST.get('receiver')

        addr = request.POST.get('address')

        zip_code = request.POST.get('zip_code')

        phone = request.POST.get('phone')

        if not all([receiver,addr,phone]):
            user = request.user
            address = Address.objects.get_default_address(user)
            return render(request,'user_center_site.html',{'errmsg':'信息不完整','address':address})

        if not re.match(r'^1[3|5|7|8][0-9]{9}$',phone):
            user = request.user
            address = Address.objects.get_default_address(user)
            return render(request,'user_center_site.html',{'errmsg':'电话格式错误','address':address})

        user = request.user
        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        #
        # except Address.DoesNotExist:
        #     is_default = True
        #
        # is_default = False
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True


        Address.objects.create(user=user,receiver=receiver,phone=phone,addr=addr,zip_code=zip_code,is_default=is_default)

        return redirect(reverse('user:address'))





