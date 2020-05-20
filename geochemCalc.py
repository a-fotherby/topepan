def calcDelta(rareTope, commonTope, topeStd):
    delta = (((rareTope / commonTope) / topeStd) - 1) * 1000
    return delta