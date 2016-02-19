from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import club.views

urlpatterns = [
    url(r'^$', club.views.index, name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^players/$', club.views.PlayerListView.as_view(), name='player-list'),
    url(r'^players/(?P<pk>[0-9]+)$', club.views.PlayerDetailView.as_view(), name='player-detail'),
    url(r'^events/$', club.views.EventListView.as_view(), name='event-list'),
    url(r'^events/(?P<pk>[0-9]+)$', club.views.EventDetailView.as_view(), name='event-detail'),
    url(r'^events/(?P<pk>[0-9]+)/ratings$', club.views.EventRatingListView.as_view(), name='event-rating-list'),
]
