from django.contrib import admin
from club.models import Player, Game, Algorithm, Event, Rating

class PlayerAdmin(admin.ModelAdmin):
    pass


class GameAdmin(admin.ModelAdmin):
    pass


class AlgorithmAdmin(admin.ModelAdmin):
    pass


class EventAdmin(admin.ModelAdmin):
    pass


class RatingAdmin(admin.ModelAdmin):
    pass


admin.site.register(Player, PlayerAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Algorithm, AlgorithmAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Rating, RatingAdmin)
