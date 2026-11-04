# -*- coding: utf-8 -*-
##############################################################################
# ЛАБОРАТОРНАЯ РАБОТА: ВЫЧИСЛЕНИЯ НА ЭЛЛИПТИЧЕСКОЙ КРИВОЙ  y^2 = x^3 + a*x + b  (mod p)
#
# Один файл. Всё написано по методичке, поиск простого числа и все остальные
# шаги выполняются ПЕРЕБОРОМ (тест Миллера-Рабина не используется).
#
# Задание из методички:
#   1) выбрать простое p, примерно равное m*n*k, где m, n, k - номера букв инициалов
#      (можно взять две буквы);
#   2) перебором найти на кривой y^2 = x^3 + a*x + b точку P с минимальным
#      положительным x (a = 1, b = 0);
#   3) найти 151*P;
#   4) * найти порядок кривой (количество точек);
#   5) * найти порядок точки P.
#
# Запуск:
#   python elliptic_lab.py                  - решение для инициалов, записанных в INITIALS
#   python elliptic_lab.py МЮ               - решение для своих инициалов (две или три буквы)
#   python elliptic_lab.py ЭЮЯ 20 22        - то же, но для кривой с a = 20, b = 22 (пример 2 методички)
#   python elliptic_lab.py check            - автоматическая самопроверка программы
##############################################################################

import sys
import random
from math import isqrt


##############################################################################
# НАСТРОЙКИ (их можно менять)
##############################################################################

INITIALS = "СВН"        # инициалы; по умолчанию - из примера 1 методички (ответ p = 19319)
A = 1                   # коэффициент a кривой (по заданию a = 1)
B = 0                   # коэффициент b кривой (по заданию b = 0)
MULTIPLIER = 151        # на какое число умножаем точку (по заданию 151)

# Русский алфавит из 33 букв: А=1, Б=2, ..., Е=6, Ё=7, ..., С=19, ..., Э=31, Ю=32, Я=33.
# (Именно так нумеруют буквы примеры методички: С=19, В=3, Э=31, Ю=32, Я=33.)
ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


##############################################################################
# ЧАСТЬ 1. Простое число p: ищем ПЕРЕБОРОМ ДЕЛИТЕЛЕЙ (без теста Миллера-Рабина)
##############################################################################

def letter_number(letter):
    # Номер буквы в алфавите. Если такой буквы нет в алфавите, возвращаем 0.
    position = ALPHABET.find(letter.upper())
    if position == -1:
        return 0
    return position + 1


def initials_to_number(initials):
    # Номера букв записываем подряд: С=19, В=3, Н=15 -> "19" + "3" + "15" -> 19315.
    text = ""
    for letter in initials:
        number = letter_number(letter)
        if number == 0:
            print("Буква", letter, "не найдена в русском алфавите, пропускаем её")
        else:
            text = text + str(number)
    if text == "":
        return 0
    return int(text)


def smallest_divisor(n):
    # Наименьший делитель числа n, который больше 1.
    # Если такого делителя меньше самого n нет, то n простое, и функция вернёт само n.
    if n % 2 == 0:
        return 2
    d = 3
    while d * d <= n:          # дальше корня из n искать делители не нужно
        if n % d == 0:
            return d
        d = d + 2              # чётные делители уже проверены, идём по нечётным
    return n


def is_prime(n):
    if n < 2:
        return False
    return smallest_divisor(n) == n


def find_prime(start, show=True):
    # Наименьшее простое число, которое не меньше start.
    # Идём по числам start, start+1, ... и каждое проверяем делением.
    n = start
    while True:
        d = smallest_divisor(n)
        if d == n and n >= 2:
            if show:
                print("   p =", n, "- не делится ни на одно число от 2 до корня из", n, "=> ПРОСТОЕ")
            return n
        if show:
            print("   p =", n, "- делится на", d, "=> не простое, берём следующее число")
        n = n + 1


##############################################################################
# ЧАСТЬ 2. Обратный элемент по модулю (расширенный алгоритм Евклида из методички)
##############################################################################

