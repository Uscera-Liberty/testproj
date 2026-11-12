# -*- coding: utf-8 -*-
"""
Диффи-Хеллман на эллиптических кривых (ECDH) + взлом двумя способами.

ЧТО ЗА ЗАДАЧА (по пояснениям преподавателя из аудиозаписи)
    Обычный Диффи-Хеллман: у каждого есть секретная СТЕПЕНЬ, ключ получается возведением в степень.
    Диффи-Хеллман на эллиптической кривой - то же самое, но вместо возведения в степень стоит
    УМНОЖЕНИЕ ТОЧКИ НА ЧИСЛО (то есть сложение точки с самой собой k раз).
    Для быстрого умножения используем те же удвоения, что и в лабораторной по кривым.

    Задание 1. Сделать обмен ключами Алисы и Боба на кривой y^2 = x^3 + a*x + b (mod p).
    Задание 2. Взломать обмен: по открытым данным найти секретное число Алисы (дискретный логарифм
               на кривой) двумя способами:
                 1) полный перебор;
                 2) "шаг младенца, шаг великана" (вместо степеней - умножения на точку).
               Алгоритм исчисления порядка здесь НЕ применяем: он раскладывает числа на простые
               множители, а у точек кривой такого разложения нет (так объяснил преподаватель).

КАК РАБОТАЕТ ОБМЕН (коротко)
    Все знают кривую и общую точку G.
    Алиса выбирает секретное число a_secret, публикует A = a_secret * G.
    Боб   выбирает секретное число b_secret, публикует B = b_secret * G.
    Общий ключ:  Алиса считает a_secret * B,  Боб считает b_secret * A.
    Оба получают точку (a_secret * b_secret) * G - это и есть общий секрет.
    Злоумышленник знает только G, A, B. Чтобы получить ключ, ему надо найти a_secret по A и G.

ЗАПУСК
    python ecdh_lab.py                     - решение с моими секретами
    python ecdh_lab.py 12345 54321         - свои секретные числа Алисы и Боба
    python ecdh_lab.py check               - автоматическая проверка программы
"""

import sys
import time
import random


# ---------------------------------------------------------------------------
# НАСТРОЙКИ
# ---------------------------------------------------------------------------
# Кривая и точка из примера 2 методички по кривым (у неё большой порядок точки,
# поэтому секретные числа получаются большими и взлом наглядный).
P_MOD = 313241          # модуль p (простое число)
A = 20                  # коэффициент a в y^2 = x^3 + a*x + b
B = 22                  # коэффициент b
G = (3, 16565)          # общая точка (генератор), её знают все

ALICE_SECRET = 98765    # секретное число Алисы
BOB_SECRET = 54321      # секретное число Боба


# ---------------------------------------------------------------------------
# ЧАСТЬ 1. Арифметика по модулю и точки кривой
# ---------------------------------------------------------------------------

def is_prime(n):
    # Простое ли число: перебираем делители до корня (без теста Миллера-Рабина)
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d = d + 1
    return True


