from __future__ import unicode_literals
from django.db import models
from model_utils import Choices
from django_pgjson.fields import JsonBField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_student_member = models.NullBooleanField(blank=True, null=True)
    	
    def __unicode__(self):
        return self.user.username

class Algorithm(models.Model):
    name = models.CharField(max_length=30, blank=True, null=True)
    formula = models.CharField(max_length=100)
    params = JsonBField(default={}, blank=True)

    def __unicode__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=30)
    event_type = models.SmallIntegerField(choices=Choices((0, 'Tournament'), (1, 'Ladder')))
    rating_algorithm = models.ForeignKey(Algorithm)
    location = models.CharField(max_length=30, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __unicode__(self):
        return self.name + ' (%s) %s-%s' % (self.get_event_type_display(), self.start_date, self.end_date)


class Game(models.Model):
    white = models.ForeignKey(Player, related_name='white')
    black = models.ForeignKey(Player, related_name='black')
    white_rating = models.IntegerField(null=True, blank=True)
    black_rating = models.IntegerField(null=True, blank=True)
    time_control = models.CharField(max_length=25)
    result = models.SmallIntegerField(choices=Choices((0, '1-0'),(1, '0-1'), (2, '1/2-1/2')))
    event = models.ForeignKey(Event)
    datetime = models.DateTimeField(null=True, blank=True)
    round = models.SmallIntegerField(null=True, blank=True)
    status = models.SmallIntegerField(choices=Choices((0, 'public'), (1, 'private')))
    eco = models.CharField(max_length=50, null=True, blank=True)
    pgn = models.CharField(max_length=2500, null=True, blank=True)

    def __unicode__(self):
        return '%s (%d) - %s (%d): %s [%s]' % (self.white.user.username, self.white_rating,
                                               self.black.user.username, self.black_rating,
                                               self.get_result_display(), self.datetime)


class Rating(models.Model):
    player = models.ForeignKey(Player)
    event = models.ForeignKey(Event)
    rating = models.IntegerField(default=1200)

    def __unicode__(self):
        return '%s (%d) [%s]' % (self.player.user.username, self.rating, self.event.name)

    class Meta:
        unique_together = ('player', 'event')

    


# Signal to associate a Player profile to each Django's User instance.
@receiver(post_save, sender=User)
def add_player(sender, instance, created, **kwargs):
    if created:
        Player.objects.create(user=instance)

@receiver(post_save, sender=Game)
def set_ratings(sender, instance, created, **kwargs):
    if created:
        instance.white_rating = instance.event.rating_set.get(player=instance.white).rating
        instance.black_rating = instance.event.rating_set.get(player=instance.black).rating
        instance.save()
