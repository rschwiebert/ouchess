from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext
import requests


from .models import Greeting

# Create your views here.
def index(request):
    template = loader.get_template('ouchess/index.html')
    context = RequestContext(request,{})
    return HttpResponse(template.render(context))

def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

