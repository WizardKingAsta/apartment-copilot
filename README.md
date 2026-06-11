# Apartment Copilot

Web app to aid in your apartment search. Load in 5-10 urls for apartments you are interested across a number of sites (Zillow, Apartment List, Rent.com). Also add your preferences, budget, and requirements and the copilot will do the rest! Providing you with an analysis and ranking list.

---

## Demo

GitHub Repo: (https://github.com/WizardKingAsta/apartment-copilot)  
Video Demo: [Link here, optional]

---

## Overview

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

The frontend is built with React, I chose React because it provides a versatile and reactive UI. This takes in all the user info, and communicates with the FastAPI backend. The backend handles storing submitted links, parsing the apartment websites, cleaning the data, storing user preferences, and interacting with the ClaudeAPI to enable AI scoring. The SQLLITE DB stores the user links submissions to and statuses to persist across sessions. The application is currently run locally. 

---
## Local Development

This project depends on external API credentials that are not included in the repository:

- DiffBot Token
- Claude API Key

Because these credentials are private, the full application cannot be run locally without creating your own API keys.

To run the project locally, create a `.env` file with the following variables:


DiffBot =your_diffBot_token
CLAUDE_API_KEY=your_claude_api_key
```text

