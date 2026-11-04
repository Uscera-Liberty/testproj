# -*- coding: utf-8 -*-
"""
Лабораторная работа: дискретное логарифмирование. Вариант 10.

ЧТО РЕШАЕМ
    Дано уравнение g^x = a (mod p). Известны g, a, p, нужно найти степень x.
    Это и есть "дискретный логарифм": x = log_g a.
    Вариант 10 (оба задания из файла с вариантами):
        часть 1:  11^x = 155 (mod 251)
        часть 2:   7^x =  97 (mod 263)

КАК РЕШАЕМ (три метода, как просил преподаватель)
    1) Полный перебор: считаем g^0, g^1, g^2, ... пока не получим a.
    2) "Шаг младенца, шаг великана" (по методичке): две таблицы
       u_i = (g^m)^i и v_j = a * g^j, ищем совпадение u_i = v_j, тогда x = m*i - j.
    3) Алгоритм исчисления порядка (index calculus, по методичке):
       сначала находим логарифмы маленьких простых чисел 2, 3, 5, 7,
       потом через них логарифм числа a.
    В конце проверка: pow(g, x, p) должно дать a.

ЗАПУСК
    python discrete_log_lab.py          - решить вариант 10 (обе части)
    python discrete_log_lab.py check    - проверить программу на примерах из методички
"""

import os
import sys
import time


# ---------------------------------------------------------------------------
# НАСТРОЙКИ: мой вариант (номер 10)
# ---------------------------------------------------------------------------
VARIANT = 10
TASKS = [
    # (название, g, a, p)
    ("Часть 1", 11, 155, 251),
    ("Часть 2", 7, 97, 263),
]

