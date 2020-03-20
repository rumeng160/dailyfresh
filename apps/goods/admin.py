from django.contrib import admin
from django.core.cache import cache

from apps.goods.models import GoodsSKU, Goods, IndexGoodsBanner, IndexTypeGoodsBanner, GoodsType, IndexPromotionBanner


# Register your models here.

class BaseModel(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from celery_tasks.tasks import create_static_index_html
        create_static_index_html.delay()
        cache.delete('cache_index_page')

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        from celery_tasks.tasks import create_static_index_html
        create_static_index_html.delay()
        cache.delete('cache_index_page')


class GoodsAdmin(BaseModel):
    pass


class GoodsTypeAdmin(BaseModel):
    pass


class GoodsSkuAdmin(BaseModel):
    pass


class IndexGoodsBannerAdmin(BaseModel):
    pass


class IndexPromotionBannerAdmin(BaseModel):
    pass


admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(GoodsSKU, GoodsSkuAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
