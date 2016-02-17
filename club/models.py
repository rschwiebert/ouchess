from django.db import models
from model_utils import Choices
from django_pgjson.fields import JsonField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_student_member = models.NullBooleanField(blank=True, null=True)
    	

class Algorithm(models.Model):
    formula = models.CharField(max_length=100)
    params = JsonField(default={}, blank=True)


class Event(models.Model):
    name = models.CharField(max_length=30)
    event_type = models.SmallIntegerField(choices=Choices('Tournament', 'Ladder'))
    rating_algorithm = models.ForeignKey(Algorithm)
    location = models.CharField(max_length=30, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class Game(models.Model):
    white = models.ForeignKey(Player, related_name='white')
    black = models.ForeignKey(Player, related_name='black')
    time_control = models.CharField(max_length=25)
    result = models.SmallIntegerField(choices=Choices('1-0','0-1', '1/2-1/2'))
    event = models.ForeignKey(Event)
    date = models.DateField(null=True, blank=True)
    round = models.SmallIntegerField(null=True, blank=True)
    status = models.SmallIntegerField(choices=Choices('public', 'private'))
    eco = models.CharField(max_length=50, null=True, blank=True)
    pgn = models.CharField(max_length=2500, null=True, blank=True)


class Rating(models.Model):
    player = models.ForeignKey(Player)
    event = models.ForeignKey(Event)
    rating = models.IntegerField(default=1200)

    class Meta:
        unique_together = ('player', 'event')


# Signal to associate a Player profile to each Django's User instance.
@receiver(post_save, sender=User)
def add_player(sender, instance, created, **kwargs):
    if created:
        Player.objects.create(user=User)
