# Publishing Checklist

## Before publishing

- [ ] Rename the GitHub repository to `tracediligence` or `source-grounded-diligence`.
- [x] Add 3 Demo-mode screenshots to the README.
- [ ] Run `pytest` and preserve the passing output.
- [ ] Confirm `.streamlit/secrets.toml` is not committed.
- [ ] Use only fictional, public, or explicitly authorized source material.
- [ ] Complete at least one real public-company test.
- [ ] Manually check at least 20 claim-citation pairs.
- [ ] Update resume metrics only after the benchmark is complete.

## GitHub commands

```bash
git init
git add .
git commit -m "Build source-grounded diligence workflow"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Streamlit deployment

- [ ] Sign in to Streamlit Community Cloud with GitHub.
- [ ] Create an app from the repository.
- [ ] Select `app.py` as the entrypoint.
- [ ] Start with `ENABLE_LIVE_MODE = false` under Advanced settings → Secrets.
- [ ] If enabling live mode, also add `OPENAI_API_KEY` and a private `APP_ACCESS_CODE`.
- [ ] Deploy and test Demo mode first.
- [ ] Test Live mode on a public company.
- [ ] Add the live URL to the README and LinkedIn Featured section.

## Suggested portfolio assets

- [ ] 60-90 second screen recording
- [ ] Architecture diagram
- [ ] Screenshot of executive brief
- [ ] Screenshot of evidence ledger with a weak claim flagged
- [ ] One-page case study describing the problem, architecture, validation controls, and benchmark
