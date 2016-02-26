def bogus2(white, black, result):
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
    return (white, black)

