from django.shortcuts import render, loader, redirect
from django.views.generic import View
from apps.goods.models import GoodsSKU, Goods, IndexGoodsBanner, IndexTypeGoodsBanner, GoodsType, IndexPromotionBanner
from apps.order.models import OrderGoods, OrderInfo
from django.conf import settings
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
import os


# Create your views here.

class IndexView(View):

    def get(self, request):

        content = cache.get('cache_index_page')

        if content is None:
            print(123)

            types = GoodsType.objects.all()
            #
            # # if types:
            # #     for type in types:
            # #
            goodsbanners = IndexGoodsBanner.objects.all().order_by('index')

            promotions = IndexPromotionBanner.objects.all().order_by('index')

            for type in types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')

                text_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                type.image_banners = image_banners

                type.text_banners = text_banners
            url = settings.NGINX_URL
            content = {

                'types': types,

                'goodsbanners': goodsbanners,

                'promotions': promotions,

                'url': url}

            cache.set('cache_index_page', content, 3600)
            print('设置缓存')

        user = request.user

        cart_count = 0

        if user.is_authenticated():
            conn = get_redis_connection('default')

            cart_key = 'cart_%s' % user.id

            cart_count = conn.hlen(cart_key)

            cart_count = cart_count

        content.update(cart_count=cart_count)

        return render(request, 'index.html', content)


class DetailView(View):
    def get(self, request, sku_id):
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))
        types = GoodsType.objects.all()

        orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku.id)

        url = settings.NGINX_URL
        user = request.user

        cart_count = 0

        if user.is_authenticated():
            conn = get_redis_connection('default')

            cart_key = 'cart_%s' % user.id

            cart_count = conn.hlen(cart_key)

            cart_count = cart_count

            conn = get_redis_connection('default')

            history_id = 'history_%s' % user.id

            conn.lrem(history_id, 0, sku_id)

            conn.lpush(history_id, sku_id)

            conn.ltrim(history_id, 0, 4)

        content = {

            'sku': sku,
            'types': types,
            'orders': orders,
            'new_skus': new_skus,
            'url': url,
            'cart_count': cart_count,
            'same_spu_skus': same_spu_skus

        }

        return render(request, 'detail.html', content)


class ListView(View):
    def get(self, request, type_id, page):
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        types = GoodsType.objects.all()

        sort = request.GET.get('sort')

        if sort == 'price':

            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'sales':
            skus = GoodsSKU.objects.filter(type=type).order_by('sales')

        else:
            sort = 'default'

            skus = GoodsSKU.objects.filter(type=type).order_by('id')

        paginator = Paginator(skus, 1)

        page = int(page)
        if page > paginator.num_pages:
            page = 1
        page_skus = paginator.page(page)

        num_pages = paginator.num_pages

        if num_pages <= 5:
            pages = range(1, num_pages + 1)

        elif page <= 3:
            pages = range(1, 6)
        elif page - num_pages <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        url = settings.NGINX_URL
        user = request.user

        cart_count = 0

        if user.is_authenticated():
            conn = get_redis_connection('default')

            cart_key = 'cart_%s' % user.id

            cart_count = conn.hlen(cart_key)

            cart_count = cart_count
        content = {
            'type': type, 'types': types,
            'page_skus': page_skus, 'new_skus': new_skus,
            'url': url, 'cart_count': cart_count,
            'sort': sort, 'pages': pages
        }

        return render(request, 'list.html', content)
