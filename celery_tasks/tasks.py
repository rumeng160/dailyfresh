from celery import Celery
from django.conf import settings
from django.core.mail import send_mail


from django.shortcuts import render,loader
# 在任务处理者一端加这几句
import os
import django_redis
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()
from apps.goods.models import GoodsSKU,Goods,IndexGoodsBanner,IndexTypeGoodsBanner,GoodsType,IndexPromotionBanner
import sys
from django_redis import get_redis_connection

app = Celery('celery_tasks.tasks', broker='redis://192.168.1.105:6379/8')
@app.task
def send_register_active_email(to_email,username,token):
    # subject =
    #
    # message = ''
    #
    # html_message =
    #
    # sender = settings.EMAIL_FROM
    #
    # receive = [to_email]
    '''发送激活邮件'''
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
    username, token, token)
    send_mail(subject,message,sender,receiver,html_message=html_message)

@app.task
def create_static_index_html():
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



        'url': url
    }

    temp = loader.get_template('static_index.html')

    index = temp.render(content)
    # index = 'zz'

    save_path = os.path.join(settings.BASE_DIR,'static\index.html')




    with open(save_path,"w",encoding='utf-8') as f :
        f.write(index)
