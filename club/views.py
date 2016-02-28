from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.generic import DetailView, ListView
import requests
import datetime
from club.models import Player, Ranking, Ladder, Rating


# Create your views here.
def index(request):
    template = loader.get_template('club/index.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))


class PlayerDetailView(DetailView):
    model = Player

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        ratings_list = Rating.objects.filter(player=self.object)
        context['rating_list'] = ratings_list
        return context


class LadderDetailView(DetailView):
    model = Ladder

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        rankings = self.object.ranking_set.order_by('rank')
        context['ranking_list'] = rankings

        ratings = list((ranking.player, ranking.int_rating) for ranking in rankings)
        ratings = sorted(ratings, key=lambda x: x[1],  reverse=True)
        context['rating_list'] = ratings
        context['timestamp'] = datetime.datetime.now()
        return context


class PlayerListView(ListView):
    model = Player


class LadderListView(ListView):
    model = Ladder

