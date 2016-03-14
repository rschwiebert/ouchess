from decimal import Decimal
from django.db.models import Q


def bogus2(white, black, result, ladder):
    white = white.rating(ladder)
    black = black.rating(ladder)
    if result == 0:
        white += 2
        black -= 2
    elif result == 1:
        white -= 2
        black += 2
    elif result == 2:
        if white > black:
            white -= 1
            black += 1
        elif white < black:
            white += 1
            black -= 1
    return white, black


def fide(white, black, result, ladder, provisional_k=32, standard_k=24,
         provisional_limit=30):
    diff = abs(white.rating(ladder)-black.rating(ladder))
    pre_d = [4, 11, 18, 26, 33, 40, 47, 54, 62, 69, 77, 84, 92, 99, 107, 
             114, 122, 130, 138, 146, 154, 163, 171, 180, 189, 198, 207,
             216, 226, 236, 246, 257, 268, 279, 291, 303, 316, 329, 345,
             358, 375, 392, 412, 433, 457, 485, 518, 560, 620, 736, 10000]
    d = [(0, 3)]
    for i in range(1, len(pre_d)):
        d.append((pre_d[i-1], pre_d[i] - 1))

    p = [Decimal('0.%d' % i) for i in range(50, 100)]
    p.append(Decimal('1.0'))
    pd = dict(zip(d, p))
    
    w_games = ladder.game_set.filter(Q(white=white) | Q(black=white)).count()
    b_games = ladder.game_set.filter(Q(white=black) | Q(black=black)).count()
    w_k = standard_k if w_games > provisional_limit else provisional_k
    b_k = standard_k if b_games > provisional_limit else provisional_k

    if result == 0:
        w_score = 1
        b_score = 0
    elif result == 1:
        w_score = 0
        b_score = 1
    else:
        w_score = b_score = Decimal('0.5')

    pd_value = None
    for pair in pd:
        if pair[0] <= diff <= pair[1]:
            pd_value = pd[pair]

    if white >= black:
        w_expected_score = pd_value
        b_expected_score = 1 - pd_value
    else:
        b_expected_score = pd_value
        w_expected_score = 1 - pd_value

    new_w_rating = white.rating(ladder) + (w_score - w_expected_score) * w_k
    new_b_rating = black.rating(ladder) + (b_score - b_expected_score) * b_k
    return new_w_rating, new_b_rating
