from django.conf.urls import url
from wechat import views

urlpatterns = [
    url(r'^wx$',views.wx),
    # url(r'^',views.index)
]