from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from django.conf import settings
from utils.mixin import LoginRequiredMixin
# Create your views here.
class AddCartView(View):
    def post(self,request):
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'请先登录'})
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        if not all([sku_id,count]):
            return JsonResponse({'res':1,'errmsg':'数据不完整'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res':2,'errmsg':'商品数目不正确'})
        try:
            goodsku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':3,'errmsg':'没有这个商品'})
        conn = get_redis_connection('default')
        cart_id = 'cart_%s'%user.id
        cart_count = conn.hget(cart_id,sku_id)
        if cart_count:
            count += int(cart_count)
        if count>goodsku.stock:
            return JsonResponse({'res':4,'errmsg':'库存不够'})
        conn.hset(cart_id,sku_id,count)
        num = conn.hlen(cart_id)
        return JsonResponse({'res':5,'num':num,'message':'添加成功'})


class CartInfoView(LoginRequiredMixin,View):
    def get(self,request):
        user = request.user
        cart_id = 'cart_%s'%user.id
        conn = get_redis_connection('default')
        cart_dict = conn.hgetall(cart_id)
        totalcount = 0
        totalprice = 0
        skus = []
        for sku_id,count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            skus.append(sku)
            amount = sku.price*int(count)
            sku.amount = amount
            sku.count = count
            totalcount += int(count)
            totalprice += amount
        url = settings.NGINX_URL
        content = {

            'skus':skus,
            'totalcount':totalcount,
            'totalprice':totalprice,
            'url':url
        }

        return render(request,'cart.html',content)

class UpdateCartView(View):
    def post(self,request):
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'请先登录'})
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        print(sku_id,count)
        if not all([sku_id,count]):
            return JsonResponse({'res':1,'errmsg':'信息不完整'})
        try:
            sku = GoodsSKU.objects.get(id = sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'没有这个商品'})
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res':3,'errmsg':'商品数量有误'})
        if count > sku.stock:
            return JsonResponse({'res':4,'errmsg':'商品库存不足'})
        conn = get_redis_connection('default')
        cart_id = 'cart_%s'%user.id
        conn.hset(cart_id,sku_id,count)
        count_list = conn.hvals(cart_id)
        total_count = 0
        for num in count_list:
            total_count += int(num)
        return JsonResponse({'res':5,'message':'数据更新成功','total_count':total_count})

class DeleteCartView(View):
    def post(self,request):
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'请先登录'})
        sku_id = request.POST.get('sku_id')
        if not sku_id:
            return JsonResponse({'res':1,'errmsg':'商品不存在'})
        try:
           sku = GoodsSKU.objects.get(id= sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'商品不存在'})
        conn = get_redis_connection('default')
        cart_id = 'cart_%s'%user.id
        conn.hdel(cart_id,sku_id)
        count_list = conn.hvals(cart_id)
        total_count = 0
        for val in count_list:
            total_count += int(val)
        return JsonResponse({'res':3,'message':'更新成功','total_count':total_count})