FACTOR_BASE = [2, 3, 5, 7]   # факторная база S (первые простые числа, как в примере методички)
C = 10                       # параметр надёжности c (в методичке c ~ 10)


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def gcdex(a, b):
    # Расширенный алгоритм Евклида: возвращает (d, x, y), где d = НОД(a, b) и a*x + b*y = d
    if b == 0:
        return a, 1, 0
    d, x1, y1 = gcdex(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    return d, x, y


def inverse(a, n):
    # Обратный элемент к a по модулю n. Если его нет (НОД(a, n) != 1) - возвращаем None
    d, x, y = gcdex(a % n, n)
    if d != 1:
        return None
    return x % n


def integer_sqrt(n):
    # Целая часть корня [sqrt(n)] без дробных чисел: подбираем перебором
    r = 0
    while (r + 1) * (r + 1) <= n:
        r = r + 1
    return r


# ---------------------------------------------------------------------------
# МЕТОД 1. Полный перебор
# ---------------------------------------------------------------------------

def brute_force(g, a, p):
    # Перебираем x = 0, 1, 2, ..., p-2 и каждый раз умножаем на g.
    # Как только g^x mod p стало равно a - это ответ.
    n = p - 1
    value = 1                      # g^0 = 1
    line = ""
    for x in range(n):
        line = line + "  " + str(g) + "^" + str(x) + "=" + str(value)
        if value == a:
            print(line + "   <-- совпало с a =", a)
            return x
        if x % 6 == 5:             # печатаем по 6 штук в строке, чтобы было компактно
            print(line)
            line = ""
        value = (value * g) % p    # переходим к следующей степени
    print(line)
    return None


# ---------------------------------------------------------------------------
# МЕТОД 2. "Шаг младенца, шаг великана" (строго по алгоритму из методички)
# ---------------------------------------------------------------------------

def baby_giant(g, a, p):
    n = p - 1

    # Шаг 1. m = [sqrt(p)] + 1
    m = integer_sqrt(p) + 1
    print("  Шаг 1. m = [sqrt(" + str(p) + ")] + 1 =", m)

    # Шаг 2. b = g^m mod p
    b = pow(g, m, p)
    print("  Шаг 2. b = " + str(g) + "^" + str(m) + " mod " + str(p) + " =", b)

    # Шаг 3 (первая половина). Таблица u_i = b^i, i = 1..m ("шаги великана")
    table_u = {}                   # словарь: значение u_i -> номер i
    u_list = []
    u = 1
    for i in range(1, m + 1):
        u = (u * b) % p
        u_list.append(u)
        if u not in table_u:       # если значение повторилось, запоминаем первое
            table_u[u] = i
    print("  Шаг 3. u_i = b^i:  ", u_list)

    # Шаг 3 (вторая половина) + Шаг 4. Считаем v_j = a * g^j, j = 1..m ("шаги младенца"),
    # пока v_j не найдётся среди u_i.
    v_list = []
    v = a
    for j in range(1, m + 1):
        v = (v * g) % p
        v_list.append(v)
        if v in table_u:
            i = table_u[v]
            print("         v_j = a*g^j:", v_list)
            x = (m * i - j) % n
            print("  Шаг 4. совпадение u_" + str(i) + " = v_" + str(j) + " = " + str(v))
            print("         x = m*i - j mod n = " + str(m) + "*" + str(i) + " - " + str(j)
                  + " mod " + str(n) + " =", x)
            return x
    print("         v_j = a*g^j:", v_list)
    print("  Совпадение не найдено")
    return None


# ---------------------------------------------------------------------------
# МЕТОД 3. Алгоритм исчисления порядка (index calculus, по методичке)
# ---------------------------------------------------------------------------

def factor_over_base(number, base):
    # Пробуем разложить number по простым из факторной базы.
    # Возвращаем список степеней [alpha_1, ..., alpha_t] или None, если не разложилось.
    powers = []
    for q in base:
        count = 0
        while number % q == 0:
            number = number // q
            count = count + 1
        powers.append(count)
    if number == 1:
        return powers
    return None


def powers_to_str(powers, base):
    # [3, 0, 1, 0] -> "2^3 * 5"   (для красивой печати)
    parts = []
    for i in range(len(base)):
        if powers[i] == 1:
            parts.append(str(base[i]))
        elif powers[i] > 1:
            parts.append(str(base[i]) + "^" + str(powers[i]))
    if len(parts) == 0:
        return "1"
    return " * ".join(parts)


def solve_system(rows, right, n):
    # Решаем систему сравнений  rows * L = right (mod n)  методом Гаусса.
    # n = p - 1 составное, поэтому делить можно только на числа, взаимно простые с n.
    # Если подходящего (обратимого) ведущего элемента не нашлось - возвращаем None
    # (тогда нужно добрать ещё сравнений и попробовать снова).
    t = len(rows[0])
    A = []
    for k in range(len(rows)):
        A.append(rows[k][:] + [right[k]])      # расширенная матрица (копия)

    row = 0
    for col in range(t):
        pivot = -1
        for r in range(row, len(A)):
            if inverse(A[r][col], n) is not None:
                pivot = r
                break
        if pivot == -1:
            return None
        A[row], A[pivot] = A[pivot], A[row]     # ставим строку с обратимым элементом наверх
        inv = inverse(A[row][col], n)
        for c in range(t + 1):                  # делим строку на ведущий элемент
            A[row][c] = (A[row][c] * inv) % n
        for r in range(len(A)):                 # вычитаем её из всех остальных строк
            if r != row and A[r][col] != 0:
                factor = A[r][col]
                for c in range(t + 1):
                    A[r][c] = (A[r][c] - factor * A[row][c]) % n
        row = row + 1

    answer = []
    for col in range(t):
        answer.append(A[col][t])
    return answer


def index_calculus(g, a, p, base, c):
    n = p - 1
    t = len(base)

    # Шаг 1. Факторная база
    print("  Шаг 1. Факторная база S =", base, " (t = " + str(t) + "), c =", c)

    # Шаги 2-5. Берём k = 1, 2, 3, ... и раскладываем g^k mod p по базе.
    # Каждое удачное разложение даёт сравнение  k = сумма alpha_i * log(p_i)  (mod n).
    print("  Шаги 2-5. Ищем k, для которых g^k mod p раскладывается по S:")
    rows = []
    right = []
    logs = None
    k = 1
    while k < n:
        value = pow(g, k, p)
        powers = factor_over_base(value, base)
        if powers is not None:
            rows.append(powers)
            right.append(k)
            print("     k = " + str(k).rjust(3) + ":  " + str(g) + "^" + str(k) + " mod " + str(p)
                  + " = " + str(value).rjust(3) + " = " + powers_to_str(powers, base))
            # Шаг 5: как только набралось t + c сравнений (и дальше после каждого нового) -
            # пробуем решить систему
            if len(rows) >= t + c:
                logs = solve_system(rows, right, n)
                if logs is not None:
                    break
        k = k + 1

    if logs is None:
        print("  Систему решить не удалось")
        return None

    # Шаг 6. Решение системы - логарифмы элементов факторной базы
    print("  Шаг 6. Решили систему из " + str(len(rows)) + " сравнений по модулю n = " + str(n) + ":")
    for i in range(t):
        ok = pow(g, logs[i], p) == base[i]
        print("     log_" + str(g) + "(" + str(base[i]) + ") = " + str(logs[i])
              + "   проверка " + str(g) + "^" + str(logs[i]) + " mod " + str(p) + " = "
              + str(pow(g, logs[i], p)) + (" верно" if ok else " ОШИБКА"))

    # Шаги 7-8. Ищем k, при котором a * g^k mod p раскладывается по базе
    print("  Шаги 7-8. Ищем k, для которого a * g^k mod p раскладывается по S:")
    for k in range(n):
        value = (a * pow(g, k, p)) % p
        powers = factor_over_base(value, base)
        if powers is None:
            print("     k = " + str(k) + ":  " + str(a) + "*" + str(g) + "^" + str(k) + " mod " + str(p)
                  + " = " + str(value) + " - не раскладывается")
            continue
        print("     k = " + str(k) + ":  " + str(a) + "*" + str(g) + "^" + str(k) + " mod " + str(p)
              + " = " + str(value) + " = " + powers_to_str(powers, base))

        # Шаг 9. x = сумма beta_i * log(p_i) - k  (mod n)
        total = 0
        text = ""
        for i in range(t):
            if powers[i] != 0:
                total = total + powers[i] * logs[i]
                if text != "":
                    text = text + " + "
                text = text + str(powers[i]) + "*" + str(logs[i])
        x = (total - k) % n
        print("  Шаг 9. x = " + text + " - " + str(k) + " mod " + str(n) + " =", x)
        return x
    return None


# ---------------------------------------------------------------------------
# Решение одного задания всеми тремя методами + проверка
# ---------------------------------------------------------------------------

def solve_task(name, g, a, p):
    print("=" * 78)
    print(name + ":  " + str(g) + "^x = " + str(a) + " (mod " + str(p) + "),   n = p - 1 =", p - 1)
    print("=" * 78)

    print("\nМетод 1. Полный перебор")
    start = time.time()
    x1 = brute_force(g, a, p)
    t1 = time.time() - start
    print("  Ответ: x =", x1)

    print("\nМетод 2. Шаг младенца, шаг великана")
    start = time.time()
    x2 = baby_giant(g, a, p)
    t2 = time.time() - start
    print("  Ответ: x =", x2)

    print("\nМетод 3. Алгоритм исчисления порядка")
    start = time.time()
    x3 = index_calculus(g, a, p, FACTOR_BASE, C)
    t3 = time.time() - start
    print("  Ответ: x =", x3)

    print("\nИтог и проверка:")
    print("  перебор:                 x =", x1, "  время", round(t1, 5), "с")
    print("  шаг младенца/великана:   x =", x2, "  время", round(t2, 5), "с")
    print("  исчисление порядка:      x =", x3, "  время", round(t3, 5), "с")
    print("  Проверка: pow(" + str(g) + ", " + str(x1) + ", " + str(p) + ") =", pow(g, x1, p),
          "(должно быть " + str(a) + ")")
    if x1 == x2 and x2 == x3 and pow(g, x1, p) == a:
        print("  Все три метода дали одно и то же, проверка пройдена. ОТВЕТ: x =", x1)
    else:
        print("  ВНИМАНИЕ: ответы не совпали!")
    print()
    return x1


# ---------------------------------------------------------------------------
# Проверка программы на примерах из методички и на всех вариантах
# ---------------------------------------------------------------------------

def run_checks():
    errors = 0

    print("Пример из методички (шаг младенца/великана): 6^x = 12 (mod 229), ответ 22")
    x = baby_giant(6, 12, 229)
    if x != 22:
        errors = errors + 1
    print()

    print("Пример из методички (исчисление порядка): 7^x = 26 (mod 71), ответ 45")
    x = index_calculus(7, 26, 71, [2, 3, 5, 7], 0)
    if x != 45:
        errors = errors + 1
    print()

    # Все 34 варианта обеих частей: три метода должны совпасть и пройти проверку pow
    print("Проверяем все варианты из файла с заданиями (вывод методов скрыт)...")
    part1 = [101, 56, 163, 198, 58, 199, 172, 192, 74, 155, 73, 242, 225, 149, 218, 178, 156,
             149, 238, 100, 238, 178, 32, 131, 26, 176, 227, 142, 145, 70, 69, 117, 135, 38]
    part2 = [233, 253, 255, 26, 108, 248, 15, 174, 85, 97, 23, 32, 174, 260, 162, 235, 186,
             153, 20, 12, 28, 198, 22, 176, 162, 94, 146, 262, 105, 4, 19, 48, 78, 23]
    real_stdout = sys.stdout
    count = 0
    for g, p, values in [(11, 251, part1), (7, 263, part2)]:
        for a in values:
            sys.stdout = open(os.devnull, "w")     # временно отключаем печать
            x1 = brute_force(g, a, p)
            x2 = baby_giant(g, a, p)
            x3 = index_calculus(g, a, p, FACTOR_BASE, C)
            sys.stdout.close()
            sys.stdout = real_stdout
            count = count + 1
            if not (x1 == x2 == x3 and pow(g, x1, p) == a):
                errors = errors + 1
                print("  ошибка:", g, a, p, x1, x2, x3)
    print("  проверено вариантов:", count)
    print("  вариант 11 (для сверки с тем, кто сдал): x =", brute_force_silent(11, 73, 251),
          "(у него 44)")

    print()
    if errors == 0:
        print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        print("ОШИБОК:", errors)


def brute_force_silent(g, a, p):
    # тот же перебор, только без печати
    value = 1
    for x in range(p - 1):
        if value == a:
            return x
        value = (value * g) % p
    return None


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        run_checks()
        return
    print("Дискретное логарифмирование. Вариант", VARIANT)
    print()
    answers = []
    for name, g, a, p in TASKS:
        answers.append(solve_task(name, g, a, p))
    print("ОТВЕТЫ ВАРИАНТА " + str(VARIANT) + ":")
    for k in range(len(TASKS)):
        name, g, a, p = TASKS[k]
        print("  " + name + ": " + str(g) + "^x = " + str(a) + " (mod " + str(p) + ")  =>  x =",
              answers[k], "   проверка: print(pow(" + str(g) + ", " + str(answers[k]) + ", "
              + str(p) + ")) ->", pow(g, answers[k], p))


if __name__ == "__main__":
    main()
