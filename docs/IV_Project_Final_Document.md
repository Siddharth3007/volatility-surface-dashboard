# SPX/SPY Implied Volatility Surface Dashboard

## 1. Project Objective

The objective of this project is to construct, plot, and visualize the SPX/SPY implied volatility surface using live option-chain data, Treasury rates, dividend assumptions, repo bootstrapping, implied volatility inversion, quadratic smile fitting, and SVI fitting.

## 2. Inputs and Data Sources

| Input | Purpose |
| --- | --- |
| Yahoo Finance | Option chains, spot prices, and SPY dividends |
| FRED | Treasury rates |
| Optional Excel Upload Mode | Allows the user to upload their own inputs instead of using live market data fetching |
| SPX vs SPY | Uses different modeling assumptions: European options for SPX and American options for SPY |

## 3. Modeling Assumptions

- SPX options are treated as European.
- SPY options are treated as American.
- SPX dividend yield is proxied using SPY's trailing four-quarter cash dividend yield.
- SPY dividends are modeled as discrete cash dividends.
- The risk-free curve is interpolated linearly.
- OTM options are used for visualization.
- A quadratic smile or SVI smile is fit tenor-by-tenor.

## 4. Implementation Walkthrough

### Step 1: Build Rate Curve

We pull daily constant maturity rates from FRED for maturities such as 1 month, 3 months, 6 months, 1 year, 2 years, and 5 years. These are theoretical yields of U.S. Treasury securities constructed daily by the Federal Reserve. For intermediate maturities, we perform linear interpolation to find the corresponding rates. This gives us the risk-free rate used in the exercise.

### Step 2: Pull and Clean Option Chain Data

We pull option chain data for multiple expiries from Yahoo Finance.

#### 2.a Expiry Selection

We select expiries closest to `[14D, 30D, 60D, 90D, 180D, 365D]`. This is done because Yahoo Finance can have many expiries, and we do not want the dashboard to look too dense. Also, many short-dated options are noisy, and IV inversion can become slow and expensive. The selected expiries give a cleaner term structure from short term to medium term to long term.

#### 2.b Strike Sampling

First, we select strikes that have quotes for both calls and puts. Then we select strikes in the range:

```text
0.8 * spot <= K <= 1.25 * spot
```

Finally, we keep strikes closest to target log-moneyness levels such as:

```text
[-0.08, -0.06, -0.04, ..., 0.10, 0.12]
```

This sampling keeps the full surface readable and avoids reading the whole chain.

#### 2.c Compute Mid Price and Spreads

We compute the mid price, spread, and relative spread, where relative spread is spread divided by mid price.

#### 2.d Bid/Ask Cleaning

We filter out options with wide spreads (`relative spread > 30%`), crossed or invalid quotes (`ask <= bid`), zero volume and open interest, very low mid price (`< 0.1`), or zero bids/asks.

#### 2.e Fallback Price Logic

Only if bid or ask is missing or NaN, we use the fallback price, provided that the fallback price is positive.

#### 2.f Pair Selection

For a given strike, we require both the call and put mid prices to pass the filter before using them as a pair. If either side fails the filter, the strike is dropped completely from the quote dictionary.

#### 2.g American Intrinsic Value Check

For American options like SPY, we reject prices below intrinsic value:

```python
intrinsic = max(S_eff - K, 0) for calls
intrinsic = max(K - S_eff, 0) for puts

if price < intrinsic:
    continue
```

#### 2.h IV Sanity Filter

After IV inversion, we drop IVs that are at/below 1% or above 200%. This removes bad results due to failed IV inversion by the numerical solver or other absurd outputs.

#### 2.i OTM Filtering

We compute the forward per tenor and mark options as OTM:

```text
Call is OTM if K >= F
Put is OTM if K <= F
```

The plots use OTM options only, so ITM quotes do not drive the smile/surface visualization.

### Step 3: Calculate Dividends and Dividend Yields

For SPY, this is straightforward with yfinance because SPY has actual cash dividend history. We use the most recent four quarterly dividends as a forward estimate of dividend payments.

For SPX, we use SPY's trailing four-quarter cash dividend yield as a proxy for SPX's continuous dividend yield.

### Step 4: Fit Repo Rate

For repo bootstrapping, we initialize the curve using a dividend/carry prior. For SPX, this prior is the SPY trailing four-quarter dividend yield proxy. For SPY, the same trailing four-quarter SPY dividend yield is used as the carry prior, while SPY cash dividends are still modeled separately as discrete payments.

For each tenor, we estimate a theoretical forward using the previously fitted repo rate. We choose the strike price closest to this theoretical forward because ATM options generally have the most liquidity and the least amount of microstructure noise. That is why IV estimates are usually best around this strike.

For European options, we use put-call parity to find the market-implied forward price:

```text
C - P = exp(-rT) * (F - K)
```

The repo rate can then be estimated from this market-implied forward.

For American options, put-call parity does not hold directly. However, around the ATM strike, call and put implied volatilities should be close when the carry assumption is correct. Therefore, for the ATM strike closest to the theoretical forward, we try different repo values and choose the one where call IV and put IV are closest.

If repo bootstrapping fails for a tenor, the model falls back to the dividend/carry prior. If live dividend data is unavailable, the model falls back to hardcoded dividend assumptions.

### Step 5: Calculate Forward Prices

We calculate forward prices for different tenors using the fitted repo rate.

### Step 6: IV Inversion

We calculate implied volatility for different maturities and log-moneyness levels, where `x = log(K/F)`.

