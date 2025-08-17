# apartment-copilot
Web app to aid in your apartment search. Load in 5-10 urls for apartments you are interested across a number of sites (Zillow, aprtments.com, aprtmentzilla etc). Also add your preferences, budget, and work location and the copilot will do the rest! Providing you with an analysis and ranking list.
# Apartment Copilot (monorepo)
- `web/` — Next.js frontend
- `api/` — FastAPI backend

## Local Dev
API:  (from `api/`) `uvicorn main:app --reload --port 8000`
Web:  (from `web/`) `npm run dev` (or `pnpm dev`, `yarn dev`)

## Env
Copy `.env.example` → put values in `api/.env` and `web/.env.local`.