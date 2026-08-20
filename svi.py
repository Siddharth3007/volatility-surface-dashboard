import numpy as np
from scipy.optimize import least_squares
from scipy.optimize import minimize
import math
import itertools
import random
import time

def make_x_grid(xs, step = 0.01, buffer = 5):
    # Making a uniform grid for constraints and checks
    xs_min = np.min(xs)
    xs_max = np.max(xs)
    x_grid = np.arange(xs_min - buffer*step, xs_max + (buffer + 1)*step, step)
    return x_grid

def initializer(xs, w_mkt):
    
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
    
    bounds = list(zip(params_min, params_max))
        
    return bounds

def fit_quality(res, xs):
    # Returns False if optimization was not successful.
    if not res.success:
        return False
    
    params = res.x
    butterfly_check = gatheral_check(params, xs)
    moment_check = lee_check(params)
    min_var_check = min_total_variance_check(params, xs)
    param_check = params_check(params, xs)
    
    if min_var_check and param_check and butterfly_check and moment_check:
        return True
    else:
        return False

def params_check(params, xs):
    step = 0.01
    a, b, rho, m, sigma = params
    xs_min = np.min(xs)
    xs_max = np.max(xs)
    if abs(rho)>0.98 or sigma < 0.01 or sigma > 2 or m < xs_min - 10*step or m > xs_max + 10*step:
        return False
    else:
        return True

def lee_check(params):
    a, b, rho, m, sigma = params
    
    # Intra-Smile Butterfly arbitrage: Roger Lee's Moment Formulas and Ferhati's paper
    moment_check_1 = (a - m*b*(rho+1))*(4 - a + m*b*(rho+1)) > (b**2)*((rho + 1)**2)
    moment_check_2 = (a - m*b*(rho-1))*(4 - a + m*b*(rho-1)) > (b**2)*((rho - 1)**2)
    moment_check_3 = 0 < (b**2)*(rho+1)**2 < 4
    moment_check_4 = 0 < (b**2)*(rho-1)**2 < 4
    moment_check = moment_check_1 and moment_check_2 and moment_check_3 and moment_check_4

    return moment_check

def gatheral_values(params, xs):
    x_grid = make_x_grid(xs)

    a, b, rho, m, sigma = params
    w = a + b*(rho*(x_grid-m) + np.sqrt((x_grid-m)**2 + sigma**2))
    w_x = b*rho + b*(x_grid-m)/np.sqrt((x_grid-m)**2 + sigma**2)
    w_xx = b*sigma**2/((x_grid-m)**2 + sigma**2)**1.5

    g = (1 - (0.5*x_grid*w_x/w))**2 - 0.25*(w_x**2)*((1/w) + 0.25) + 0.5*w_xx

    return g

def gatheral_check(params, xs):
    g = gatheral_values(params, xs)

    if np.all(g>=-1e-7):
        return True
    else:
        return False

def min_total_variance_check(params, xs):
    a, b, rho, m, sigma = params
    n = len(xs)
    x_grid = make_x_grid(xs)
    w_svi = a + b*(rho*(x_grid - m) + np.sqrt((x_grid-m)**2 + sigma**2))

    if a + b*sigma*math.sqrt(1-rho**2) < 0 or np.min(w_svi) <= 0:
        return False
    else:
        return True

def calendar_arb_check(params, params_prev, xs, t, t_prev):
    x_grid = make_x_grid(xs)
    violations = []
    tol = 1e-7
    violation_sq = 0
    a, b, rho, m, sigma = params
    a_prev, b_prev, rho_prev, m_prev, sigma_prev = params_prev
    
    for x in x_grid:
        w_svi = a + b*(rho*(x - m) + np.sqrt((x - m)**2 + sigma**2))
        w_svi_prev = a_prev + b_prev*(rho_prev*(x - m_prev) + \
                                      np.sqrt((x - m_prev)**2 + sigma_prev**2))
        
        if w_svi + tol < w_svi_prev:
            violations.append((t_prev, t, x))
            violation_sq += (w_svi_prev - w_svi)**2

    if len(violations) > 0:
        return math.sqrt(violation_sq/len(violations)), violations, False
    else:
        return 0, violations, True

def svi_butterfly(params):
    a, b, rho, m, sigma = params

    # Based on Lee's moment checks
    con_1 = (a - m*b*(rho+1))*(4 - a + m*b*(rho+1)) - (b**2)*((rho + 1)**2)
    con_2 = (a - m*b*(rho-1))*(4 - a + m*b*(rho-1)) - (b**2)*((rho - 1)**2)
    con_3 = 4 - (b**2)*(rho+1)**2
    con_4 = 4 - (b**2)*(rho-1)**2

    return np.array([con_1, con_2, con_3, con_4])

