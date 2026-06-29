# Project Context: AI-Powered Restaurant Recommendation System (Zomato Use Case)

## Overview

This project is an **AI-powered restaurant recommendation service** inspired by Zomato. The system intelligently suggests restaurants based on user preferences by combining **structured restaurant data** with a **Large Language Model (LLM)** to produce personalized, human-like recommendations.

---

## Objective

Design and implement an application that:

1. **Takes user preferences** — location, budget, cuisine, ratings, and other inputs
2. **Uses a real-world dataset** — Zomato restaurant data from Hugging Face
3. **Leverages an LLM** — to generate personalized, human-like recommendations
4. **Displays clear, useful results** — actionable output for the end user

---

## Data Source

| Attribute | Value |
|-----------|-------|
| **Dataset** | Zomato Restaurant Recommendation |
| **Provider** | Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |

### Relevant Fields to Extract

- Restaurant name
- Location
- Cuisine
- Cost
- Rating
- (Additional fields as available in the dataset)

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract relevant fields: restaurant name, location, cuisine, cost, rating, etc.
- Prepare data for filtering and LLM consumption

### 2. User Input

Collect user preferences:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | Low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional preferences** | Family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM **reason** and **rank** options

### 4. Recommendation Engine

Use the LLM to:

- **Rank** restaurants by fit to user preferences
- **Explain** why each recommendation fits the user
- **Optionally summarize** the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format:

| Field | Description |
|-------|-------------|
| **Restaurant Name** | Name of the recommended restaurant |
| **Cuisine** | Type of cuisine offered |
| **Rating** | Restaurant rating |
| **Estimated Cost** | Approximate cost for the user |
| **AI-generated explanation** | Why this restaurant was recommended |

---

## Architecture Summary

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Hugging Face   │────▶│  Data Ingestion  │────▶│  Filtered Data  │
│  Zomato Dataset │     │  & Preprocessing │     │  (Structured)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐               │
│  User Input     │────▶│  Integration     │◀──────────────┘
│  (Preferences)  │     │  Layer + Prompt  │
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  LLM             │
                        │  Recommendation  │
                        │  Engine          │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Output Display  │
                        │  (Top picks +    │
                        │   explanations)  │
                        └──────────────────┘
```

---

## Key Requirements Checklist

- [ ] Load Zomato dataset from Hugging Face
- [ ] Preprocess and extract relevant restaurant fields
- [ ] Build user preference input (location, budget, cuisine, rating, extras)
- [ ] Implement filtering logic based on user preferences
- [ ] Design LLM prompt for ranking and reasoning
- [ ] Integrate LLM for recommendations and explanations
- [ ] Display results: name, cuisine, rating, cost, AI explanation

---

## Success Criteria

A successful implementation will:

1. Accept natural user preferences and map them to dataset filters
2. Return a ranked list of restaurants that match those preferences
3. Provide clear, personalized explanations for each recommendation via the LLM
4. Present results in a readable, user-friendly format

---

## Source Document

This context is derived from: `Docs/ProblemStatement`
