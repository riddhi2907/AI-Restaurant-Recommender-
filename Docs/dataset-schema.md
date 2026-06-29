# Dataset Schema: Zomato Restaurant Recommendation

> Source: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)  
> Explored during Phase 1 implementation.

## Overview

| Attribute | Value |
|-----------|-------|
| **Rows** | ~51,717 |
| **Split** | `train` |
| **Primary city** | Bangalore (dataset is Bangalore-focused) |
| **Format** | CSV via Hugging Face `datasets` |

## Raw Columns (17)

| Column | Type | Mapped To | Notes |
|--------|------|-----------|-------|
| `url` | string | — | Not used in v1 |
| `address` | string | `address` | Full street address; used for stable ID |
| `name` | string | `name` | Required; rows without name are dropped |
| `online_order` | string | — | Yes/No |
| `book_table` | string | — | Yes/No |
| `rate` | string | `rating` | Formats: `4.1/5`, `NEW`, `-`, null |
| `votes` | int | `votes` | Review vote count |
| `phone` | string | — | Not used in v1 |
| `location` | string | `location` | Locality (e.g. Banashankari, Koramangala) |
| `rest_type` | string | `rest_type` | e.g. Casual Dining, Cafe |
| `dish_liked` | string | — | Not used in v1 |
| `cuisines` | string | `cuisine` | Comma-separated (e.g. `North Indian, Chinese`) |
| `approx_cost(for two people)` | string | `cost` | Numeric strings, may include commas (`1,200`) |
| `reviews_list` | string | — | Not used in v1 |
| `menu_item` | string | — | Not used in v1 |
| `listed_in(type)` | string | — | e.g. Buffet, Cafes |
| `listed_in(city)` | string | locality fallback | Area zone / locality (e.g. Banashankari); not the city name |

## Normalization Decisions (Phase 1)

| Decision | Resolution |
|----------|------------|
| **Location granularity** | `location` = locality (Indiranagar, Bellandur, etc.). `city` = Bangalore/Delhi from address. City names are never stored in `location`. |
| **Missing ratings** | Default to `0.0` (`NEW`, `-`, null treated as unrated). |
| **Missing cost** | `cost=None`, `budget_tier=None`; row still included. |
| **Missing cuisine** | Set to `"Unknown"`. |
| **Budget tiers** | low ≤ ₹500, medium ₹501–1500, high > ₹1500 (configurable via env). |
| **Stable ID** | SHA-256 hash (12 chars) of `name|location|address`. |

## Sample Raw Record

```
name:     Spice Elephant
location: Banashankari
rate:     4.1/5
cuisines: Chinese, North Indian, Thai
cost:     800
address:  2nd Floor, 80 Feet Road, ..., Banashankari, Bangalore
```

## Normalized Output

```python
Restaurant(
    id="a1b2c3d4e5f6",
    name="Spice Elephant",
    location="Banashankari",
    city="Bangalore",
    cuisine="Chinese, North Indian, Thai",
    cost=800.0,
    rating=4.1,
    budget_tier="medium",
)
```
