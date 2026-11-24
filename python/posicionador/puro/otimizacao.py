"""Raiz de Brent em Python puro (substitui scipy.optimize.brentq do mecanismo)."""
import math


def brentq(f, a, b, xtol=1e-13, rtol=1e-12, maxiter=100):
    """Raiz de f em [a, b] (f(a) e f(b) de sinais opostos), método de Brent, mesma parametrização do scipy
    (critério: |x − x*| ≤ xtol + rtol·|x*|). ValueError se não há mudança de sinal; RuntimeError se não converge."""
    fa, fb = f(a), f(b)
    if fa * fb > 0.0:
        raise ValueError("f(a) e f(b) devem ter sinais opostos")
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    xpre, xcur = a, b
    fpre, fcur = fa, fb
    spre = scur = 0.0
    for _ in range(maxiter):
        if fpre != 0.0 and fcur != 0.0 and (math.copysign(1.0, fpre) != math.copysign(1.0, fcur)):
            xblk, fblk = xpre, fpre
            spre = scur = xcur - xpre
        if abs(fblk) < abs(fcur):
            xpre, xcur, xblk = xcur, xblk, xcur
            fpre, fcur, fblk = fcur, fblk, fcur
        delta = (xtol + rtol * abs(xcur)) / 2.0
        sbis = (xblk - xcur) / 2.0
        if fcur == 0.0 or abs(sbis) < delta:
            return xcur
        if abs(spre) > delta and abs(fcur) < abs(fpre):
            if xpre == xblk:
                stry = -fcur * (xcur - xpre) / (fcur - fpre)
            else:
                dpre = (fpre - fcur) / (xpre - xcur)
                dblk = (fblk - fcur) / (xblk - xcur)
                stry = -fcur * (fblk * dblk - fpre * dpre) / (dblk * dpre * (fblk - fpre))
            if 2.0 * abs(stry) < min(abs(spre), 3.0 * abs(sbis) - delta):
                spre, scur = scur, stry
            else:
                spre = scur = sbis
        else:
            spre = scur = sbis
        xpre, fpre = xcur, fcur
        xcur += scur if abs(scur) > delta else (delta if sbis > 0 else -delta)
        fcur = f(xcur)
    raise RuntimeError("brentq não convergiu")
