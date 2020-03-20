from django.shortcuts import render,redirect
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.core.urlresolvers import reverse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
from django.conf import settings
from django.http import JsonResponse
from apps.order.models import OrderInfo,OrderGoods
from datetime import *
from django.db import transaction
from alipay import AliPay
import os
# Create your views here.

class OrderPlaceView(LoginRequiredMixin,View):
    def post(self,request):
        user = request.user


        sku_ids = request.POST.getlist('sku_ids')
        if not sku_ids:
            return redirect(reverse('cart:cart'))
        total_price =0
        total_count = 0
        skus = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id = sku_id)
            conn = get_redis_connection('default')
            cart_id = 'cart_%s'%user.id
            count = conn.hget(cart_id,sku_id)
            count = int(count)
            amount = count*sku.price

            sku.amount = amount
            sku.count = count
            skus.append(sku)
            total_count += count
            total_price += amount
        transprit_price = 10

        pay = transprit_price + total_price

        addr = Address.objects.filter(user=user)

        url = settings.NGINX_URL
        sku_ids = ','.join(sku_ids)

        content = {
            'skus':skus,
            'total_price':total_price,
            'total_count':total_count,
            'transprit_price':transprit_price,
            'pay':pay,
            'addr':addr,
            'url':url,
            'sku_ids':sku_ids
        }
        return render(request,'place_order.html',content)

class OrderCommitView(View):
    @transaction.atomic
    def post(self,request):
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'请先登录'})
        addr_id = request.POST.get('addr')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        if not all([addr_id,pay_method,sku_ids]):
            return JsonResponse({'res':1,'errmsg':'信息不完整'})

        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'地址信息不正确'})

        if pay_method not in OrderInfo.PAY_METHOD.keys():
            return JsonResponse({'res':3,'errmsg':'支付方式不存在'})
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
        total_price = 0
        total_count = 0
        transit_price = 10
        save_id = transaction.savepoint()
        try:
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price

                                             )



            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    print(sku.stock)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':4,'errmsg':'商品不存在'})
                conn = get_redis_connection('default')
                cart_id = 'cart_%s'%user.id
                count = conn.hget(cart_id,sku.id)
                origin_stock = sku.stock
                if int(count) > origin_stock :
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':6,'errmsg':'库存不够'})
                amount = sku.price*int(count)
                total_price += amount
                total_count += int(count)
                conn.hdel(cart_id,sku.id)
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()
                OrderGoods.objects.create(order=order,
                                        sku=sku,
                                        count=count,
                                        price=sku.price

                                        )

            order.total_count = total_count
            order.total_price = total_price
            order.save()
            transaction.savepoint_commit(save_id)
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res':7,'errmsg':'订单失败'})

        conn = get_redis_connection('default')
        cart_id = 'cart_%s' % user.id
        conn.hdel(cart_id,*sku_ids)
        return JsonResponse({'res':5,'message':'更新成功'})

