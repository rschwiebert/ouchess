from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.generic import DetailView, ListView
import requests
from club.models import Player, Rating, Ladder

# Create your views here.
def index(request):
    template = loader.get_template('club/index.html')
    context = RequestContext(request,{})
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


class PlayerListView(ListView):
    model = Player


class LadderListView(ListView):
    model = Ladder

class LadderRatingListView(ListView):
    model = Rating

    @property
    def ladder(self):
        return Ladder.objects.get(id=self.kwargs['pk']) or None

    def get_context_data(self):
        context = super(ListView, self).get_context_data()
        context['ladder'] = self.ladder
        return context

    def get_queryset(self, **kwargs):
        current_ladder = Ladder.objects.get(id=self.kwargs['pk'])
        queryset = super(ListView, self).get_queryset(**kwargs)
        queryset = queryset.filter(ladder=current_ladder).order_by('-rating')
        return queryset
    
