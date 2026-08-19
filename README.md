# Volatility Surface Dashboard

Interactive SPX/SPY implied volatility surface dashboard built with Streamlit and Plotly.

## Run locally

```bash
streamlit run app.py
```

The app can either:

- upload an `OptionData.xlsx` file, or
- fetch latest available SPX/SPY option chains with `yfinance` and Treasury rates from FRED.

## Project documentation

A detailed explanation of the data pipeline, modeling assumptions, option-chain cleaning, repo bootstrapping, IV inversion, and dashboard outputs is available here:

[Project Documentation](docs/IV_Project_Final_Document.md)

A PDF copy is also available for download:

[PDF Documentation](docs/IV_Project_Final_Document.pdf)

## Sample SVI RMSE comparison

In one latest-data SPX run, multi-start SVI reduced total-variance RMSE versus single-start SLSQP on most fitted tenors:

| Tenor | Single-start RMSE | Multi-start RMSE | Improvement |
| ---: | ---: | ---: | ---: |
| 0.0384 | 0.000150 | 0.000043 | 71.5% |
| 0.0822 | 0.000031 | 0.000031 | 2.2% |
| 0.1589 | 0.000059 | 0.000054 | 8.0% |
| 0.2548 | 0.000089 | 0.000024 | 72.5% |
| 0.5041 | 0.000049 | 0.000021 | 57.5% |
| 1.0027 | 0.000072 | 0.000025 | 64.9% |

Average SPX improvement was approximately 46%. SPY could not be compared in this run because the available yfinance SPY option chains did not pass the quote-quality filters.

## Credits and references

- Finite Difference Methods (Explicit, Implicit and Crank-Nicolson): [https://quintus-zhang.github.io/post/on_pricing_options_with_finite_difference_methods/?utm_source=chatgpt.com](https://quintus-zhang.github.io/post/on_pricing_options_with_finite_difference_methods/?utm_source=chatgpt.com)
- IV and Vol Surfaces: [https://www.youtube.com/watch?v=F_qh827iXFQ](https://www.youtube.com/watch?v=F_qh827iXFQ)
- SVI: [https://sellersgaard.github.io/blog/2023/svi/](https://sellersgaard.github.io/blog/2023/svi/)
- SciPy documentation for SLSQP: [https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)

## FRED API key

For local use, add the key to `.streamlit/secrets.toml`.

For deployment, add this secret in Streamlit Community Cloud:

```toml
FRED_API_KEY = "your_key_here"
```

Do not commit `.streamlit/secrets.toml` to GitHub.

## Free hosting

Use Streamlit Community Cloud:

1. Push this folder to a GitHub repository.
2. Go to Streamlit Community Cloud.
3. Create an app from the repository.
4. Select `app.py` as the entrypoint.
5. Add `FRED_API_KEY` in app secrets.

The free deployment gives you a public `streamlit.app` URL that you can add to a resume or portfolio.
