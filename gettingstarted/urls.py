from django.conf.urls import include, url

from django.contrib import admin, auth
from django.contrib.auth.views import login, logout, password_reset
admin.autodiscover()

import club.views

urlpatterns = [

    url(r'^$', club.views.index, name='index'),
    url(r'^login/$', login, {'template_name': 'club/login.html'}, name='login'),
    url(r'^logout/$', logout, {'next_page': '/'}, name='logout'),
    url(r'^password_reset/$', password_reset, name='password_reset'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^players/$', club.views.PlayerListView.as_view(), name='player-list'),
    url(r'^players/(?P<pk>[0-9]+)$', club.views.PlayerDetailView.as_view(), name='player-detail'),
    url(r'^ladders/$', club.views.LadderListView.as_view(), name='ladder-list'),
    url(r'^ladders/(?P<pk>[0-9]+)$', club.views.LadderDetailView.as_view(), name='ladder-detail'),
    url(r'^ladders/(?P<pk>[0-9]+)/games$', club.views.LadderGameListView.as_view(), name='ladder-games'),
    url(r'^tourneys/$', club.views.TourneyListView.as_view(), name='tourney-list'),
    url(r'^tourneys/(?P<pk>[0-9]+)$', club.views.TourneyDetailView.as_view(), name='tourney-detail'),
    url(r'^tourneys/(?P<pk>[0-9]+)/games$', club.views.TourneyGameListView.as_view(), name='tourney-games'),
    url(r'^games/$', club.views.GameListView.as_view(), name='game-list'),
    url(r'^games/(?P<pk>[0-9]+)$', club.views.GameDetailView.as_view(), name='game-detail'),
    
]
