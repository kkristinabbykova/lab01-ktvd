"""labstat: библиотека из основной части Lab01 (автор Нефедьева А. С., трек «Инфохимия»).

Скопирована без изменений логики: доп. задание КТвД использует те же функции,
чтобы статистика и стиль графиков совпадали с основной работой.

Громоздкий код вынесен сюда, чтобы ноутбук читался как исследование.
"""
from . import data, dependence, describe, distributions, estimation, hypotheses, normalize, sampling, stochastic

__all__ = ["data", "dependence", "describe", "distributions", "estimation", "hypotheses",
           "normalize", "sampling", "stochastic"]
