import random

def plusone(y):
    return y+1

if random.random() < 0.5:
    z = 1

y = 3
lambda x: x+1

[mode, nlines], (filename, x) = ('w', 4), ('test.txt', y)
with open(filename, mode) as bar:
    try:
        z
        for i in range(nlines):
            bar.write("that is odd!")
    except NameError as e:
        [bar.write(str(e)) for i in range(nlines) for j in range(plusone(i))]
    except IOError as e:
        raise e
    finally:
        try:
            bar.write("check done.")
        except IOError as e:
            pass

bar = mode
del bar