# class OrderCommitView(View):
#     @transaction.atomic
#     def post(self,request):
#         user = request.user
#         if not user.is_authenticated():
#             return JsonResponse({'res':0,'errmsg':'请先登录'})
#         addr_id = request.POST.get('addr')
#         pay_method = request.POST.get('pay_method')
#         sku_ids = request.POST.get('sku_ids')
#
#         if not all([addr_id,pay_method,sku_ids]):
#             return JsonResponse({'res':1,'errmsg':'信息不完整'})
#
#         try:
#             addr = Address.objects.get(id=addr_id)
#         except Address.DoesNotExist:
#             return JsonResponse({'res':2,'errmsg':'地址信息不正确'})
#
#         if pay_method not in OrderInfo.PAY_METHOD.keys():
#             return JsonResponse({'res':3,'errmsg':'支付方式不存在'})
#         order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
#         total_price = 0
#         total_count = 0
#         transit_price = 10
#         save_id = transaction.savepoint()
#         try:
#             order = OrderInfo.objects.create(order_id=order_id,
#                                              user=user,
#                                              addr=addr,
#                                              pay_method=pay_method,
#                                              total_count=total_count,
#                                              total_price=total_price,
#                                              transit_price=transit_price
#
#                                              )
#
#
#
#             sku_ids = sku_ids.split(',')
#             for sku_id in sku_ids:
#                 for i in range(3):
#                     try:
#                         sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
#                         print(sku.stock)
#                     except GoodsSKU.DoesNotExist:
#                         transaction.savepoint_rollback(save_id)
#                         return JsonResponse({'res':4,'errmsg':'商品不存在'})
#                     conn = get_redis_connection('default')
#                     cart_id = 'cart_%s'%user.id
#                     count = conn.hget(cart_id,sku.id)
#                     origin_stock = sku.stock
#                     print(origin_stock)
#                     if int(count) > origin_stock :
#                         transaction.savepoint_rollback(save_id)
#                         return JsonResponse({'res':6,'errmsg':'库存不够'})
#
#
#                     new_stock = origin_stock-int(count)
#                     new_sales = int(count)+sku.sales
#                     import time
#                     time.sleep(10)
#                     # print(user.id+':'+sku.stock)
#                     res = GoodsSKU.objects.filter(id=sku_id,stock=origin_stock).update(stock=new_stock,sales=new_sales)
#                     if res == 0:
#                         if i ==2:
#                             transaction.savepoint_rollback(save_id)
#                             return JsonResponse({'res':8,'errmsg':'下单失败'})
#                         continue
#                 # sku.stock -= int(count)
#                 # sku.sales += int(count)
#
#
#                     OrderGoods.objects.create(order=order,
#                                             sku=sku,
#                                             count=count,
#                                             price=sku.price
#
#                                             )
#                     amount = sku.price * int(count)
#                     total_price += amount
#                     total_count += int(count)
#                     conn.hdel(cart_id, sku.id)
#                     break
#             order.total_count = total_count
#             order.total_price = total_price
#             order.save()
#             transaction.savepoint_commit(save_id)
#         except Exception as e:
#             transaction.savepoint_rollback(save_id)
#             return JsonResponse({'res':7,'errmsg':'订单失败'})
#
#         conn = get_redis_connection('default')
#         cart_id = 'cart_%s' % user.id
#         conn.hdel(cart_id,*sku_ids)
#         return JsonResponse({'res':5,'message':'更新成功'})

class OrderPayView(View):
    def post(self,request):

        user = request.user

        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'请先登录'})
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res':1,'errmsg':'无效的订单'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,user=user,pay_method=3,order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'订单错误'})

        alipay = AliPay(
            appid="2016092200569759",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=os.path.join(settings.BASE_DIR,'apps/order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=os.path.join(settings.BASE_DIR,'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True # 默认False
        )
        total_pay = order.total_price+order.transit_price
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_pay),
            subject='天天生鲜%s'%order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )


        pay_url = 'https://openapi.alipaydev.com/gateway.do?'+order_string
        return JsonResponse({'res':3,'message':'跳转支付','pay_url':pay_url})
class OrderCheckView(View):
    def post(self,request):
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'清先登录'})
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res':1,'errmsg':'订单失效'})
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'订单失效'})

        alipay = AliPay(
            appid="2016092200569759",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        while True:
            response = alipay.api_alipay_trade_query(order_id)

            # response = {
            #         "trade_no": "2017032121001004070200176844", # 支付宝交易号
            #         "code": "10000", # 接口调用是否成功
            #         "invoice_amount": "20.00",
            #         "open_id": "20880072506750308812798160715407",
            #         "fund_bill_list": [
            #             {
            #                 "amount": "20.00",
            #                 "fund_channel": "ALIPAYACCOUNT"
            #             }
            #         ],
            #         "buyer_logon_id": "csq***@sandbox.com",
            #         "send_pay_date": "2017-03-21 13:29:17",
            #         "receipt_amount": "20.00",
            #         "out_trade_no": "out_trade_no15",
            #         "buyer_pay_amount": "20.00",
            #         "buyer_user_id": "2088102169481075",
            #         "msg": "Success",
            #         "point_amount": "0.00",
            #         "trade_status": "TRADE_SUCCESS", # 支付结果
            #         "total_amount": "20.00"
            # }
            code = response['code']
            if code == '10000' and response['trade_status'] == 'TRADE_SUCCESS':
                order.order_status = 4
                order.trade_no =response['trade_no']
                order.save()
                return JsonResponse({'res':3,'message':'支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
               import time
               time.sleep(5)
               continue

            else:
                print(code)
                return JsonResponse({'res':4,'errmsg':'支付错误'})
class CommentView(LoginRequiredMixin, View):
    """订单评论"""
    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count*order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i) # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '') # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5 # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))































