# TOM-CO-TCG-BOT

**`main`** — ancrage minimal (statique + backend Python). **`interface`** — **TCG Scalper Pro** ([code](https://github.com/AnthonyNadjari/TOM-CO-TCG-BOT/tree/interface), [prod](https://tom-co-tcg-bot.vercel.app)).

Prod : push sur **`interface`** → [workflow Vercel](https://github.com/AnthonyNadjari/TOM-CO-TCG-BOT/blob/interface/.github/workflows/vercel-deploy-interface.yml). Les builds Git déclenchés par **`main`** sont ignorés côté Vercel (Ignored Build Step).

---

## Backend Python (`main`)

`pyproject.toml` — `pip install -e ".[dev]"` puis `pytest`.

```
orchestrator/  bots/  scrapers/  sites/  execution/  accounts/
payment/  infra/  security/  config/  utils/  tests/
```
