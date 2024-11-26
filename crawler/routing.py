from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/crawler/(?P<task_id>[^/]+)/$', consumers.TaskProgressConsumer.as_asgi()),
]
