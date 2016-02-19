from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.generic import DetailView
import requests
from club.models import Player, Rating

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