def gcdex(a, b):
    # Возвращает тройку (d, x, y), где d = НОД(a, b) и x*a + y*b = d.
    if b == 0:
        return a, 1, 0
    d, x, y = gcdex(b, a % b)
    return d, y, x - y * (a // b)


def obr(a, p):
    # Находит a^(-1) mod p, то есть такое c, что a*c = 1 (mod p).
    # Если НОД(a, p) != 1, обратного нет и функция возвращает 0.
    g = gcdex(a % p, p)
    if g[0] == 1:
        return g[1] % p
    return 0


##############################################################################
# ЧАСТЬ 3. Кривая и поиск точки перебором
##############################################################################

def format_point(point):
    # Красивая запись точки. Бесконечно удалённая точка E хранится как None.
    if point is None:
        return "E (бесконечно удалённая)"
    return "(" + str(point[0]) + ", " + str(point[1]) + ")"


def is_nonsingular(a, b, p):
    # Кривая y^2 = x^3 + ax + b должна быть "гладкой": 4a^3 + 27b^2 != 0 (mod p).
    return (4 * a * a * a + 27 * b * b) % p != 0


def is_on_curve(point, a, b, p):
    if point is None:
        return True
    x = point[0]
    y = point[1]
    return (y * y - (x * x * x + a * x + b)) % p == 0


def find_point(a, b, p, show=True):
    # Перебором ищем точку с минимальным положительным x.
    # Для каждого x считаем правую часть x^3 + ax + b (mod p) и перебираем ВСЕ y от 0 до p-1,
    # пока не найдём y, для которого y^2 = правая часть (mod p).
    for x in range(1, p):
        right = (x * x * x + a * x + b) % p
        for y in range(p):
            if (y * y) % p == right:
                if show:
                    print("   x =", x, ": правая часть =", right, ", подходит y =", y, "=> точка P =", format_point((x, y)))
                return (x, y)
        if show:
            print("   x =", x, ": правая часть =", right, "- квадратом не является, подходящего y нет")
    return None


##############################################################################
# ЧАСТЬ 4. Сложение точек, удвоение, умножение на число
##############################################################################

def add_points(P, Q, a, p, show=False):
    # Сумма двух точек кривой по правилам методички. Все вычисления - по модулю p.
    # Правило 0: P + E = P.
    if P is None:
        if show:
            print("      правило 0: одно слагаемое равно E, сумма равна другому слагаемому")
        return Q
    if Q is None:
        if show:
            print("      правило 0: одно слагаемое равно E, сумма равна другому слагаемому")
        return P
    x1 = P[0]
    y1 = P[1]
    x2 = Q[0]
    y2 = Q[1]
    # Правило II: x одинаковые, а y противоположные => сумма равна E.
    # (Сюда попадает и удвоение точки с y = 0: тогда y + y = 0.)
    if x1 == x2 and (y1 + y2) % p == 0:
        if show:
            print("      правило II: x равны, y противоположны => сумма равна E")
        return None
    if x1 != x2:
        # Правило I: сложение разных точек.
        k = ((y2 - y1) * obr(x2 - x1, p)) % p
        if show:
            print("      правило I: k = (y2-y1)/(x2-x1) =", k)
    else:
        # Правило III: удвоение (x1 = x2 и y1 = y2).
        k = ((3 * x1 * x1 + a) * obr(2 * y1, p)) % p
        if show:
            print("      правило III (удвоение): k = (3*x1^2 + a)/(2*y1) =", k)
    x = (k * k - x1 - x2) % p          # формулы для x и y одинаковы в правилах I и III
    y = (k * (x1 - x) - y1) % p
    if show:
        print("      x = k^2 - x1 - x2 =", x, ", y = k*(x1 - x) - y1 =", y)
    return (x, y)


def negate_point(P, p):
    # Противоположная точка: (x, -y).
    if P is None:
        return None
    return (P[0], (-P[1]) % p)


def multiply(k, P, a, p):
    # Быстрое умножение k*P: идём по двоичной записи числа k.
    # Если последняя двоичная цифра k равна 1, добавляем к результату текущее "2^i * P".
    result = None            # результат пока E (нулевая точка)
    addend = P               # здесь будет P, 2P, 4P, 8P, ...
    while k > 0:
        if k % 2 == 1:
            result = add_points(result, addend, a, p)
        addend = add_points(addend, addend, a, p)
        k = k // 2
    return result


def multiply_slowly(k, P, a, p):
    # Умножение "в лоб": складываем P с собой k раз. Нужна только для проверки.
    result = None
    for i in range(k):
        result = add_points(result, P, a, p)
    return result


def powers_of_two_parts(n):
    # Раскладываем n в сумму степеней двойки, как в методичке:
    # из числа последовательно вычитаем наибольшую степень двойки, не превосходящую его.
    # Например, 151 = 128 + 16 + 4 + 2 + 1.
    parts = []
    while n > 0:
        power = 1
        while power * 2 <= n:
            power = power * 2
        parts.append(power)
        n = n - power
    return parts


def multiply_with_steps(n, P, a, p):
    # То же, что multiply, но по шагам, как в примере методички: сначала удвоения, потом сложения.
    parts = powers_of_two_parts(n)
    print("   Раскладываем", n, "на степени двойки:", " + ".join(str(x) for x in parts))
    biggest = parts[0]
    doubles = {1: P}
    current = P
    power = 1
    print("   Считаем 2^k * P последовательными удвоениями:")
    while power < biggest:
        print("     ", 2 * power, "P = 2 * ", format_point(current), sep="")
        if current is None:
            print("      удвоение E даёт E (правило 0)")
        else:
            current = add_points(current, current, a, p, True)
        power = power * 2
        doubles[power] = current
        print("      => ", power, "P = ", format_point(current), sep="")
    print("   Складываем нужные точки:")
    result = None
    for part in parts:
        print("     добавляем ", part, "P = ", format_point(doubles[part]), sep="")
        result = add_points(result, doubles[part], a, p, True)
        print("      => сумма пока равна", format_point(result))
    return result, doubles


##############################################################################
# ЧАСТЬ 5. Порядок кривой (количество точек), перебором
##############################################################################

def count_points(a, b, p):
    # Перебираем все x от 0 до p-1 и все возможные y: каждая пара (x, y), для которой
    # y^2 = x^3 + ax + b (mod p), - это точка кривой. К ним добавляется одна бесконечная точка E.
    # Чтобы не перебирать для каждого x все y заново (это p^2 действий, часы для больших p),
    # один раз перебираем y и запоминаем: сколько y даёт каждое значение y^2 mod p.
    how_many = [0] * p
    for y in range(p):
        how_many[(y * y) % p] = how_many[(y * y) % p] + 1
    s = 1                                    # бесконечная точка E
    for x in range(p):
        right = (x * x * x + a * x + b) % p
        s = s + how_many[right]
    return s


def count_points_slowly(a, b, p):
    # Тот же подсчёт, как в программе методички (двойной цикл, p^2 действий). Только для маленьких p.
    s = 1
    for x in range(p):
        right = (x * x * x + a * x + b) % p
        for y in range(p):
            if (y * y) % p == right:
                s = s + 1
    return s


def count_points_euler(a, b, p):
    # Второй способ из методички: правая часть - квадрат тогда и только тогда, когда
    # right^((p-1)/2) = 1 (mod p) (критерий Эйлера). Квадратов даёт 2 значения y, ноль - одно.
    s = 1
    for x in range(p):
        right = (x * x * x + a * x + b) % p
        if right == 0:
            s = s + 1
        elif pow(right, (p - 1) // 2, p) == 1:
            s = s + 2
    return s


def hasse_check(n, p):
    # Теорема Хассе: |N - (p + 1)| <= 2*sqrt(p), то есть (N - p - 1)^2 <= 4p.
    return (n - p - 1) * (n - p - 1) <= 4 * p


##############################################################################
# ЧАСТЬ 6. Порядок точки
##############################################################################

def factorize(n):
    # Разложение числа на простые множители делением: возвращает список пар (простое, степень).
    result = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n = n // d
                e = e + 1
            result.append((d, e))
        d = d + 1
    if n > 1:
        result.append((n, 1))
    return result


def point_order(P, group_order, a, p, show=False):
    # Порядок точки находим по двум утверждениям из приложения 3 методички:
    #   1) порядок точки делит порядок группы N, и N*P = E;
    #   2) если k*P = E и для каждого простого делителя q числа k верно (k/q)*P != E,
    #      то порядок точки равен k.
    # Начинаем с k = N и пытаемся "сократить" k на простые делители, пока (k/q)*P = E.
    k = group_order
    for q, e in factorize(group_order):
        for i in range(e):
            if k % q != 0:
                break
            test = multiply(k // q, P, a, p)
            if show:
                print("     проверяем (", k, "/", q, ")*P = ", k // q, "*P = ", format_point(test), sep="")
            if test is None:
                k = k // q
            else:
                break
    return k


def point_order_brute(P, a, p, limit):
    # Порядок точки "в лоб": прибавляем P, пока не получим E. Нужна только для проверки.
    current = P
    k = 1
    while current is not None:
        current = add_points(current, P, a, p)
        k = k + 1
        if k > limit:
            return -1
    return k


##############################################################################
# ЧАСТЬ 7. Полное решение лабораторной (все пункты задания)
##############################################################################

def solve(initials, a, b, multiplier):
    print("=" * 78)
    print("Кривая: y^2 = x^3 +", a, "* x +", b, " (mod p).  Инициалы:", initials)
    print("=" * 78)

    # ---- Пункт 1: простое p ----
    print()
    print("ПУНКТ 1. Выбираем простое число p.")
    numbers = []
    for letter in initials:
        numbers.append(letter_number(letter))
    print("   Номера букв:", ", ".join(initials[i] + "=" + str(numbers[i]) for i in range(len(initials))))
    start = initials_to_number(initials)
    print("   Записываем номера подряд: ", start)
    print("   Ищем ближайшее простое число, не меньшее", start, "(проверка делением):")
    p = find_prime(start)
    print("   ОТВЕТ: p =", p)
    if p < 5:
        print("   Число p слишком маленькое для кривой; возьмите инициалы с большими номерами букв")
        return None
    if not is_nonsingular(a, b, p):
        print("   Кривая вырожденная (4a^3 + 27b^2 = 0 mod p) - так нельзя")
        return None

    # ---- Пункт 2: точка ----
    print()
    print("ПУНКТ 2. Ищем перебором точку P с минимальным положительным x.")
    P = find_point(a, b, p)
    if P is None:
        print("   Точек с x > 0 нет")
        return None
    print("   Проверка: y^2 =", (P[1] * P[1]) % p, ", x^3 + ax + b =", (P[0] ** 3 + a * P[0] + b) % p,
          "(mod p) - равны:", is_on_curve(P, a, b, p))
    print("   ОТВЕТ: P =", format_point(P))

    # ---- Пункт 3: n*P ----
    print()
    print("ПУНКТ 3. Находим", multiplier, "* P.")
    Q, doubles = multiply_with_steps(multiplier, P, a, p)
    print("   ОТВЕТ:", multiplier, "P =", format_point(Q))
    print("   Проверка 1: точка лежит на кривой:", is_on_curve(Q, a, b, p))
    check_slow = multiply_slowly(multiplier, P, a, p)
    print("   Проверка 2: если сложить P с собой", multiplier, "раз подряд, получится", format_point(check_slow),
          "- совпало:", check_slow == Q)

    # ---- Пункт 4: порядок кривой ----
    print()
    print("ПУНКТ 4*. Порядок кривой (перебором считаем все точки).")
    n = count_points(a, b, p)
    print("   Порядок кривой |G| =", n, "(все конечные точки + одна бесконечная)")
    n2 = count_points_euler(a, b, p)
    print("   Проверка вторым способом (критерий Эйлера):", n2, "- совпало:", n == n2)
    print("   Проверка по теореме Хассе: |", n, "-", p + 1, "| =", abs(n - p - 1), "<= 2*sqrt(p) =",
          round(2 * (p ** 0.5), 1), "-", hasse_check(n, p))
    print("   ОТВЕТ: |G| =", n)

    # ---- Пункт 5: порядок точки ----
    print()
    print("ПУНКТ 5*. Порядок точки P.")
    print("   Порядок точки делит порядок кривой (утверждение 1). Проверяем: N*P = E:",
          multiply(n, P, a, p) is None)
    parts = factorize(n)
    text = " * ".join(str(q) + ("^" + str(e) if e > 1 else "") for q, e in parts)
    print("   Раскладываем", n, "на простые множители:", text)
    print("   Начинаем с k =", n, "и сокращаем k, пока (k/q)*P = E:")
    order = point_order(P, n, a, p, True)
    print("   Порядок точки найден: k =", order)
    print("   Проверка по утверждению 2: k*P = E:", multiply(order, P, a, p) is None)
    for q, e in factorize(order):
        print("      (", order, "/", q, ")*P =", format_point(multiply(order // q, P, a, p)),
              "- это не E:", multiply(order // q, P, a, p) is not None)
    if order <= 20000:
        brute = point_order_brute(P, a, p, order + 5)
        print("   Проверка прямым перебором (складываем P, пока не получим E):", brute, "- совпало:", brute == order)
    print("   ОТВЕТ: |P| =", order)

    # ---- Итог ----
    print()
    print("=" * 78)
    print("ИТОГ.  1) p =", p, "  2) P =", format_point(P), "  3)", multiplier, "P =", format_point(Q))
    print("       4) |G| =", n, "  5) |P| =", order)
    print("=" * 78)
    return {"p": p, "P": P, "nP": Q, "N": n, "order": order}


##############################################################################
# ЧАСТЬ 8. Самопроверка
##############################################################################

failures = 0
total = 0


def check(condition, message):
    global failures, total
    total = total + 1
    if not condition:
        failures = failures + 1
        print("   НЕ ПРОШЛО:", message)


def section(title):
    print(title)


def test_primes():
    section("1. Простые числа и нумерация букв")
    # решето Эратосфена как независимый способ
    limit = 20000
    sieve = [True] * (limit + 1)
    sieve[0] = False
    sieve[1] = False
    for i in range(2, limit + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    for n in range(limit + 1):
        check(is_prime(n) == sieve[n], "is_prime(%d)" % n)
    check(letter_number("С") == 19 and letter_number("В") == 3 and letter_number("Э") == 31, "номера букв")
    check(letter_number("Ю") == 32 and letter_number("Я") == 33 and letter_number("А") == 1, "номера букв 2")
    check(initials_to_number("ЭЮЯ") == 313233, "ЭЮЯ -> 313233 (пример 2)")
    check(find_prime(19314, False) == 19319, "пример 1: ближайшее простое к 19314 равно 19319")
    check(find_prime(19315, False) == 19319, "то же при Н=15")
    check(find_prime(313233, False) == 313241, "пример 2: ближайшее простое к 313233 равно 313241")
    check(find_prime(2, False) == 2 and find_prime(24, False) == 29, "малые числа")
    check(smallest_divisor(19314) == 2 and smallest_divisor(19315) == 5 and smallest_divisor(19317) == 3,
          "делители из примера 1")


def test_inverse():
    section("2. Обратный элемент")
    random.seed(1)
    for p in [5, 7, 101, 19319, 313241]:
        for i in range(200):
            a = random.randint(1, p - 1)
            check(obr(a, p) == pow(a, -1, p), "obr(%d, %d)" % (a, p))
            check((a * obr(a, p)) % p == 1, "a * a^(-1) = 1")
    check(obr(278, 19319) == 14524, "пример методички: 278^(-1) = 14524")
    check(gcdex(278, 19319) == (1, -4795, 69), "gcdex(278, 19319) = (1, -4795, 69)")
    check(obr(2 * 139, 19319) == 14524, "(2*139)^(-1) = 14524")
    check(obr(2 * 16565, 313241) == 263026, "(2*16565)^(-1) = 263026")
    # в методичке команда записана как obr(-295279, ...), но x2 - x1 = 3 - 295279 = -295276
    check(obr(3 - 295279, 313241) == 280182, "(3 - 295279)^(-1) = (-295276)^(-1) = 280182")


def test_example_1():
    section("3. Пример 1 методички: p = 19319, a = 1, b = 0")
    p = 19319
    P = find_point(1, 0, p, False)
    check(P == (1, 139), "точка P = (1, 139)")
    check(add_points(P, P, 1, p) == (0, 0), "2P = (0, 0)")
    check(add_points((0, 0), (0, 0), 1, p) is None, "4P = E")
    check(multiply(151, P, 1, p) == (1, 19180), "151P = (1, 19180)")
    check(multiply_slowly(151, P, 1, p) == (1, 19180), "151P = (1, 19180) сложением 151 раз")
    check(count_points(1, 0, p) == 19320, "порядок кривой 19320")
    check(count_points_euler(1, 0, p) == 19320, "порядок кривой 19320 (Эйлер)")
    check(point_order(P, 19320, 1, p) == 4, "порядок точки 4")


def test_example_2():
    section("4. Пример 2 методички: p = 313241, a = 20, b = 22")
    p = 313241
    a = 20
    b = 22
    P = find_point(a, b, p, False)
    check(P == (3, 16565), "точка P = (3, 16565)")
    # все промежуточные точки из методички
    pts = {}
    pts[1] = P
    expected = {2: (295279, 59147), 4: (145452, 56088), 8: (66413, 72431), 16: (290599, 127491),
                32: (86170, 104335), 64: (292650, 220324), 128: (62131, 147945),
                256: (26793, 219730), 512: (76849, 220967), 1024: (71538, 237641),
                2048: (68157, 15081), 4096: (242214, 186976), 8192: (88667, 220798),
                3: (127932, 220265), 7: (140220, 270773), 23: (105212, 156356),
                151: (98182, 39108), 11: (121122, 1329), 27: (287103, 118859), 59: (215606, 118353),
                571: (168488, 302393), 1595: (227824, 192351), 9787: (197962, 9052),
                19574: (228397, 278716), 39148: (146232, 197830), 78296: (8349, 0)}
    for k in expected:
        check(multiply(k, P, a, p) == expected[k], "%dP = %s" % (k, expected[k]))
    check(multiply(156592, P, a, p) is None, "156592P = E")
    check(multiply(313184, P, a, p) is None, "313184P = E")
    check(count_points(a, b, p) == 313184, "порядок кривой 313184")
    check(count_points_euler(a, b, p) == 313184, "порядок кривой 313184 (Эйлер)")
    check(factorize(313184) == [(2, 5), (9787, 1)], "313184 = 2^5 * 9787")
    check(point_order(P, 313184, a, p) == 156592, "порядок точки 156592")
    # независимая проверка прямым перебором (с быстрым обратным элементом из Python)
    current = P
    k = 1
    while current is not None:
        x1 = current[0]
        y1 = current[1]
        if x1 == P[0]:
            if (y1 + P[1]) % p == 0:
                current = None
            else:
                kk = ((3 * x1 * x1 + a) * pow(2 * y1, -1, p)) % p
                x = (kk * kk - 2 * x1) % p
                current = (x, (kk * (x1 - x) - y1) % p)
        else:
            kk = ((P[1] - y1) * pow(P[0] - x1, -1, p)) % p
            x = (kk * kk - x1 - P[0]) % p
            current = (x, (kk * (x1 - x) - y1) % p)
        k = k + 1
    check(k == 156592, "порядок точки прямым перебором равен 156592")


def small_primes():
    result = []
    for n in range(5, 60):
        if is_prime(n):
            result.append(n)
    return result


def test_group_law():
    section("5. Групповой закон на всех маленьких кривых")
    random.seed(5)
    curves = 0
    for p in small_primes():
        for a in range(p):
            for b in range(p):
                if not is_nonsingular(a, b, p):
                    continue
                curves = curves + 1
                n = count_points(a, b, p)
                if p <= 23:
                    check(n == count_points_slowly(a, b, p), "перебор и двойной цикл p=%d a=%d b=%d" % (p, a, b))
                check(n == count_points_euler(a, b, p), "перебор и Эйлер p=%d a=%d b=%d" % (p, a, b))
                check(hasse_check(n, p), "теорема Хассе p=%d a=%d b=%d" % (p, a, b))
                # соберём все точки
                points = []
                for x in range(p):
                    for y in range(p):
                        if (y * y - (x * x * x + a * x + b)) % p == 0:
                            points.append((x, y))
                check(len(points) + 1 == n, "число точек p=%d a=%d b=%d" % (p, a, b))
                if len(points) == 0:
                    continue
                # несколько случайных точек
                for i in range(3):
                    P = random.choice(points)
                    Q = random.choice(points)
                    R = random.choice(points)
                    S = add_points(P, Q, a, p)
                    check(is_on_curve(S, a, b, p), "сумма лежит на кривой")
                    check(S == add_points(Q, P, a, p), "коммутативность")
                    check(add_points(S, R, a, p) == add_points(P, add_points(Q, R, a, p), a, p), "ассоциативность")
                    check(add_points(P, negate_point(P, p), a, p) is None, "P + (-P) = E")
                    check(multiply(n, P, a, p) is None, "N*P = E p=%d a=%d b=%d" % (p, a, b))
                    k = random.randint(0, 40)
                    check(multiply(k, P, a, p) == multiply_slowly(k, P, a, p), "быстрое и медленное умножение")
                    order = point_order(P, n, a, p)
                    check(order == point_order_brute(P, a, p, n + 1), "порядок точки p=%d a=%d b=%d P=%s" % (p, a, b, P))
                    check(n % order == 0, "порядок точки делит порядок кривой")
    print("   проверено кривых:", curves)


def test_solve_runs():
    section("6. Полное решение для разных инициалов")
    for initials in ["СВН", "МЮ", "АБ", "ЭЮЯ", "ПЛК", "ЯЯ"]:
        start = initials_to_number(initials)
        p = find_prime(start, False)
        P = find_point(1, 0, p, False)
        if P is None:
            continue
        check(is_on_curve(P, 1, 0, p), "точка на кривой, " + initials)
        # минимальность x: для меньших x решений нет
        for x in range(1, P[0]):
            right = (x * x * x + x) % p
            found = False
            for y in range(p):
                if (y * y) % p == right:
                    found = True
            check(not found, "x=%d меньше найденного, решений быть не должно" % x)
        n = count_points(1, 0, p)
        check(multiply(n, P, 1, p) is None, "N*P = E, " + initials)
        # для кривой y^2 = x^3 + x при p = 3 (mod 4) порядок всегда p + 1
        if p % 4 == 3:
            check(n == p + 1, "при p = 3 mod 4 для y^2 = x^3 + x порядок p + 1, " + initials)


def run_checks():
    test_primes()
    test_inverse()
    test_example_1()
    test_example_2()
    test_group_law()
    test_solve_runs()
    print()
    print("Выполнено проверок: %d, не прошло: %d" % (total, failures))
    if failures == 0:
        print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        print("ЕСТЬ ОШИБКИ")
        sys.exit(1)


##############################################################################
# ЗАПУСК
##############################################################################

def main():
    args = sys.argv[1:]
    if len(args) > 0 and args[0].lower() in ["check", "проверка"]:
        run_checks()
        return
    initials = INITIALS
    a = A
    b = B
    if len(args) > 0:
        initials = args[0]
    if len(args) > 2:
        a = int(args[1])
        b = int(args[2])
    solve(initials, a, b, MULTIPLIER)


if __name__ == "__main__":
    main()
