from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import club.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', club.views.index, name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^player/(?P<pk>[0-9]+)$', club.views.PlayerDetailView.as_view(), name='player-detail'),
]
