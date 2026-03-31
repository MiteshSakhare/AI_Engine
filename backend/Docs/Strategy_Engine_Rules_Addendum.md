# 📊 Strategy Engine — Rules Registry Addendum
## Extracted Directly from Client Excel Files

> **This document supplements `AI_Engine_Implementation_Plan.md`**
> It replaces the placeholder rules in `engines/strategy/rules/rules_registry.py`
> with the actual complete rule definitions extracted from the client's Excel frameworks.

---

## 1. Understanding the Four Excel Files

The client provided 4 files. Here is exactly what each one is and how they relate:

| File | What It Is | Your Role With It |
|---|---|---|
| `Strategy_Engine_Framework.xlsx` | The **original base template** — 4 equal-weight categories (Revenue, Engagement, Audience, Open Rates), placeholder weights (X, Y, Z) | Reference for the simple framework structure |
| `Sample_A.xlsx` | A **blank copy** of the base template sent to a client to fill in — all data is empty | Ignore — it's an input form, not data |
| `Strategy_Engine_Generic_Framework_SSS_4SH.xlsx` | The **advanced generic framework** — 4 categories with weighted priorities, fully filled rules with thresholds, campaigns, flows, qualifying questions | **Primary source for the rules engine** |
| `Sample_A_SSS_4SH.xlsx` | A **completed sample** of the SSS_4SH framework for a specific merchant — same rules, tweaked thresholds/weights, actual assumed KPI values | **Use as your test fixture / sample merchant data** |

### Key Difference: Two Framework Variants

**Simple Framework** (`Strategy_Engine_Framework.xlsx`):
- 4 categories, equal 25% weight each
- Category names: `Revenue`, `Engagement`, `Audience`, `Open Rates`
- Fewer rules, simpler structure — used as the blank template

**SSS_4SH Framework** (`Strategy_Engine_Generic_Framework_SSS_4SH.xlsx`):
- 4 categories with **unequal weights** (Revenue 40%, Audience Growth 30%, Audience Engagement 15%, Email Engagement 15%)
- Category names: `Revenue`, `Audience Engagement`, `Audience Growth`, `Email Engagement`
- More rules, richer thresholds, detailed qualifying questions
- **This is the production framework — code this one**

---

## 2. Category Weights (Critical for Strategy Engine Scoring)

These are the **global category weights** that the Strategy Engine uses to prioritize across rule categories.

### SSS_4SH Framework Weights (Use These)

```python
CATEGORY_WEIGHTS = {
    "revenue":             0.40,   # Highest priority — revenue is always #1
    "audience_growth":     0.30,   # Second priority — list growth, attributed revenue
    "audience_engagement": 0.15,   # Third — click rates, CVR, churn, winback
    "email_engagement":    0.15,   # Fourth — open rates, deliverability, RPR
}
```

### Sample A Client Weights (Slightly Different — Shows Per-Client Customization)

```python
# Sample A client's weights (filled in by strategist for this specific merchant)
SAMPLE_A_CATEGORY_WEIGHTS = {
    "revenue":             0.40,
    "audience_growth":     0.40,   # Bumped up — this client needs list growth more
    "audience_engagement": 0.15,
    "email_engagement":    0.05,   # Lowered — email engagement less of a priority
}
```

**Implementation Note:** Category weights should be stored per-merchant in the DB, not hardcoded. The generic SSS_4SH weights are the default. A strategist can override them per merchant via the Strategist Dashboard.

---

## 3. Complete Rules Registry

This is the full rule set to code into `engines/strategy/rules/rules_registry.py`.