def gcdex(a, b):
    # Расширенный алгоритм Евклида: возвращает (d, x, y), где d = НОД(a, b), a*x + b*y = d
    if b == 0:
        return a, 1, 0
    d, x1, y1 = gcdex(b, a % b)
    return d, y1, x1 - (a // b) * y1


def obr(a, p):
    # Обратный элемент a^(-1) по модулю p (нужен, чтобы "делить" по модулю)
    d, x, y = gcdex(a % p, p)
    if d != 1:
        raise ValueError("нет обратного элемента")
    return x % p


# Точка кривой - пара (x, y). Бесконечно удалённая точка E ("ноль") хранится как None.

def is_on_curve(point, a, b, p):
    if point is None:
        return True
    x = point[0]
    y = point[1]
    return (y * y - (x * x * x + a * x + b)) % p == 0


def add_points(P, Q, a, p):
    # Сложение двух точек кривой (правила 0, I, II, III из методички)
    if P is None:                       # правило 0: E + Q = Q
        return Q
    if Q is None:                       # правило 0: P + E = P
        return P
    x1 = P[0]
    y1 = P[1]
    x2 = Q[0]
    y2 = Q[1]
    if x1 == x2 and (y1 + y2) % p == 0:     # правило II: точки-"зеркала" дают E
        return None
    if x1 != x2:                            # правило I: разные точки
        k = ((y2 - y1) * obr(x2 - x1, p)) % p
    else:                                   # правило III: удвоение
        k = ((3 * x1 * x1 + a) * obr(2 * y1, p)) % p
    x3 = (k * k - x1 - x2) % p
    y3 = (k * (x1 - x3) - y1) % p
    return (x3, y3)


def multiply(k, P, a, p):
    # Быстрое умножение k*P: идём по двоичной записи k.
    # Каждый шаг: если младший бит k равен 1 - прибавляем текущую точку к результату,
    # затем удваиваем текущую точку и сдвигаем k на один бит.
    result = None
    addend = P
    while k > 0:
        if k % 2 == 1:
            result = add_points(result, addend, a, p)
        addend = add_points(addend, addend, a, p)
        k = k // 2
    return result


def multiply_slowly(k, P, a, p):
    # Медленное умножение "в лоб": складываем P с собой k раз (нужно только для проверки)
    result = None
    for i in range(k):
        result = add_points(result, P, a, p)
    return result


def point_order(P, a, p):
    # Порядок точки: наименьшее n > 0, при котором n*P = E. Складываем P, пока не получим E.
    current = P
    n = 1
    while current is not None:
        current = add_points(current, P, a, p)
        n = n + 1
    return n


def point_to_str(P):
    if P is None:
        return "E (бесконечно удалённая)"
    return "(" + str(P[0]) + ", " + str(P[1]) + ")"


# ---------------------------------------------------------------------------
# ЗАДАНИЕ 1. Обмен ключами Диффи-Хеллмана на кривой
# ---------------------------------------------------------------------------

def diffie_hellman(a, b, p, G, n, alice_secret, bob_secret):
    print("Общие открытые данные: кривая y^2 = x^3 + " + str(a) + "x + " + str(b) + " (mod " + str(p) + ")")
    print("                       точка G =", point_to_str(G), ", порядок точки n =", n)
    print()

    # Секретные числа должны быть от 1 до n-1
    print("Секрет Алисы a_secret =", alice_secret, "(знает только Алиса)")
    print("Секрет Боба  b_secret =", bob_secret, "(знает только Боб)")
    print()

    # Открытые ключи
    A_pub = multiply(alice_secret, G, a, p)
    B_pub = multiply(bob_secret, G, a, p)
    print("Алиса публикует A = a_secret * G =", point_to_str(A_pub))
    print("Боб   публикует B = b_secret * G =", point_to_str(B_pub))
    print()

    # Общий секрет: каждый умножает чужой открытый ключ на свой секрет
    alice_shared = multiply(alice_secret, B_pub, a, p)
    bob_shared = multiply(bob_secret, A_pub, a, p)
    print("Алиса считает a_secret * B =", point_to_str(alice_shared))
    print("Боб   считает b_secret * A =", point_to_str(bob_shared))

    # Проверка: оба получили одно и то же и это точно (a_secret*b_secret)*G
    both = multiply((alice_secret * bob_secret) % n, G, a, p)
    print("Проверка: (a_secret*b_secret mod n) * G =", point_to_str(both))
    if alice_shared == bob_shared and alice_shared == both:
        print("Общий секрет совпал у обоих. Ключом считаем x-координату:", alice_shared[0])
    else:
        print("ОШИБКА: общий секрет не совпал!")
    print()
    return A_pub, B_pub, alice_shared


# ---------------------------------------------------------------------------
# ЗАДАНИЕ 2. Взлом: по G и A найти секрет Алисы (дискретный логарифм на кривой)
# ---------------------------------------------------------------------------

def brute_force_log(G, Q, n, a, p):
    # Способ 1. Полный перебор: считаем G, 2G, 3G, ... пока не получим Q.
    current = G
    for k in range(1, n):
        if current == Q:
            return k
        current = add_points(current, G, a, p)
    return None


def baby_giant_log(G, Q, n, a, p, show=True):
    # Способ 2. "Шаг младенца, шаг великана" - тот же алгоритм, что и для чисел,
    # только степень g^i превратилась в умножение i*G, а произведение - в сложение точек.
    #   Шаг 1. m = [sqrt(n)] + 1
    #   Шаг 2. H = m*G
    #   Шаг 3. u_i = i*H   (i = 1..m, "великан")   и   v_j = Q + j*G   (j = 1..m, "младенец")
    #   Шаг 4. ищем u_i = v_j, тогда  x = m*i - j  (mod n)
    m = int(n ** 0.5) + 1
    if show:
        print("  Шаг 1. m = [sqrt(" + str(n) + ")] + 1 =", m)

    H = multiply(m, G, a, p)
    if show:
        print("  Шаг 2. H = m*G =", point_to_str(H))

    # Таблица великанов: точка u_i -> номер i
    table = {}
    u = None
    for i in range(1, m + 1):
        u = add_points(u, H, a, p)
        if u not in table:
            table[u] = i
    if show:
        print("  Шаг 3. таблица u_i = i*H из", m, "точек построена, например u_1 =", point_to_str(multiply(1, H, a, p)),
              ", u_2 =", point_to_str(multiply(2, H, a, p)))

    # Младенцы: v_j = Q + j*G, ищем совпадение с таблицей
    v = Q
    for j in range(1, m + 1):
        v = add_points(v, G, a, p)
        if v in table:
            i = table[v]
            x = (m * i - j) % n
            if show:
                print("  Шаг 4. совпадение: u_" + str(i) + " = v_" + str(j) + " =", point_to_str(v))
                print("         x = m*i - j mod n = " + str(m) + "*" + str(i) + " - " + str(j)
                      + " mod " + str(n) + " =", x)
            return x
    return None


def hack(a, b, p, G, n, A_pub, B_pub, alice_shared):
    print("Злоумышленник Ева знает: кривую, G, A =", point_to_str(A_pub), ", B =", point_to_str(B_pub))
    print("Секреты ей неизвестны. Найдём a_secret из равенства  a_secret * G = A.")
    print()

    print("Способ 1. Полный перебор (G, 2G, 3G, ... до совпадения с A)")
    start = time.time()
    x1 = brute_force_log(G, A_pub, n, a, p)
    t1 = time.time() - start
    print("  Найдено a_secret =", x1, "  (время " + str(round(t1, 4)) + " с)")
    print()

    print("Способ 2. Шаг младенца, шаг великана")
    start = time.time()
    x2 = baby_giant_log(G, A_pub, n, a, p)
    t2 = time.time() - start
    print("  Найдено a_secret =", x2, "  (время " + str(round(t2, 4)) + " с)")
    print()

    print("Способ 3 (исчисление порядка) не применим: у точек кривой нет разложения на простые множители.")
    print()

    # Проверка: найденный секрет действительно даёт A, и с ним Ева получает общий ключ
    print("Проверка:")
    print("  x1 * G =", point_to_str(multiply(x1, G, a, p)), "(должно быть A)")
    stolen = multiply(x2, B_pub, a, p)
    print("  Ева считает x * B =", point_to_str(stolen), "(должно быть общим секретом)")
    if x1 == x2 and multiply(x1, G, a, p) == A_pub and stolen == alice_shared:
        print("  Оба способа дали один ответ, общий секрет Евой получен. Обмен ключами взломан.")
    else:
        print("  ОШИБКА: ответы не совпали!")
    print()
    return x1


# ---------------------------------------------------------------------------
# Основная часть
# ---------------------------------------------------------------------------

def run(alice_secret, bob_secret):
    p = P_MOD
    print("=" * 78)
    print("Подготовка")
    print("=" * 78)
    if not is_prime(p):
        print("ОШИБКА: p не простое")
        return
    if (4 * A * A * A + 27 * B * B) % p == 0:
        print("ОШИБКА: кривая вырождена")
        return
    if not is_on_curve(G, A, B, p):
        print("ОШИБКА: G не лежит на кривой")
        return
    print("p =", p, "простое, кривая невырожденная, G лежит на кривой.")
    start = time.time()
    n = point_order(G, A, p)
    print("Порядок точки G (складываем G с собой до E): n =", n, "  (время " + str(round(time.time() - start, 3)) + " с)")
    print("Проверка: n*G =", point_to_str(multiply(n, G, A, p)))
    if not (1 <= alice_secret < n and 1 <= bob_secret < n):
        print("ОШИБКА: секретные числа должны быть от 1 до n-1 =", n - 1)
        return
    print()

    print("=" * 78)
    print("ЗАДАНИЕ 1. Обмен ключами Диффи-Хеллмана на эллиптической кривой")
    print("=" * 78)
    A_pub, B_pub, shared = diffie_hellman(A, B, p, G, n, alice_secret, bob_secret)

    print("=" * 78)
    print("ЗАДАНИЕ 2. Взлом: поиск секретного числа Алисы")
    print("=" * 78)
    found = hack(A, B, p, G, n, A_pub, B_pub, shared)

    print("=" * 78)
    print("ИТОГ")
    print("  Секрет Алисы:", alice_secret, " найден взломом:", found)
    print("  Общий секрет (точка):", point_to_str(shared))
    print("=" * 78)


# ---------------------------------------------------------------------------
# Проверка программы
# ---------------------------------------------------------------------------

errors = 0
total = 0


def check(condition, message):
    global errors, total
    total = total + 1
    if not condition:
        errors = errors + 1
        print("  НЕ ПРОШЛО:", message)


def find_points(a, b, p):
    # Все точки кривой перебором (для маленьких p)
    result = []
    for x in range(p):
        right = (x * x * x + a * x + b) % p
        for y in range(p):
            if (y * y) % p == right:
                result.append((x, y))
    return result


def run_checks():
    print("1) Числа из методички (пример 2 по кривым): P = (3, 16565), p = 313241, a = 20, b = 22")
    P = (3, 16565)
    check(multiply(151, P, 20, 313241) == (98182, 39108), "151*P")
    check(multiply(16, P, 20, 313241) == (290599, 127491), "16*P")
    check(multiply(78296, P, 20, 313241) == (8349, 0), "78296*P")
    check(multiply(156592, P, 20, 313241) is None, "156592*P = E")
    check(point_order(P, 20, 313241) == 156592, "порядок точки P")

    print("2) Маленькие кривые: полная проверка всех секретов")
    random.seed(1)
    for p in [11, 13, 17, 31, 53, 101, 211, 307]:
        for a, b in [(1, 0), (2, 3), (20, 22), (5, 7)]:
            if (4 * a * a * a + 27 * b * b) % p == 0:
                continue
            points = find_points(a, b, p)
            if len(points) == 0:
                continue
            for G0 in points[:3]:
                if G0[1] == 0:
                    continue
                n = point_order(G0, a, p)
                if n < 3:
                    continue
                # умножение двумя способами должно совпадать на всех k
                for k in range(1, n):
                    Q = multiply(k, G0, a, p)
                    check(Q == multiply_slowly(k, G0, a, p), "умножение " + str(k) + " " + str(G0) + " " + str(p))
                    check(is_on_curve(Q, a, b, p), "результат на кривой")
                    # взлом обоими способами должен вернуть именно k (k < n)
                    if Q is not None:
                        check(brute_force_log(G0, Q, n, a, p) == k, "перебор k=" + str(k))
                        check(baby_giant_log(G0, Q, n, a, p, False) == k, "младенец-великан k=" + str(k))
                # n*G = E, (n+1)*G = G
                check(multiply(n, G0, a, p) is None, "n*G = E")
                check(multiply(n + 1, G0, a, p) == G0, "(n+1)*G = G")
                # Диффи-Хеллман: оба получают одно и то же
                for t in range(5):
                    sa = random.randint(1, n - 1)
                    sb = random.randint(1, n - 1)
                    A_pub = multiply(sa, G0, a, p)
                    B_pub = multiply(sb, G0, a, p)
                    check(multiply(sa, B_pub, a, p) == multiply(sb, A_pub, a, p), "общий секрет")

    print("3) Основная кривая: несколько случайных секретов (шаг младенца/великана и общий секрет)")
    n = 156592
    for t in range(10):
        sa = random.randint(1, n - 1)
        sb = random.randint(1, n - 1)
        A_pub = multiply(sa, G, A, P_MOD)
        B_pub = multiply(sb, G, A, P_MOD)
        check(multiply(sa, B_pub, A, P_MOD) == multiply(sb, A_pub, A, P_MOD), "ECDH на большой кривой")
        check(baby_giant_log(G, A_pub, n, A, P_MOD, False) == sa, "младенец-великан на большой кривой")
    # перебор на большой кривой проверяем для одного небольшого секрета
    A_pub = multiply(777, G, A, P_MOD)
    check(brute_force_log(G, A_pub, n, A, P_MOD) == 777, "перебор на большой кривой")

    print()
    print("Выполнено проверок:", total, ", не прошло:", errors)
    if errors == 0:
        print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")


def main():
    args = sys.argv[1:]
    if len(args) == 1 and args[0] == "check":
        run_checks()
    elif len(args) == 2:
        run(int(args[0]), int(args[1]))
    else:
        run(ALICE_SECRET, BOB_SECRET)


if __name__ == "__main__":
    main()
