# Folder 04 — Pattern Mining (Apriori and FP-Growth)

**Responsibility of this folder:** find conditions that often appear together with winning, as "IF … THEN …" rules.
**Real project:** `04_pattern_mining/apriori_analysis.py`, `fp_growth_analysis.py` and the dashboard page *Pattern Mining*.

---

## File: `apriori_vs_fpgrowth.py`

**1. Location:** `exam_simplified/04_pattern_mining/apriori_vs_fpgrowth.py`

**2. What it does:** turns every driver-race into a basket of items, finds frequent itemsets with **both** Apriori and FP-Growth, checks they agree, and builds association rules.

**3. Parameters and logic**
| Parameter | Value | Meaning |
|---|---|---|
| Transactions | 12,358 | one basket per driver-race |
| Items | 24 | grid band, team, driver form, team form, circuit history, teammate battle, outcomes |
| `min_support` | 0.02 | an itemset must appear in ≥ 2% of baskets |
| `min_confidence` | 0.25 | a rule must be right ≥ 25% of the time |
| Result | 414 itemsets, 1,393 rules | identical from both algorithms |

Formulas:
- support(X ⇒ Y) = P(X and Y together)
- confidence(X ⇒ Y) = support(X ∪ Y) / support(X)
- lift(X ⇒ Y) = confidence / support(Y); above 1 means "more likely than normal"