For European options, we use the Newton-Raphson method to find the root of `BS(sigma) - price = 0`. In the Newton-Raphson update, the denominator is vega, which has a closed-form expression under Black-Scholes. If Newton-Raphson is unstable, we use bisection as a fallback.

For American options, we use bisection to find the root of `pricer(sigma) - price = 0`. The pricer solves the Black-Scholes PDE with an early exercise premium. To solve the PDE, we use a Crank-Nicolson finite difference method. To account for early exercise, we use the Brennan-Schwartz approximation during backward substitution, updating values as:

```text
V = max(payoff, continuation value)
```

### Step 7: Fit the Volatility Smile

The dashboard supports three fitting modes.

#### Quadratic Fit

We fit a quadratic polynomial to model IV versus log-moneyness and obtain coefficients `a`, `b`, and `c`:

```text
IV(x) = a + b*x + c*x^2, where x = log(K/F)
```

- `a` = ATM IV level
- `b` = skew
- `c` = curvature

#### SVI Single Start

SVI single start fits Gatheral's raw SVI parameterization to observed IVs in total variance space. It uses one informed warm start for SLSQP.

```text
w(x) = a + b * [rho * (x - m) + sqrt((x - m)^2 + sigma^2)]
```

Here `w(x)` is total implied variance and `x = log(K/F)`.

#### SVI Multi-Start

SVI multi-start fits Gatheral's raw SVI parameterization using multiple warm starts in different regions of the parameter space. Among feasible fits, the dashboard chooses the one with the lowest RMSE. In testing, the multi-start version generally reduced RMSE by around 50-60% compared with the single-start SLSQP version.

The SVI modes also include no-arbitrage style checks such as positive total variance, calendar constraints across tenors, and risk-neutral-density based validation.

### Step 8: Visualization and Dashboard Output

Finally, we display the fitted repo curve, implied volatility table, surface coefficients, volatility smiles across tenors, and the 3D implied volatility surface. The plotted smiles and surfaces use OTM options only, so the visualization focuses on the most liquid and commonly quoted side of the volatility surface.

When an SVI mode is selected, the dashboard also displays SVI-implied risk-neutral density plots, including a multi-tenor overlay and a front-month comparison against a lognormal density.

## 5. Dashboard Features

- Fetch latest market data
- Upload Excel file
- View SPX/SPY surfaces
- View smiles across tenors
- View front-month smile
- View SVI-implied risk-neutral densities
- Download IV data
- Inspect repo curve, IV table, and coefficients

## 6. Interpretation Guide

- `a` = ATM volatility level
- `b` = skew
- `c` = curvature for the quadratic fit
- For SVI, `a`, `b`, `rho`, `m`, and `sigma` define the raw SVI total variance curve
- Higher left-wing IV means downside protection is more expensive
- Repo curve instability can signal noisy short-tenor data
- Spikes can come from short-dated OTM put skew

## 7. Sample SVI RMSE Comparison

In one latest-data run, multi-start SVI reduced total-variance RMSE versus single-start SLSQP for both SPX and SPY.

SPX:

| Tenor | Single-start RMSE | Multi-start RMSE | Improvement |
| ---: | ---: | ---: | ---: |
| 0.0822 | 0.00004211 | 0.00002469 | 41.4% |
| 0.1589 | 0.00004768 | 0.00004331 | 9.2% |
| 0.2548 | 0.00007725 | 0.00003152 | 59.2% |
| 0.5041 | 0.00010883 | 0.00002108 | 80.6% |
| 1.0027 | 0.00006738 | 0.00002013 | 70.1% |

Average SPX improvement was approximately 52.1%.

SPY:

| Tenor | Single-start RMSE | Multi-start RMSE | Improvement |
| ---: | ---: | ---: | ---: |
| 0.0438 | 0.00026225 | 0.00003122 | 88.1% |
| 0.0822 | 0.00003889 | 0.00001367 | 64.8% |
| 0.1589 | 0.00004826 | 0.00004040 | 16.3% |
| 0.2548 | 0.00002884 | 0.00000706 | 75.5% |
| 0.4466 | 0.00006977 | 0.00002384 | 65.8% |
| 1.0795 | 0.00025084 | 0.00012184 | 51.4% |

Average SPY improvement was approximately 60.3%.

## 8. Limitations

- Yahoo Finance data may be delayed or stale
- Bid/ask quality varies
- The quadratic fit is simple and not arbitrage-free
- SVI improves the fitting framework, but the dashboard is still not a production-grade volatility surface engine
- Repo bootstrapping can be unstable for short tenors
- This is not intended for trading or risk decisions

## 9. Future Improvements

- More robust static arbitrage checks
- Calendar/butterfly violation flags
- Better dividend curve
- More robust quote cleaning
- Fit-quality metrics and residual plots
- Historical surface snapshots

## 10. Deployment

- Built with Streamlit
- Hosted on Streamlit Cloud
- Uses free data sources
- Public dashboard link / GitHub repository

## 11. Credits and References

- Finite Difference Methods (Explicit, Implicit and Crank-Nicolson): [https://quintus-zhang.github.io/post/on_pricing_options_with_finite_difference_methods/?utm_source=chatgpt.com](https://quintus-zhang.github.io/post/on_pricing_options_with_finite_difference_methods/?utm_source=chatgpt.com)
- IV and Vol Surfaces: [https://www.youtube.com/watch?v=F_qh827iXFQ](https://www.youtube.com/watch?v=F_qh827iXFQ)
- SVI: [https://sellersgaard.github.io/blog/2023/svi/](https://sellersgaard.github.io/blog/2023/svi/)
- SciPy documentation for SLSQP: [https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)