def svi_calendar(params, params_prev, xs):
    a, b, rho, m, sigma = params
    a_prev, b_prev, rho_prev, m_prev, sigma_prev = params_prev
    
    x_grid = make_x_grid(xs)
    cons = []
    tol = 1e-7
    
    for x in x_grid:
        w_svi = a + b*(rho*(x - m) + np.sqrt((x - m)**2 + sigma**2))
        w_svi_prev = a_prev + b_prev*(rho_prev*(x - m_prev) + \
                                      np.sqrt((x - m_prev)**2 + sigma_prev**2))
        cons.append(w_svi - w_svi_prev - tol)

    return np.array(cons)

def svi_min_var(params, xs):
    a, b, rho, m, sigma = params

    # x_grid = np.arange(-0.1, 0.101, 0.01)
    x_grid = make_x_grid(xs)
    tol = 1e-7
    
    w_svi = a + b*(rho*(x_grid - m) + np.sqrt((x_grid-m)**2 + sigma**2))

    return w_svi - tol

def svi_constraints(params, xs, params_prev = None, calendar = True):
    con_butterfly = svi_butterfly(params)
    con_min_var = svi_min_var(params, xs)
    
    if calendar:
        con_calendar = svi_calendar(params, params_prev, xs)
        return np.concatenate((con_butterfly, con_min_var, con_calendar))
    else:
        return np.concatenate((con_butterfly, con_min_var))

def calc_svi_density(params, xs, F):
    x_grid = make_x_grid(xs)

    a, b, rho, m, sigma = params
    w = a + b*(rho*(x_grid-m) + np.sqrt((x_grid-m)**2 + sigma**2))
    w_x = b*rho + b*(x_grid-m)/np.sqrt((x_grid-m)**2 + sigma**2)
    w_xx = b*sigma**2/((x_grid-m)**2 + sigma**2)**1.5

    g = (1 - (0.5*x_grid*w_x/w))**2 - 0.25*(w_x**2)*((1/w) + 0.25) + 0.5*w_xx

    d2 = (-1*x_grid/np.sqrt(w)) - 0.5*np.sqrt(w)

    q = (g/np.sqrt(2*math.pi*w))*np.exp(-0.5*(d2**2)) # Risk Neutral density in moneyness space

    strike_space = F*np.exp(x_grid)
    q_k = q/strike_space # Risk Neutral density in strike space
    
    return q_k, strike_space

def calc_lognormal_density(params, xs, F):
    x_grid = make_x_grid(xs)
    
    a, b, rho, m, sigma = params
    
    w_atm = a + b*(rho*(-m) + np.sqrt((m)**2 + sigma**2))
    
    d2 = (-x_grid / np.sqrt(w_atm)) - 0.5*np.sqrt(w_atm)

    q = (1/np.sqrt(2*math.pi*w_atm)) * np.exp(-0.5*d2**2) # Risk Neutral density in moneyness space
    
    strike_space = F * np.exp(x_grid)
    q_k = q/strike_space # Risk Neutral density in strike space
    
    return q_k, strike_space

def fit_svi_sequential_vanilla_slsqp(xs_by_tenor, ys_by_tenor, tenors):
    # Single Start SLSQP
    params_by_tenor = []
    rmse_by_tenor = []
    
    # Cost Function
    f_svi = lambda params, x, y: sum((params[0] + params[1]*(params[2]*(x - params[3]) + \
                                                  np.sqrt((x - params[3])**2 + params[4]**2)) - y)**2)
    bounds = bounder()

    
                        
    for i in range(len(tenors)):
        xs = xs_by_tenor[i]
        ys = ys_by_tenor[i]
        t = tenors[i]
        w_mkt = (ys**2)*t


        # Initial parameter values
        a0 = np.mean(w_mkt)
        m0 = 1e-4
        rho0 = -0.5
        w_max = np.max(w_mkt)
        w_min = np.min(w_mkt)
        x_max = np.max(xs)
        x_min = np.min(xs)
        b0 = (w_max - w_min)/abs(x_max - x_min)
        sigma0 = 0.1
        params0 = np.array([a0, b0, rho0, m0, sigma0])
            
        if i == 0:
            ineq_cons = {
                'type': 'ineq', 'fun': lambda params: svi_constraints(params, xs, None,  False)
            }
            print("Doing SLSQP for tenor {0}".format(t))
            
            res = minimize(f_svi, params0, args = (xs, w_mkt), method='SLSQP', 
           constraints=[ineq_cons], options={'ftol': 1e-9, 'disp': True},
           bounds=bounds)
            
        else:
            params_prev = params_by_tenor[i-1]
            t_prev = tenors[i-1]
            
            ineq_cons = {
                    'type': 'ineq', 'fun': lambda params: svi_constraints(params, xs, params_prev,  True)
                }
            
            print("Doing SLSQP for tenor {0}".format(t))
            
            res = minimize(f_svi, params0, args = (xs, w_mkt), method='SLSQP', 
           constraints=[ineq_cons], options={'ftol': 1e-9, 'disp': True},
           bounds=bounds)

        if res.success:
            params_best = res.x
            fit_check = fit_quality(res, xs)
    
            if i==0:
                 calendar_check = True
                
            else:
                _, _, calendar_check = calendar_arb_check(params_best, params_prev, xs, t, t_prev)
            
            if fit_check and calendar_check:
                rmse = math.sqrt(f_svi(params_best, xs, w_mkt)/len(xs))
                params_by_tenor.append(params_best)
                rmse_by_tenor.append(rmse)
                    
            else:
                # Just to debug
                if not calendar_check:
                    print("Calendar Violation")
                if not fit_check:
                    print("Fit Violation")
                raise RuntimeError(
                    "Calendar SVI calibration did not produce the correct surface for tenor {0}".format(t)
                )
            
        else:
            print("Calendar SVI calibration failed for tenor {0}".format(t))
            continue

    return params_by_tenor, rmse_by_tenor