Each rule has:
- `rule_id` — unique identifier
- `category` — which category group it belongs to
- `description` — human-readable problem
- `metric` — the KPI being evaluated
- `threshold` — the trigger condition
- `base_weight` — importance within its category (as a % of that category's pool)
- `campaigns` — suggested email campaign types
- `flows` — suggested Klaviyo flows to activate
- `creative_notes` — design/creative direction
- `data_source` — where to fetch the metric
- `qualifying_questions` — what the Lola chatbot or strategist should ask

---

### 3.1 Revenue Rules

```python
REVENUE_RULES = [
    {
        "rule_id": "REV-01",
        "category": "revenue",
        "description": "Low returning customer rate",
        "metric": "repeat_customer_rate",
        "condition": "repeat_customer_rate < 0.20",
        "threshold_value": 0.20,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "Winback",
            "Product Education",
            "Brand Education",
            "What's New Campaign",
            "Testimonials Campaign",
            "Sale campaigns",
        ],
        "flows": [
            "Winback",
            "Post-Purchase",
            "Second Purchase Incentive",
        ],
        "creative_notes": None,
        "data_source": "Shopify repeat rate, LTV",
        "qualifying_questions": [
            "What is time to first purchase?",
            "What is time to second purchase?",
            "What is your average purchase rate?",
            "How are you defining and measuring churn?",
            "At what point in the customer lifecycle do you see the highest churn?",
            "Are you tracking engagement scores or predictive churn indicators?",
            "What's your churn rate by customer segment or acquisition channel?",
            "Do you have a proactive retention program?",
            "How are you identifying at-risk customers?",
            "What interventions do you currently use to prevent churn?",
            "Are you personalizing experiences based on customer behavior?",
        ],
    },
    {
        "rule_id": "REV-02",
        "category": "revenue",
        "description": "High margin SKUs not promoted",
        "metric": "product_margin",
        "condition": "top_product_margin > 0.70",
        "threshold_value": 0.70,
        "threshold_operator": "gt",
        "base_weight": 5,
        "campaigns": [
            "Product Recommendation",
            "Cross/Upsell",
            "Limited edition/exclusive product launches",
            "Product Education",
        ],
        "flows": [
            "Premium Product Cross-Sell",
            "VIP Customer Flow",
        ],
        "creative_notes": "Prominent product feature, Focused email",
        "data_source": "Shopify product margin",
        "qualifying_questions": [
            "What are your top selling products?",
            "What products do you sell the least of?",
            "Why are your top-sellers the top-sellers?",
            "What are your margins on your products?",
            "What is your product release plan and calendar?",
            "What products pair best?",
            "Are people reordering the same products or trying new ones?",
        ],
    },
    {
        "rule_id": "REV-03",
        "category": "revenue",
        "description": "Discount dependency — over-reliance on promotions",
        "metric": "discount_usage_rate",
        "condition": "discount_usage_rate > 0.30",
        "threshold_value": 0.30,
        "threshold_operator": "gt",
        "base_weight": 5,
        "campaigns": [
            "Product Education",
            "Product value and quality focus campaigns",
            "Brand Education",
            "Testimonial Campaigns",
            "Early access campaigns (value over discount)",
        ],
        "flows": [
            "Post-Purchase",
            "Winback",
        ],
        "creative_notes": None,
        "data_source": "Shopify discount usage",
        "qualifying_questions": [
            "How often do you do sales?",
            "What is your propensity for discounts?",
            "What are your typical sale amounts?",
            "Are they on products or sitewide?",
        ],
    },
    {
        "rule_id": "REV-04",
        "category": "revenue",
        "description": "Inventory clearance — overstock detected",
        "metric": "inventory_overstock_flag",
        "condition": "inventory_overstock_flag == True",
        "threshold_value": True,
        "threshold_operator": "eq",
        "base_weight": 5,
        "campaigns": [
            "Flash Sale",
            "Discount",
            "Product Feature",
            "Last Chance urgency campaigns",
            "Overstock clearance campaign",
            "Bundle deal campaigns",
            "Staff Favorites picks",
        ],
        "flows": None,
        "creative_notes": "Prominent product feature, Focused email",
        "data_source": "Shopify inventory",
        "qualifying_questions": [
            "Why do you have so much inventory of X product?",
            "Why hasn't it moved?",
            "Have you marketed it and the audience isn't interested or has it not gotten proper airtime?",
        ],
    },
    {
        "rule_id": "REV-05",
        "category": "revenue",
        "description": "Low RPR — revenue per recipient below threshold",
        "metric": "revenue_per_recipient",
        "condition": "revenue_per_recipient < 0.20",
        "threshold_value": 0.20,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "Product pairing suggestion campaigns",
            "Seasonal refresh campaigns",
            "Complete Your Collection series",
            "Customer lifestyle campaigns",
        ],
        "flows": [
            "Replenishment Reminder Flow",
            "Cross-sell Flow",
            "Loyalty Milestone Flow",
            "Surprise and Delight Flow",
        ],
        "creative_notes": None,
        "data_source": "Klaviyo RPR",
        "qualifying_questions": [
            "Have you changed your email send schedule?",
            "Are you sending more emails than previously?",
            "Did you have a big boost in list size with less qualified traffic?",
            "Did you just do a big sale?",
            "What percentage of your customers make a second purchase within 90 days?",
            "How long do your products typically last a customer (30, 60, 90+ days)?",
            "Are you educating customers on proper usage?",
            "Which specific products have the highest vs. lowest repurchase rates?",
            "What does your post-purchase experience look like in the first 30-60 days?",
            "Do you send replenishment reminders based on estimated product usage timelines?",
            "Are you introducing customers to complementary products in your post-purchase flows?",
        ],
    },
    {
        "rule_id": "REV-06",
        "category": "revenue",
        "description": "Declining Average Order Value",
        "metric": "aov_mom_change",
        "condition": "aov_mom_change < -0.20",
        "threshold_value": -0.20,
        "threshold_operator": "lt",
        "base_weight": 20,
        "campaigns": [
            "Frequently Bought Together series",
            "Gift guide campaigns",
            "Bundle campaigns",
            "Middle-price product campaigns",
        ],
        "flows": [
            "Upsell Flow",
            "Post-Purchase",
        ],
        "creative_notes": None,
        "data_source": "Shopify AOV",
        "qualifying_questions": [
            "Did you just release any lower ticket items?",
            "Have you changed any of your prices?",
            "What external economic issues are happening?",
            "Have your products been on sale for a while?",
            "What does your post-purchase experience look like?",
            "How are you onboarding new customers?",
            "Do you have a loyalty or rewards program?",
        ],
    },
    {
        "rule_id": "REV-07",
        "category": "revenue",
        "description": "Declining Total Sales / Revenue",
        "metric": "revenue_yoy_change",
        "condition": "revenue_yoy_change < -0.15",
        "threshold_value": -0.15,
        "threshold_operator": "lt",
        "base_weight": 35,   # Highest weight in Revenue category
        "campaigns": [
            "Sale",
            "Product features",
            "Seasonal campaigns",
            "Brand Education",
            "VIP Campaigns",
            "Loyalty Campaigns",
            "Product Launches",
            "Cross-sell/Upsell",
        ],
        "flows": [
            "Welcome Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
            "Upsell Flow",
        ],
        "creative_notes": "Prominent product shots",
        "data_source": "Gross Revenue",
        "qualifying_questions": [
            "What happened in this month last year?",
            "Are there things we can't see in the data that would cause a decrease?",
            "Did you change any other marketing channels?",
            "Are you open to a sale?",
            "Have you increased prices?",
            "Are you experiencing higher returns or CX complaints than normal?",
            "Are you seeing fewer purchases, lower order values, or both?",
            "Have there been changes in your industry or competitive landscape?",
            "Are you seeing the decline across all customer segments?",
        ],
    },
    {
        "rule_id": "REV-08",
        "category": "revenue",
        "description": "Declining Customer LTV",
        "metric": "ltv_yoy_change",
        "condition": "ltv_yoy_change < -0.15",
        "threshold_value": -0.15,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "Long-term value education campaigns",
            "Loyalty program benefits campaigns",
            "Exclusive member experience campaigns",
        ],
        "flows": [
            "Churn Prevention Flow",
            "Milestone/Anniversary campaigns",
            "Review request campaigns",
        ],
        "creative_notes": None,
        "data_source": "Shopify LTV",
        "qualifying_questions": [
            "Have you changed your products?",
            "Has there been a boost in traffic of unqualified traffic?",
            "Have you been running too many sales?",
        ],
    },
]
```

---

### 3.2 Audience Engagement Rules

```python
AUDIENCE_ENGAGEMENT_RULES = [
    {
        "rule_id": "ENG-01",
        "category": "audience_engagement",
        "description": "Low email click rate",
        "metric": "click_rate_avg",
        "condition": "click_rate_avg < 0.01",
        "threshold_value": 0.01,
        "threshold_operator": "lt",
        "base_weight": 12,
        "campaigns": [
            "Newsletter",
            "New arrival announcement campaigns",
            "Seasonal trend campaigns",
            "Flash sale campaigns",
        ],
        "flows": [
            "Birthday Flow",
            "Welcome Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
        ],
        "creative_notes": "Move CTA Up, Focused Email",
        "data_source": "Shopify repeat rate, LTV",
        "qualifying_questions": [
            "Have you tested any segmentation?",
            "What audiences have you been sending to most?",
            "Which have you seen perform well in the past?",
            "Do click rates differ by segment?",
            "Have you changed anything in email creative strategy recently?",
        ],
    },
    {
        "rule_id": "ENG-02",
        "category": "audience_engagement",
        "description": "Low website conversion rate",
        "metric": "website_cvr",
        "condition": "website_cvr < 0.018",
        "threshold_value": 0.018,
        "threshold_operator": "lt",
        "base_weight": 18,
        "campaigns": [
            "FOMO campaigns",
            "Sale campaigns",
            "Product-focused campaign",
            "Testimonial campaigns",
        ],
        "flows": [
            "VIP Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
        ],
        "creative_notes": "Move CTA Up, Focused Email, Onsite Exit Intent Pop-Ups",
        "data_source": "Shopify CVR",
        "qualifying_questions": [
            "Did anything change on the website recently?",
            "Have you increased spend in other marketing channels?",
            "What happens when someone clicks from your email to your website?",
            "Are you sending people to product pages, collection pages, or your homepage?",
            "How aligned is your email messaging with your landing page messaging?",
            "What's your shipping and return policy?",
            "Do you have exit-intent popups or cart abandonment features on your website?",
        ],
    },
    {
        "rule_id": "ENG-03",
        "category": "audience_engagement",
        "description": "Audience fatigue — high unsubscribe rate",
        "metric": "unsubscribe_rate",
        "condition": "unsubscribe_rate > 0.01",
        "threshold_value": 0.01,
        "threshold_operator": "gt",
        "base_weight": 10,
        "campaigns": [
            "Survey/Feedback",
            "Interactive Quiz campaigns",
            "Educational content campaigns",
            "Sale Campaigns",
        ],
        "flows": [
            "Sunset Flow (re-engagement before removal)",
            "Content Preference Flow",
            "Winback",
        ],
        "creative_notes": None,
        "data_source": "Shopify discount usage",
        "qualifying_questions": [
            "How many emails have you been sending a month over the last 6 months?",
            "What segments have you been targeting?",
            "Have you done any customer feedback recently?",
            "What's your ratio of promotional vs. educational content?",
            "How often do you repeat similar offers or messaging?",
            "Are you rotating email templates and designs?",
        ],
    },
    {
        "rule_id": "ENG-04",
        "category": "audience_engagement",
        "description": "Declining Average Order Value (engagement signal)",
        "metric": "aov_mom_change",
        "condition": "aov_mom_change < -0.15",
        "threshold_value": -0.15,
        "threshold_operator": "lt",
        "base_weight": 20,
        "campaigns": [
            "Frequently Bought Together series",
            "Gift guide campaigns",
            "Bundle campaigns",
            "Middle-price product campaigns",
        ],
        "flows": [
            "Upsell Flow",
            "Post-Purchase",
            "Cross-Sell",
            "Review request",
        ],
        "creative_notes": "Shoppable emails (prominent product blocks)",
        "data_source": "Shopify AOV",
        "qualifying_questions": [
            "Did you just release any lower ticket items?",
            "Have you changed any of your prices?",
            "What external economic issues are happening?",
            "Have your products been on sale for a while?",
        ],
    },
    {
        "rule_id": "ENG-05",
        "category": "audience_engagement",
        "description": "Low returning customer rate (engagement angle)",
        "metric": "repeat_customer_rate",
        "condition": "repeat_customer_rate < 0.25",
        "threshold_value": 0.25,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "Winback",
            "Brand Education",
            "What's New Campaign",
            "Testimonials Campaign",
            "Sale campaigns",
            "New product Campaigns",
        ],
        "flows": [
            "Winback",
            "Post-Purchase",
            "Second Purchase Incentive",
            "Birthday flow",
        ],
        "creative_notes": None,
        "data_source": "Shopify repeat rate, LTV",
        "qualifying_questions": [
            "What is time to first purchase?",
            "What is time to second purchase?",
            "At what point in the customer lifecycle do you see the highest churn?",
        ],
    },
    {
        "rule_id": "ENG-06",
        "category": "audience_engagement",
        "description": "High monthly churn rate",
        "metric": "monthly_churn_rate",
        "condition": "monthly_churn_rate > 0.10",
        "threshold_value": 0.10,
        "threshold_operator": "gt",
        "base_weight": 10,
        "campaigns": [
            "Exclusive retention offers",
            "Customer feedback survey campaigns",
            "Emotion-based education campaigns",
            "Loyalty Campaigns",
            "Founder Content",
        ],
        "flows": [
            "At-Risk Customer Flow",
            "Churn Prevention Flow",
            "Feedback Collection Flow",
            "Winback",
            "Post-Purchase",
        ],
        "creative_notes": "Lifestyle content",
        "data_source": None,
        "qualifying_questions": [
            "What's your churn rate benchmark and target?",
            "What types of customers are more likely to churn?",
            "Are there certain products they're churning from?",
            "Is there a certain time of year where churn increases?",
        ],
    },
    {
        "rule_id": "ENG-07",
        "category": "audience_engagement",
        "description": "Low winback / re-engagement rate",
        "metric": "reengagement_rate",
        "condition": "reengagement_rate < 0.10",
        "threshold_value": 0.10,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "Come back to your best self campaigns",
            "Major discount campaigns (25-40% off)",
            "New launch announcement campaigns",
            "See what you've missed campaigns",
        ],
        "flows": ["Winback"],
        "creative_notes": None,
        "data_source": None,
        "qualifying_questions": [
            "What's your re-engagement rate?",
            "What's the typical time between orders?",
            "Are you offering a winback discount? If so, what %?",
            "What's changed about your brand/products since these customers left?",
            "What new value can you offer that might bring them back?",
        ],
    },
    {
        "rule_id": "ENG-08",
        "category": "audience_engagement",
        "description": "Low overall engagement rate",
        "metric": "engagement_rate",
        "condition": "engagement_rate < 0.15",
        "threshold_value": 0.15,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "Survey/Feedback",
            "Interactive Quiz campaigns",
            "Educational content campaigns",
            "Sale campaigns",
            "Newsletter",
        ],
        "flows": [
            "Winback",
            "Re-engagement Flow",
            "First-Purchase Flows",
        ],
        "creative_notes": None,
        "data_source": None,
        "qualifying_questions": [
            "How many emails have you been sending a month over the last 6 months?",
            "What segments have you been targeting?",
            "Have you done any customer feedback recently?",
            "Have you acquired new customers from a new source recently?",
            "What's your current open rate, click rate, and overall engagement score?",
        ],
    },
]
```

---

### 3.3 Audience Growth Rules

```python
AUDIENCE_GROWTH_RULES = [
    {
        "rule_id": "AUD-01",
        "category": "audience_growth",
        "description": "Low list growth / opt-in rate",
        "metric": "opt_in_rate",
        "condition": "opt_in_rate < 0.05",
        "threshold_value": 0.05,
        "threshold_operator": "lt",
        "base_weight": 24,
        "campaigns": [
            "First-time purchaser campaigns",
            "Brand education",
            "Product education",
            "Interactive Quick campaign",
            "Founder Content",
        ],
        "flows": [
            "Welcome Flow",
            "Referral Flow",
        ],
        "creative_notes": None,
        "data_source": None,
        "qualifying_questions": [
            "Do you currently have a website pop-up?",
            "What's your current list size and monthly growth rate?",
            "How many new subscribers are you gaining per month vs. losing?",
            "What's your target list size for your revenue goals?",
            "How does your current growth rate compare to 6-12 months ago?",
            "How much are you spending on paid ads to drive email signups?",
            "Are you running any referral programs or partnerships for list building?",
        ],
    },
    {
        "rule_id": "AUD-02",
        "category": "audience_growth",
        "description": "Low attributed email revenue",
        "metric": "attributed_revenue_pct",
        "condition": "attributed_revenue_pct < 0.28",
        "threshold_value": 0.28,
        "threshold_operator": "lt",
        "base_weight": 23,
        "campaigns": [
            "Product launch campaigns",
            "Sale campaigns",
            "Product Recommendation Campaigns",
            "Bundle deal campaigns",
            "Seasonal collection campaigns",
            "Loyalty campaigns",
            "Brand education",
            "Product education",
            "Cross-sell campaigns",
            "Up-sell campaigns",
        ],
        "flows": [
            "Birthday Flow",
            "Welcome Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
            "Review Request Flow",
            "Post-Purchase",
        ],
        "creative_notes": "Clear Revenue Driving CTAs, Leverage Social Proof",
        "data_source": "Shopify discount usage",
        "qualifying_questions": [
            "Which types of email campaigns drive the highest revenue?",
            "How often are you sending revenue-driving campaigns vs. nurture content?",
            "Are you personalizing offers based on customer purchase history?",
            "How long does it typically take for a new subscriber to make their first purchase?",
            "Are you tracking revenue from automated flows vs. campaigns?",
        ],
    },
    {
        "rule_id": "AUD-03",
        "category": "audience_growth",
        "description": "High list churn — unsubscribe rate too high",
        "metric": "unsubscribe_rate",
        "condition": "unsubscribe_rate > 0.01",
        "threshold_value": 0.01,
        "threshold_operator": "gt",
        "base_weight": 10,
        "campaigns": [
            "Survey/Feedback",
            "Interactive Quiz campaigns",
            "Educational content campaigns",
            "Sale Campaigns",
            "Founder Content",
        ],
        "flows": [
            "Sunset Flow (re-engagement before removal)",
            "Content Preference Flow",
            "Winback",
        ],
        "creative_notes": None,
        "data_source": "Shopify discount usage",
        "qualifying_questions": [
            "At what point in the subscriber lifecycle do you see the highest churn?",
            "Are there specific campaigns or email types that drive higher unsubscribes?",
            "Do you see seasonal patterns in your churn rates?",
            "How does churn correlate with your email frequency?",
            "Do you have a preference center to let people customize their experience?",
        ],
    },
    {
        "rule_id": "AUD-04",
        "category": "audience_growth",
        "description": "Low RPR (audience growth angle)",
        "metric": "revenue_per_recipient",
        "condition": "revenue_per_recipient < 0.25",
        "threshold_value": 0.25,
        "threshold_operator": "lt",
        "base_weight": 12,
        "campaigns": [
            "Product pairing suggestion campaigns",
            "Seasonal refresh campaigns",
            "Complete Your Collection series",
            "Customer lifestyle campaigns",
            "Gamified challenge campaigns (e.g. 60 day challenge)",
        ],
        "flows": [
            "Replenishment Reminder Flow",
            "Cross-sell Flow",
            "Loyalty Milestone Flow",
            "Post-Purchase",
        ],
        "creative_notes": None,
        "data_source": "Klaviyo RPR",
        "qualifying_questions": [
            "Have you changed your email send schedule?",
            "What percentage of customers make 3+ purchases?",
            "How long do your products typically last customers?",
            "Are you sending replenishment reminders based on usage timelines?",
            "Which products have the highest repurchase rates?",
        ],
    },
    {
        "rule_id": "AUD-05",
        "category": "audience_growth",
        "description": "Declining total sales (audience growth signal)",
        "metric": "revenue_yoy_change",
        "condition": "revenue_yoy_change < -0.15",
        "threshold_value": -0.15,
        "threshold_operator": "lt",
        "base_weight": 21,
        "campaigns": [
            "Sale",
            "Product features",
            "Seasonal campaigns",
            "Brand Education",
            "VIP Campaigns",
            "Loyalty Campaigns",
            "Product Launches",
            "Cross-sell/Upsell",
        ],
        "flows": [
            "Welcome Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
            "Upsell Flow",
            "Post-Purchase",
            "Winback",
        ],
        "creative_notes": "Prominent product shots",
        "data_source": "Gross Revenue",
        "qualifying_questions": [
            "What happened in this month last year?",
            "Did you change any other marketing channels?",
            "Are you open to a sale?",
        ],
    },
    {
        "rule_id": "AUD-06",
        "category": "audience_growth",
        "description": "Weak VIP program — few VIP customers",
        "metric": "vip_pct_of_list",
        "condition": "vip_pct_of_list < 0.05",
        "threshold_value": 0.05,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "VIP Sales",
            "VIP member appreciation campaigns",
            "Product Education",
            "Product recommendation campaigns",
            "Interactive Quiz campaigns",
        ],
        "flows": [
            "VIP Onboarding Flow",
            "VIP Cross-Sell Flow",
            "Loyalty Program Flow",
            "Points Redemption Reminder Flow",
        ],
        "creative_notes": None,
        "data_source": None,
        "qualifying_questions": [
            "What percentage of your customers are enrolled in your VIP/loyalty program?",
            "What's the engagement rate within your loyalty program?",
            "How do VIP customers perform vs. non-VIP customers (LTV, purchase frequency, AOV)?",
            "What exclusive benefits do VIP members receive?",
            "Are you giving your VIPs early access to launches and sales?",
        ],
    },
]
```

---

### 3.4 Email Engagement Rules

```python
EMAIL_ENGAGEMENT_RULES = [
    {
        "rule_id": "OPEN-01",
        "category": "email_engagement",
        "description": "Low email open rate",
        "metric": "open_rate_avg",
        "condition": "open_rate_avg < 0.30",
        "threshold_value": 0.30,
        "threshold_operator": "lt",
        "base_weight": 5,
        "campaigns": [
            "FOMO campaigns",
            "Sale campaigns",
            "Founder Content",
            "Product Education",
            "Brand Education",
            "Testimonial Campaigns",
        ],
        "flows": [
            "Welcome Flow",
            "Browse Abandon Flow",
            "Cart Abandon Flow",
            "Checkout Abandon Flow",
            "Winback Flow",
            "Post-Purchase Flow",
            "Order Confirmation Flow",
            "Review Request Flow",
            "VIP Onboarding Flow",
        ],
        "creative_notes": "Strong subject lines, Test emojis, Send-time optimization",
        "data_source": "Klaviyo Open Rate",
        "qualifying_questions": [
            "What's your current average open rate, and how has it trended over the past 3-6 months?",
            "How does your open rate vary by campaign type?",
            "Are you seeing consistent low opens across all segments, or is it specific groups?",
            "How do you currently approach writing subject lines?",
            "Are you A/B testing subject lines regularly?",
            "What name appears in the from field?",
            "When was the last time you cleaned your list of inactive subscribers?",
            "What days and times of day are you typically sending emails?",
            "Are you optimizing your preview text/pre-header content?",
        ],
    },
    {
        "rule_id": "OPEN-02",
        "category": "email_engagement",
        "description": "Low email click rate (email engagement angle)",
        "metric": "click_rate_avg",
        "condition": "click_rate_avg < 0.008",
        "threshold_value": 0.008,
        "threshold_operator": "lt",
        "base_weight": 15,
        "campaigns": [
            "Newsletter",
            "New arrival announcement campaigns",
            "Seasonal trend campaigns",
            "Flash sale campaigns",
            "Brand education campaign",
            "Testimonials campaign",
        ],
        "flows": [
            "Birthday Flow",
            "Welcome Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
            "Review Request Flow",
        ],
        "creative_notes": "Move CTA Up, Focused Email",
        "data_source": "Shopify repeat rate, LTV",
        "qualifying_questions": [
            "Have you tested any segmentation?",
            "Do click rates differ by segment?",
            "Have you changed anything in email creative strategy recently?",
        ],
    },
    {
        "rule_id": "OPEN-03",
        "category": "email_engagement",
        "description": "Low website CVR (email engagement angle)",
        "metric": "website_cvr",
        "condition": "website_cvr < 0.016",
        "threshold_value": 0.016,
        "threshold_operator": "lt",
        "base_weight": 20,
        "campaigns": [
            "FOMO campaigns",
            "Bundle offer campaigns",
            "Sale campaigns",
            "Testimonial campaigns",
        ],
        "flows": [
            "VIP Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
            "Post-purchase",
            "Order upcoming",
        ],
        "creative_notes": "Move CTA Up, Focused Email, Onsite Pop-Ups",
        "data_source": "Shopify CVR",
        "qualifying_questions": [
            "Did anything change on the website recently?",
            "What happens when someone clicks from your email to your website?",
            "How aligned is your email messaging with your landing page messaging?",
        ],
    },
    {
        "rule_id": "OPEN-04",
        "category": "email_engagement",
        "description": "Low RPR (email engagement angle)",
        "metric": "revenue_per_recipient",
        "condition": "revenue_per_recipient < 0.18",
        "threshold_value": 0.18,
        "threshold_operator": "lt",
        "base_weight": 15,
        "campaigns": [
            "Product pairing suggestion campaigns",
            "Seasonal refresh campaigns",
            "Complete Your Collection series",
            "Customer lifestyle campaigns",
        ],
        "flows": [
            "Replenishment Reminder Flow",
            "Cross-sell Flow",
            "Loyalty Milestone Flow",
            "Surprise and Delight Flow",
        ],
        "creative_notes": None,
        "data_source": "Klaviyo RPR",
        "qualifying_questions": [
            "Have you changed your email send schedule?",
            "What percentage of your customers make a second purchase within 90 days?",
        ],
    },
    {
        "rule_id": "OPEN-05",
        "category": "email_engagement",
        "description": "Dropping email deliverability rate",
        "metric": "deliverability_rate",
        "condition": "deliverability_rate < 0.68",
        "threshold_value": 0.68,
        "threshold_operator": "lt",
        "base_weight": 10,
        "campaigns": [
            "We miss you engagement campaigns",
            "List preference campaigns",
            "Feedback collection campaigns",
            "Highest-engagement campaigns",
            "VIP campaigns",
        ],
        "flows": [
            "Re-engagement Flow",
            "Sunset Flow",
            "Welcome Flow",
        ],
        "creative_notes": None,
        "data_source": None,
        "qualifying_questions": [
            "Which email providers are showing the worst deliverability?",
            "How many emails have you been sending a month over the last 6 months?",
            "What's your current bounce rate, and how has it changed recently?",
            "When did you last clean your email list?",
            "What's your unsubscribe rate, and has it increased recently?",
            "Have you increased your email frequency recently?",
            "Are you sending to purchased lists or only opted-in subscribers?",
        ],
    },
    {
        "rule_id": "OPEN-06",
        "category": "email_engagement",
        "description": "Low attributed email revenue (email angle)",
        "metric": "attributed_revenue_pct",
        "condition": "attributed_revenue_pct < 0.30",
        "threshold_value": 0.30,
        "threshold_operator": "lt",
        "base_weight": 27,  # Highest weight in email engagement
        "campaigns": [
            "Product launch campaigns",
            "Sale campaigns",
            "Bundle deal campaigns",
            "Seasonal collection campaigns",
            "Loyalty campaigns",
            "Brand education",
            "Product education",
            "Newsletter",
            "Cross-sell campaigns",
            "Up-sell campaigns",
        ],
        "flows": [
            "Birthday Flow",
            "Browse Abandon",
            "Cart Abandon",
            "Checkout Abandon",
            "Review Request Flow",
            "Post-Purchase",
        ],
        "creative_notes": "Clear Revenue Driving CTAs, Leverage Social Proof",
        "data_source": "Shopify discount usage",
        "qualifying_questions": [
            "Which types of email campaigns drive the highest revenue?",
            "How often are you sending revenue-driving campaigns vs. nurture content?",
            "Are you personalizing offers based on customer purchase history?",
        ],
    },
    {
        "rule_id": "OPEN-07",
        "category": "email_engagement",
        "description": "Low overall engagement rate (email angle)",
        "metric": "engagement_rate",
        "condition": "engagement_rate < 0.15",
        "threshold_value": 0.15,
        "threshold_operator": "lt",
        "base_weight": 8,
        "campaigns": [
            "Survey/Feedback",
            "Interactive Quiz campaigns",
            "Educational content campaigns",
            "Sale campaigns",
        ],
        "flows": [
            "Winback",
            "Re-engagement Flow",
        ],
        "creative_notes": None,
        "data_source": None,
        "qualifying_questions": [
            "How many emails have you been sending a month over the last 6 months?",
            "What segments have you been targeting?",
            "Which emails or campaigns get the highest engagement?",
        ],
    },
]
```

---

## 4. Master Rules Registry (All Rules Combined)

```python
# engines/strategy/rules/rules_registry.py

ALL_RULES = (
    REVENUE_RULES +
    AUDIENCE_ENGAGEMENT_RULES +
    AUDIENCE_GROWTH_RULES +
    EMAIL_ENGAGEMENT_RULES
)

# Quick lookup by rule_id
RULES_BY_ID = {rule["rule_id"]: rule for rule in ALL_RULES}

# Quick lookup by category
RULES_BY_CATEGORY = {
    "revenue":             REVENUE_RULES,
    "audience_engagement": AUDIENCE_ENGAGEMENT_RULES,
    "audience_growth":     AUDIENCE_GROWTH_RULES,
    "email_engagement":    EMAIL_ENGAGEMENT_RULES,
}

# Total rule counts
# Revenue:             8 rules
# Audience Engagement: 8 rules
# Audience Growth:     6 rules
# Email Engagement:    7 rules
# TOTAL:              29 rules
```

---

## 5. Required Merchant Metrics (What the Feature Store Must Provide)

Based on the complete rule set, these are **all the metrics** the Strategy Engine needs to evaluate conditions:

| Metric Key | Description | Source | Used By Rules |
|---|---|---|---|
| `repeat_customer_rate` | % customers who ordered 2+ times | Shopify | REV-01, ENG-05 |
| `top_product_margin` | Highest margin product's margin % | Shopify | REV-02 |
| `discount_usage_rate` | % orders using a discount code | Shopify | REV-03 |
| `inventory_overstock_flag` | Boolean — any SKU significantly overstocked | Shopify | REV-04 |
| `revenue_per_recipient` | Total email revenue / emails sent | Klaviyo | REV-05, AUD-04, OPEN-04 |
| `aov_mom_change` | AOV % change month-over-month | Shopify | REV-06, ENG-04 |
| `revenue_yoy_change` | Revenue % change year-over-year | Shopify | REV-07, AUD-05 |
| `ltv_yoy_change` | LTV % change year-over-year | Shopify | REV-08 |
| `click_rate_avg` | Average email click rate | Klaviyo | ENG-01, OPEN-02 |
| `website_cvr` | Website conversion rate (sessions → purchase) | Shopify | ENG-02, OPEN-03 |
| `unsubscribe_rate` | Email unsubscribe rate | Klaviyo | ENG-03, AUD-03 |
| `monthly_churn_rate` | % customers who churned this month | Shopify | ENG-06 |
| `reengagement_rate` | % lapsed customers who returned | Klaviyo | ENG-07 |
| `engagement_rate` | Overall email engagement score | Klaviyo | ENG-08, OPEN-07 |
| `opt_in_rate` | New subscribers / total visitors | Klaviyo | AUD-01 |
| `attributed_revenue_pct` | Email-attributed revenue / total revenue | Klaviyo | AUD-02, OPEN-06 |
| `vip_pct_of_list` | VIP/loyalty segment / total list | Klaviyo/Shopify | AUD-06 |
| `open_rate_avg` | Average email open rate | Klaviyo | OPEN-01 |
| `deliverability_rate` | % emails successfully delivered | Klaviyo | OPEN-05 |

---

## 6. Sample Merchant Test Fixture

Extracted from `Sample_A_SSS_4SH.xlsx` — this is real assumed data for a sample merchant. Use this as your test fixture in `tests/fixtures/sample_merchant_features.json`.

```json
{
  "merchant_id": "sample-a-test-merchant",
  "vertical": "beauty",
  "metrics": {
    "revenue_per_recipient":    0.14,
    "revenue_yoy_change":      -0.17,
    "ltv_yoy_change":          -0.21,
    "repeat_customer_rate":     0.22,
    "open_rate_avg":            0.50,
    "click_rate_avg":           0.005,
    "website_cvr":              0.012,
    "unsubscribe_rate":         0.012,
    "monthly_churn_rate":       0.17,
    "engagement_rate":          0.08,
    "opt_in_rate":              0.042,
    "attributed_revenue_pct":   0.26,
    "vip_pct_of_list":          0.03,
    "top_product_margin":       0.75,
    "discount_usage_rate":      0.22,
    "inventory_overstock_flag": false,
    "aov_mom_change":           0.00,
    "reengagement_rate":        0.06
  }
}
```

### Expected Rules to Fire for This Merchant

Based on the sample data above and the rule thresholds, these rules should trigger:

| Rule ID | Metric | Merchant Value | Threshold | Should Fire? |
|---|---|---|---|---|
| REV-01 | repeat_customer_rate | 0.22 | < 0.20 | ❌ No (22% > 20%) |
| REV-02 | top_product_margin | 0.75 | > 0.70 | ✅ Yes |
| REV-05 | revenue_per_recipient | $0.14 | < $0.20 | ✅ Yes |
| REV-07 | revenue_yoy_change | -17% | < -15% | ✅ Yes |
| REV-08 | ltv_yoy_change | -21% | < -15% | ✅ Yes |
| ENG-01 | click_rate_avg | 0.5% | < 1% | ✅ Yes |
| ENG-02 | website_cvr | 1.2% | < 1.8% | ✅ Yes |
| ENG-03 | unsubscribe_rate | 1.2% | > 1% | ✅ Yes |
| ENG-07 | reengagement_rate | 6% | < 10% | ✅ Yes |
| ENG-08 | engagement_rate | 8% | < 15% | ✅ Yes |
| AUD-01 | opt_in_rate | 4.2% | < 5% | ✅ Yes |
| AUD-02 | attributed_revenue_pct | 26% | < 28% | ✅ Yes |
| AUD-03 | unsubscribe_rate | 1.2% | > 1% | ✅ Yes |
| AUD-04 | revenue_per_recipient | $0.14 | < $0.25 | ✅ Yes |
| AUD-05 | revenue_yoy_change | -17% | < -15% | ✅ Yes |
| AUD-06 | vip_pct_of_list | 3% | < 5% | ✅ Yes |
| OPEN-01 | open_rate_avg | 50% | < 30% | ❌ No (50% > 30%) |
| OPEN-02 | click_rate_avg | 0.5% | < 0.8% | ✅ Yes |
| OPEN-03 | website_cvr | 1.2% | < 1.6% | ✅ Yes |
| OPEN-04 | revenue_per_recipient | $0.14 | < $0.18 | ✅ Yes |
| OPEN-06 | attributed_revenue_pct | 26% | < 30% | ✅ Yes |
| OPEN-07 | engagement_rate | 8% | < 15% | ✅ Yes |

**16 rules fire for this merchant.** Your Strategy Engine should de-duplicate and rank these using the scoring formula, returning the top 5.

---

## 7. Final Strategy Preview — What the Output Should Look Like

From `Sample_A_SSS_4SH.xlsx` Final Strategy Preview sheet, the strategist selected these 11 strategies for this client. Use this to validate your Strategy Engine output order and content:

| Priority | Category | Campaign/Flow | Trigger Rule |
|---|---|---|---|
| 1 | Revenue | Product pairing suggestion campaigns + Replenishment Reminder Flow + Cross-sell Flow | Low RPR (REV-05) |
| 2 | Revenue | Brand Education + Product Launches + Cross-sell/Upsell + Browse/Cart/Checkout Abandon | Declining Total Sales (REV-07) |
| 3 | Revenue | Exclusive member experience/Loyalty + Churn Prevention + Anniversary campaigns | Declining LTV (REV-08) |
| 4 | Audience Engagement | Newsletter + Seasonal campaigns + Birthday/Welcome/Abandon Flows | Low CTR (ENG-01) |
| 5 | Audience Engagement | FOMO + Bundle + Sale + Testimonial + Browse/Cart/Checkout Abandon | Low CVR (ENG-02) |
| 6 | Audience Engagement | New launch + See what you've missed + Winback Flow | Winback (ENG-07) |
| 7 | Audience Engagement | Survey/Feedback + Quiz + Educational + Winback/Re-engagement | Low Engagement Rate (ENG-08) |
| 8 | Audience Growth | VIP Campaigns + VIP Onboarding/Cross-Sell/Loyalty Flows | Weak VIP (AUD-06) |
| 9 | Audience Growth | Product launch + Loyalty + Brand ed + Cross-sell + All Abandon Flows | Attributed Revenue (AUD-02) |
| 10 | Audience Growth | First-time purchaser + Brand ed + Product ed + Welcome/Referral Flows | List Growth (AUD-01) |
| 11 | Email Engagement | FOMO + Founder Content + Product Ed + All Abandon/Winback Flows | Low Open Rate (OPEN-01) |

**Note:** This is what a human strategist selected from all fired rules. Your ML ranking model should learn to reproduce this ordering.

---

## 8. Important Notes for Implementation

### Duplicate Rules Across Categories
Several rules appear in multiple categories (e.g., `unsubscribe_rate` triggers both `ENG-03` and `AUD-03`; `revenue_yoy_change` triggers `REV-07`, `AUD-05`). This is intentional — each fires independently and contributes its category weight. However, **do not show duplicate campaign recommendations** in the final output. De-duplicate at the campaign/flow level, keeping the highest-scored instance.

### Per-Merchant Threshold Customization
The thresholds in the rules are **defaults from the generic framework**. A strategist may override specific thresholds for a specific merchant (e.g., a brand in a low-margin industry might use `discount_usage_rate > 0.50` instead of the default `0.30`). Plan for threshold overrides to be stored per-merchant in the DB alongside the rules.

### Rules Are Living Documents
The Excel files contain a footer row in every sheet: *"Please provide additional rulesets as per your judgement following the above structure."* This confirms the rules are expected to grow. Your `rules_registry.py` must support adding new rules without code changes — rules should be loadable from DB, not hardcoded in the Python file.

### Qualifying Questions → Lola Chatbot
The `qualifying_questions` arrays are the source of truth for what the "Lola" onboarding chatbot should ask. When a rule fires and a strategy is presented to the strategist, these questions should surface as *"Ask the merchant these questions to refine this strategy."* They are also used to collect more context during onboarding.
