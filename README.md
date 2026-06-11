# Apartment Copilot

Web app to aid in your apartment search. Load in 5-10 urls for apartments you are interested across a number of sites (Zillow, Apartment List, Rent.com). Also add your preferences, budget, and requirements and the copilot will do the rest! Providing you with an analysis and ranking list.

---

## Demo

GitHub Repo: (https://github.com/WizardKingAsta/apartment-copilot) 
Video Demo: [Link here, optional]

### Screenshots

![Screenshot description](./path-to-screenshot.png)

---

## Overview

[Write 2–4 sentences explaining the project.]

This project was built to solve the headache that comes with comparing endless apartment listings. 
Users can upload links of apartments they like, fill in numerical apartment preferences, verbally describe their dream apartment, and analyze all their options.  
I built this project to help cut through the noisey apartment searching market and help improve my full stack development skills.

---

## Features

- Site catches duplicate link submissions and notifies the user.
- Parses the websites and scrapes data to give the user reccomendations down to the specific unit number.
- Can process verbal or written preferences and work them into the user's custom ranking using LLM scoring.
- Allows the user to quickly adjust numerical preferences, beds, baths, minimum size etc. very quickly on the dashboard.
- Stores the apartments and links in a sql database to persist across sessions.
- Returns a result of top 5 choices for the user with a number score 1-100 and a written sentence explaining why it fits.

---

## Tech Stack

**Frontend:** React, Next.js, HTML/CSS,
**Backend:** Node.js, FastAPI
**Database:** SQLITE  

---

## Architecture

[Briefly explain how the app is structured.]

Example:
The frontend is built with [frontend framework] and communicates with a [backend framework] API. The backend handles [auth/business logic/data processing], while [database] stores [main types of data]. The application is deployed using [deployment platform].

---
# Apartment Copilot (monorepo)
- `web/` — Next.js frontend
- `api/` — FastAPI backend

## Local Dev
API:  (from `api/`) `uvicorn main:app --reload --port 8000`
Web:  (from `web/`) `npm run dev` (or `pnpm dev`, `yarn dev`)

## Env
Copy `.env.example` → put values in `api/.env` and `web/.env.local`.

## API
returns up the top 5 data or {error: no results}

Returns up data in the form: 
```text