**4. Simplified code**
```python
# ============================================================
# FILE: 04_pattern_mining/apriori_vs_fpgrowth.py
# REAL MODULES: 04_pattern_mining/apriori_analysis.py and fp_growth_analysis.py
# WHAT IT DOES:
#   1. turns every driver-race into a "shopping basket" of items (like Grid_Pole_P1, Outcome_Winner)
#   2. finds item groups that appear together often (frequent itemsets) with Apriori AND FP-Growth
#   3. makes rules "IF X THEN Y" and ranks them by lift
# Parameters: min_support = 0.02, min_confidence = 0.25
# ============================================================

import os
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules

MIN_SUPPORT = 0.02      # an itemset must appear in at least 2% of all baskets
MIN_CONFIDENCE = 0.25   # a rule must be right at least 25% of the time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
data = pd.read_csv(DATA, low_memory=False)


def make_basket(row):
    """Turns one driver-race into a list of items (same buckets as the real project)."""
    items = []
    # Starting grid
    if row["grid_position"] == 1:
        items.append("Grid_Pole_P1")
    elif row["grid_position"] == 2:
        items.append("Grid_FrontRow_P2")
    elif row["grid_position"] <= 4:
        items.append("Grid_Top4")
    elif row["grid_position"] <= 10:
        items.append("Grid_Top10")
    else:
        items.append("Grid_Backmarker")
    # Team
    team = str(row["constructor_name"]).lower()
    if "ferrari" in team:
        items.append("Team_Ferrari")
    elif "mclaren" in team:
        items.append("Team_McLaren")
    elif "williams" in team:
        items.append("Team_Williams")
    elif "red bull" in team:
        items.append("Team_RedBull")
    elif "mercedes" in team:
        items.append("Team_Mercedes")
    else:
        items.append("Team_Midfield_Customer")
    # Driver form (average finish over the last 5 races)
    if row["driver_rolling_finish_5"] <= 3:
        items.append("Driver_Form_Elite_P1_P3")
    elif row["driver_rolling_finish_5"] <= 6:
        items.append("Driver_Form_Front_P4_P6")
    elif row["driver_rolling_finish_5"] <= 10:
        items.append("Driver_Form_Points_P7_P10")
    else:
        items.append("Driver_Form_Midfield")
    # Team form (average finish over the team's last 10 entries)
    if row["constructor_rolling_finish_10"] <= 4:
        items.append("Team_Form_Elite_Top4")
    elif row["constructor_rolling_finish_10"] <= 8:
        items.append("Team_Form_Competitive")
    # Circuit history and teammate battle
    if row["circuit_experience"] >= 5:
        items.append("Circuit_Veteran_5Plus")
    if row["circuit_win_rate"] > 0.20:
        items.append("Circuit_Prior_Multi_Winner")
    if row["ahead_of_teammate_grid"] == 1:
        items.append("Beat_Teammate_In_Quali")
    # What actually happened
    if row["target_is_win"] == 1:
        items.append("Outcome_Winner")
    if row["target_is_podium"] == 1:
        items.append("Outcome_Podium")
    if row["target_is_points"] == 1:
        items.append("Outcome_Points")
    if row["target_is_dnf"] == 1:
        items.append("Outcome_DNF")
    return items


baskets = [make_basket(row) for _, row in data.iterrows()]
print("Baskets (transactions):", len(baskets))                    # 12,358

# Make a True/False table: one column per item, one row per basket
encoder = TransactionEncoder()
table = pd.DataFrame(encoder.fit(baskets).transform(baskets), columns=encoder.columns_)
print("Different items:", len(table.columns))                     # 24

# Run both algorithms with the same minimum support
itemsets_apriori = apriori(table, min_support=MIN_SUPPORT, use_colnames=True)
itemsets_fpgrowth = fpgrowth(table, min_support=MIN_SUPPORT, use_colnames=True)
print("Frequent itemsets - Apriori:", len(itemsets_apriori), " FP-Growth:", len(itemsets_fpgrowth))   # 414 and 414

# Both must find exactly the same itemsets
same = set(itemsets_apriori["itemsets"]) == set(itemsets_fpgrowth["itemsets"])
print("Same itemsets from both algorithms:", same)
assert same

# Rules "IF antecedent THEN consequent"
rules = association_rules(itemsets_fpgrowth, metric="confidence", min_threshold=MIN_CONFIDENCE)
print("Association rules:", len(rules))                            # 1,393

# Show the strongest rules that end in a win
win_rules = rules[rules["consequents"].apply(lambda c: "Outcome_Winner" in c)].sort_values("lift", ascending=False)
for _, rule in win_rules.head(5).iterrows():
    print(f"IF {set(rule['antecedents'])} THEN {set(rule['consequents'])}"
          f"   support={rule['support']:.3f} confidence={rule['confidence']:.2f} lift={rule['lift']:.1f}")
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `def make_basket(row)` | Turns one row into items, using simple if/elif buckets |
| `if row["grid_position"] == 1: items.append("Grid_Pole_P1")` | Grid bucket: pole, front row, top 4, top 10 or back |
| `if row["target_is_win"] == 1: items.append("Outcome_Winner")` | The outcome is an item too, so rules can end in "Winner" |
| `TransactionEncoder()` | Converts the lists into a True/False table (one column per item) |
| `apriori(table, min_support=0.02)` | Apriori: builds candidates level by level (5 scans of the data) |
| `fpgrowth(table, min_support=0.02)` | FP-Growth: builds a compressed tree in 2 scans, no candidates |
| `assert same` | Both must find exactly the same itemsets |
| `association_rules(..., min_threshold=0.25)` | Make rules and keep those with confidence ≥ 0.25 |
| `.sort_values("lift", ascending=False)` | Show the strongest rules first |

**Key result:** {pole position, podium} ⇒ {beat teammate, winner}: support 0.022, confidence 0.64, lift 17.2.
Apriori: 770 candidates, 5 scans. FP-tree: 4,230 nodes, 2 scans. At min_support 0.005, FP-Growth becomes faster.

**6. Say this in the jury:** "We treat every driver-race like a shopping basket. Both algorithms found the same 414 frequent itemsets and 1,393 rules. The strongest rule says that starting on pole and reaching the podium makes a win 17 times more likely than average."

**7. Viva question:** *If both give the same answer, why compare them?*
**Answer:** They differ in cost. Apriori generates candidates and rescans the data many times; FP-Growth compresses the data into a tree once. On our small 24-item data Apriori is faster at high support, but as support falls its candidates grow 11× while the tree stays the same, and at 0.005 FP-Growth wins.
