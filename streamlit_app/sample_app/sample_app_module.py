from handcalcs.decorator import handcalc
import math

# Example calcs with handcalcs
hc_renderer = handcalc(override='long')


def _sample_calc1(a, b):
    z = a / b
    return z

def _sample_calc2(a, b):
    y = a ** b
    return y

@handcalc()
def other_calc(a,b):
    F_y = math.sqrt(a**2 + b **2)
    return F_y

calc1 = hc_renderer(_sample_calc1)
calc2 = hc_renderer(_sample_calc2)

def sample_main_calculation(a: float, b: float):
    """
    Doc strings
    """
    latex1, _ = calc1(a,b)
    latex2, _ = calc2(a,b)
    latex3, calculated_value = other_calc(
        a,
        b
        )
    return [latex1, latex2, latex3], calculated_value




