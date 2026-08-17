import numpy as np
from scipy.optimize import least_squares
import math
import itertools
import random

def fit_svi(xs, ys, t, max_checks = 15, max_iters = 50):

    if len(xs) < 8:
        raise ValueError("Too less points, should have at least 8 points")
    
    # Market Implied Total Variance
    w_mkt = (ys**2)*t
    
    # Initial parameter values
    sample_init = initializer(xs, w_mkt)
    
    # Parameter bounds
    bounds = bounder()
    
    # Residual function
    f_svi = lambda params, x, y: params[0] + params[1]*(params[2]*(x - params[3]) + \
                                                  np.sqrt((x - params[3])**2 + params[4]**2)) - y
    n_valids = 0 # Number of valid iterations
    n_iters = 0 # Number of iterations
    rmse_min = math.inf
    params_best = [0, 0, 0, 0, 0]
    svi_success = False
    for params0 in sample_init:
        res = least_squares(f_svi, params0, jac = jacobian, bounds = bounds, args = (xs, w_mkt))
        rmse, check = fit_quality(res, xs)
        n_iters += 1
        if check:
            n_valids += 1
            if rmse < rmse_min:
                params_best = res.x
                rmse_min = rmse
                svi_success = True
        
        if n_valids >= max_checks or n_iters >= max_iters:
            break

    if svi_success:
        return params_best, rmse_min
    else:
        raise RuntimeError("SVI calibration failed")

def jacobian(params, x, y):
    n = len(x)
    a, b, rho, m, sigma = params
    jac = np.ones((n, 5))
    jac[:, 0] = 1
    jac[:, 1] = rho*(x-m) + np.sqrt((x-m)**2 + sigma**2)
    jac[:, 2] = b*(x-m)
    jac[:, 3] = -1*b*rho + b*(m - x)/np.sqrt((x-m)**2 + sigma**2)
    jac[:, 4] = b*sigma/(np.sqrt((x-m)**2 + sigma**2))
    return jac

def initializer(xs, w_mkt):
    # Need to change this to a geometry informed starting guess later for a0, b0, rho0, m0, sigma0
    
    # Initial parameter values
    a0 = np.mean(w_mkt)
    a_init = [0.5*a0, a0, 1.5*a0]
    m0 = 1e-4
    m_init = [m0 - 0.05, m0-0.02, m0, m0 + 0.02, m0 + 0.05]
    rho0 = -0.5
    rho_init = [0.5*rho0, rho0, 1.5*rho0, 0]
    w_max = np.max(w_mkt)
    w_min = np.min(w_mkt)
    x_max = np.max(xs)
    x_min = np.min(xs)
    b0 = (w_max - w_min)/abs(x_max - x_min)
    b_init = [0.5*b0, b0, 1.5*b0]
    sigma0 = 0.1
    sigma_init = [0.5*sigma0, sigma0, 1.5*sigma0]

    base_guess = tuple([a0, b0, rho0, m0, sigma0])
    random_guess = list(itertools.product(a_init, b_init, rho_init, m_init, sigma_init))
    random_guess.remove(base_guess)
    
    random.seed(42)
    random.shuffle(random_guess)

    guess = [base_guess] + random_guess # To always start with the base guess
    return guess

def bounder():
    # Gives upper and lower bounds
    epsilon = 1e-6
    a_min = -math.inf
    a_max = math.inf
    b_min = 0
    b_max = math.inf
    rho_min = -0.98+epsilon
    rho_max = 0.98-epsilon
    m_min = -math.inf
    m_max= math.inf
    sigma_min = epsilon
    sigma_max = math.inf
    params_min = [a_min, b_min, rho_min, m_min, sigma_min]
    params_max = [a_max, b_max, rho_max, m_max, sigma_max]
    bounds = (params_min, params_max)
    return bounds

def fit_quality(res, xs):
    # Returns False if optimization was not successful,
    if not res.success:
        return -1, False
    
    params = res.x
    butterfly_check = butterfly_arb_check(params)
    min_var_check = min_total_variance_check(params, xs)
    param_check = params_check(params, xs)
    
    if butterfly_check and min_var_check and param_check:
        n = len(xs)
        return math.sqrt(2*res.cost/n), True
    else:
        return -1, False

def params_check(params, xs):
    step = 0.01
    a, b, rho, m, sigma = params
    xs_min = np.min(xs)
    xs_max = np.max(xs)
    if abs(rho)>0.98 or sigma < 0.01 or sigma > 2 or m < xs_min - 10*step or m > xs_max + 10*step:
        return False
    else:
        return True

def butterfly_arb_check(params):
    a, b, rho, m, sigma = params
    
    # Intra-Smile Butterfly arbitrage: Roger Lee's Moment Formulas and Ferhati's paper
    moment_check_1 = (a - m*b*(rho+1))*(4 - a + m*b*(rho+1)) > (b**2)*((rho + 1)**2)
    moment_check_2 = (a - m*b*(rho-1))*(4 - a + m*b*(rho-1)) > (b**2)*((rho - 1)**2)
    moment_check_3 = 0 < (b**2)*(rho+1)**2 < 4
    moment_check_4 = 0 < (b**2)*(rho-1)**2 < 4
    moment_check = moment_check_1 and moment_check_2 and moment_check_3 and moment_check_4

    return moment_check

def min_total_variance_check(params, xs):
    a, b, rho, m, sigma = params
    n = len(xs)
    step = 0.01
    xs_min = np.min(xs)
    xs_max = np.max(xs)
    x_grid = np.arange(xs_min-50*step, xs_max+51*step, step)
    w_svi = a + b*(rho*(x_grid - m) + np.sqrt((x_grid-m)**2 + sigma**2))

    if a + b*sigma*math.sqrt(1-rho**2) < 0 or np.min(w_svi) <= 0:
        return False
    else:
        return True

def calendar_arb_check(params_by_tenor, tenors):
    x_grid = np.arange(-0.1, 0.101, 0.01)
    violations = []
    tol = 1e-7
    for i in range(len(tenors) - 1):
        t1 = tenors[i]
        t2 = tenors[i+1]
        a, b, rho, m, sigma = params_by_tenor[i+1]
        a_prev, b_prev, rho_prev, m_prev, sigma_prev = params_by_tenor[i]
        for x in x_grid:
            w_svi = a + b*(rho*(x - m) + np.sqrt((x - m)**2 + sigma**2))
            w_svi_prev = a_prev + b_prev*(rho_prev*(x - m_prev) + \
                                          np.sqrt((x - m_prev)**2 + sigma_prev**2))
            if w_svi + tol < w_svi_prev:
                violations.append((t1, t2, x))

    return violations
