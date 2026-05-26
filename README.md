# Volatility Surface Dashboard

Interactive SPX/SPY implied volatility surface dashboard built with Streamlit and Plotly.

## Run locally

```bash
streamlit run app.py
```

The app can either:

- upload an `OptionData.xlsx` file, or
- fetch latest available SPX/SPY option chains with `yfinance` and Treasury rates from FRED.

## FRED API key

For local use, you can enter the key in the sidebar.

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