def fit_svi_sequential_vanilla_slsqp_multistart(xs_by_tenor, ys_by_tenor, tenors, max_checks = 20, max_iters = 150):
    # Multi-start SLSQP
    params_by_tenor = []
    rmse_by_tenor = []
    
    # Cost Function
    f_svi = lambda params, x, y: sum((params[0] + params[1]*(params[2]*(x - params[3]) + \
                                                  np.sqrt((x - params[3])**2 + params[4]**2)) - y)**2)
    bounds = bounder()

    for i in range(len(tenors)):
        xs = xs_by_tenor[i]
        ys = ys_by_tenor[i]
        t = tenors[i]
        print("Tenor : ", t)
        w_mkt = (ys**2)*t
        sample_init = initializer(xs, w_mkt)

        n_valids = 0 # Number of valid iterations
        n_iters = 0 # Number of iterations
        rmse_min = math.inf
        params_best = None
        
        for params0 in sample_init:
            
            if i == 0:
                ineq_cons = {
                    'type': 'ineq', 'fun': lambda params: svi_constraints(params, xs, None,  False)
                }
                
                res = minimize(f_svi, params0, args = (xs, w_mkt), method='SLSQP', 
               constraints=[ineq_cons], options={'ftol': 1e-9, 'disp': False},
               bounds=bounds)
                
            else:
                params_prev = params_by_tenor[i-1]
                t_prev = tenors[i-1]
                
                ineq_cons = {
                        'type': 'ineq', 'fun': lambda params: svi_constraints(params, xs, params_prev,  True)
                    }
                
                print("Doing SLSQP for tenor {0}".format(t))
                
                res = minimize(f_svi, params0, args = (xs, w_mkt), method='SLSQP', 
               constraints=[ineq_cons], options={'ftol': 1e-9, 'disp': False},
               bounds=bounds)
    
            if res.success:
                params = res.x
                fit_check = fit_quality(res, xs)
        
                if i==0:
                     calendar_check = True
                    
                else:
                    _, _, calendar_check = calendar_arb_check(params, params_prev, xs, t, t_prev)
                
                if fit_check and calendar_check:
                    n_valids += 1
                    print("Starting Point # : {0}".format(n_valids))
                    rmse = math.sqrt(f_svi(params, xs, w_mkt)/len(xs))
                    print(params)
                    if rmse < rmse_min:
                        rmse_min = rmse
                        params_best = params
                        
            n_iters += 1

            if n_valids >= max_checks or n_iters >= max_iters:
                break

        if params_best is not None:
            params_by_tenor.append(params_best)
            rmse_by_tenor.append(rmse_min)
        else:
            raise RuntimeError("SVI did not converge for tenor {0}".format(t))


    return params_by_tenor, rmse_by_tenor
        
def svi(xs_by_tenor, ys_by_tenor, tenors, mode, F, max_checks = 20, max_iters = 150):
    
    if mode == 'single-start':
        params_by_tenor, rmse_by_tenor = fit_svi_sequential_vanilla_slsqp(xs_by_tenor, ys_by_tenor, tenors)
    else:
        params_by_tenor, rmse_by_tenor = fit_svi_sequential_vanilla_slsqp_multistart(xs_by_tenor, ys_by_tenor, tenors)

    q_svi_by_tenor = []
    q_ln_by_tenor = []
    strike_space_by_tenor = []
    
    for i in range(len(tenors)):
        xs = xs_by_tenor[i]
        params = params_by_tenor[i]
        q_svi, strike_space = calc_svi_density(params, xs, F) # SVI-Implied Risk Neutral Density
        q_ln, _ = calc_lognormal_density(params, xs, F) # Lognormal Density
        q_svi_by_tenor.append(q_svi)
        q_ln_by_tenor.append(q_ln)
        strike_space_by_tenor.append(strike_space)

    return params_by_tenor, rmse_by_tenor, q_svi_by_tenor, q_ln_by_tenor, strike_space_by_tenor
    
        
