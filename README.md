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
