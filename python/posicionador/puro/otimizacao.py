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


def nelder_mead(f, x0, simplex_inicial, maxfev, xatol=1e-6, fatol=1e-9):
    """Nelder–Mead (mesmos coeficientes e critérios do scipy: ρ=1, χ=2, ψ=0.5, σ=0.5; parada por xatol e fatol ou por
    `maxfev` avaliações, verificadas no início de cada iteração). `simplex_inicial`: N+1 vértices (listas). Devolve
    (x, f(x), número de avaliações)."""
    rho, chi, psi, sigma = 1.0, 2.0, 0.5, 0.5
    N = len(x0)
    sim = [list(v) for v in simplex_inicial]
    fcalls = 0
    fsim = []
    for v in sim:
        fsim.append(f(v))
        fcalls += 1

    def ordenar():
        idx = sorted(range(N + 1), key=lambda i: fsim[i])
        return [sim[i] for i in idx], [fsim[i] for i in idx]

    sim, fsim = ordenar()
    it, maxiter = 0, N * 200
    while fcalls < maxfev and it < maxiter:
        if (max(abs(sim[j][k] - sim[0][k]) for j in range(1, N + 1) for k in range(N)) <= xatol
                and max(abs(fsim[0] - fsim[j]) for j in range(1, N + 1)) <= fatol):
            break
        xbar = [sum(sim[j][k] for j in range(N)) / N for k in range(N)]
        xr = [(1 + rho) * xbar[k] - rho * sim[-1][k] for k in range(N)]
        fxr = f(xr)
        fcalls += 1
        shrink = False
        if fxr < fsim[0]:
            xe = [(1 + rho * chi) * xbar[k] - rho * chi * sim[-1][k] for k in range(N)]
            fxe = f(xe)
            fcalls += 1
            if fxe < fxr:
                sim[-1], fsim[-1] = xe, fxe
            else:
                sim[-1], fsim[-1] = xr, fxr
        elif fxr < fsim[-2]:
            sim[-1], fsim[-1] = xr, fxr
        else:
            if fxr < fsim[-1]:
                xc = [(1 + psi * rho) * xbar[k] - psi * rho * sim[-1][k] for k in range(N)]
                fxc = f(xc)
                fcalls += 1
                if fxc <= fxr:
                    sim[-1], fsim[-1] = xc, fxc
                else:
                    shrink = True
            else:
                xcc = [(1 - psi) * xbar[k] + psi * sim[-1][k] for k in range(N)]
                fxcc = f(xcc)
                fcalls += 1
                if fxcc < fsim[-1]:
                    sim[-1], fsim[-1] = xcc, fxcc
                else:
                    shrink = True
            if shrink:
                for j in range(1, N + 1):
                    sim[j] = [sim[0][k] + sigma * (sim[j][k] - sim[0][k]) for k in range(N)]
                    fsim[j] = f(sim[j])
                    fcalls += 1
        sim, fsim = ordenar()
        it += 1
    return sim[0], fsim[0], fcalls
