"""
Strategy Rules Registry — Complete 29-rule production set.

Extracted from client Excel files (SSS_4SH Framework).
Categories: Revenue (40%), Audience Engagement (15%),
            Audience Growth (30%), Email Engagement (15%).

File: backend/engines/strategy/rules/rules_registry.py
"""

from __future__ import annotations
from typing import Dict, List


# ── Category Weights (SSS_4SH Framework) ────────────

CATEGORY_WEIGHTS: Dict[str, float] = {
    "revenue":             0.40,
    "audience_growth":     0.30,
    "audience_engagement": 0.15,
    "email_engagement":    0.15,
}


# ── Rule Definition ─────────────────────────────────

class RuleDefinition:
    """Single rule from the Excel rule framework."""

    def __init__(
        self,
        rule_id: str,
        category: str,
        description: str,
        metric: str,
        threshold_operator: str,   # "lt", "gt", "eq"
        threshold_value: float | bool,
        base_weight: int,          # Importance within category (sums to ~100)
        campaigns: List[str] | None = None,
        flows: List[str] | None = None,
        creative_notes: str | None = None,
        data_source: str | None = None,
        qualifying_questions: List[str] | None = None,
    ):
        self.rule_id = rule_id
        self.category = category
        self.description = description
        self.metric = metric
        self.threshold_operator = threshold_operator
        self.threshold_value = threshold_value
        self.base_weight = base_weight
        self.campaigns = campaigns or []
        self.flows = flows or []
        self.creative_notes = creative_notes
        self.data_source = data_source
        self.qualifying_questions = qualifying_questions or []

    @property
    def normalised_weight(self) -> float:
        """Weight normalised by category total (0–1)."""
        cat_rules = RULES_BY_CATEGORY.get(self.category, [])
        total = sum(r.base_weight for r in cat_rules) or 1
        return self.base_weight / total

    @property
    def global_weight(self) -> float:
        """Weight adjusted by category priority (0–1)."""
        cat_w = CATEGORY_WEIGHTS.get(self.category, 0.25)
        return self.normalised_weight * cat_w


# ══════════════════════════════════════════════════════
# 3.1  REVENUE RULES  (8 rules, category weight 40%)
# ══════════════════════════════════════════════════════

REVENUE_RULES: List[RuleDefinition] = [
    RuleDefinition(
        rule_id="REV-01",
        category="revenue",
        description="Low returning customer rate",
        metric="repeat_customer_rate",
        threshold_operator="lt",
        threshold_value=0.20,
        base_weight=10,
        campaigns=[
            "Winback", "Product Education", "Brand Education",
            "What's New Campaign", "Testimonials Campaign", "Sale campaigns",
        ],
        flows=["Winback", "Post-Purchase", "Second Purchase Incentive"],
        data_source="Shopify repeat rate, LTV",
        qualifying_questions=[
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
    ),
    RuleDefinition(
        rule_id="REV-02",
        category="revenue",
        description="High margin SKUs not promoted",
        metric="top_product_margin",
        threshold_operator="gt",
        threshold_value=0.70,
        base_weight=5,
        campaigns=[
            "Product Recommendation", "Cross/Upsell",
            "Limited edition/exclusive product launches", "Product Education",
        ],
        flows=["Premium Product Cross-Sell", "VIP Customer Flow"],
        creative_notes="Prominent product feature, Focused email",
        data_source="Shopify product margin",
        qualifying_questions=[
            "What are your top selling products?",
            "What products do you sell the least of?",
            "Why are your top-sellers the top-sellers?",
            "What are your margins on your products?",
            "What is your product release plan and calendar?",
            "What products pair best?",
            "Are people reordering the same products or trying new ones?",
        ],
    ),
    RuleDefinition(
        rule_id="REV-03",
        category="revenue",
        description="Discount dependency — over-reliance on promotions",
        metric="discount_usage_rate",
        threshold_operator="gt",
        threshold_value=0.30,
        base_weight=5,
        campaigns=[
            "Product Education", "Product value and quality focus campaigns",
            "Brand Education", "Testimonial Campaigns",
            "Early access campaigns (value over discount)",
        ],
        flows=["Post-Purchase", "Winback"],
        data_source="Shopify discount usage",
        qualifying_questions=[
            "How often do you do sales?",
            "What is your propensity for discounts?",
            "What are your typical sale amounts?",
            "Are they on products or sitewide?",
        ],
    ),
    RuleDefinition(
        rule_id="REV-04",
        category="revenue",
        description="Inventory clearance — overstock detected",
        metric="inventory_overstock_flag",
        threshold_operator="eq",
        threshold_value=True,
        base_weight=5,
        campaigns=[
            "Flash Sale", "Discount", "Product Feature",
            "Last Chance urgency campaigns", "Overstock clearance campaign",
            "Bundle deal campaigns", "Staff Favorites picks",
        ],
        creative_notes="Prominent product feature, Focused email",
        data_source="Shopify inventory",
        qualifying_questions=[
            "Why do you have so much inventory of X product?",
            "Why hasn't it moved?",
            "Have you marketed it and the audience isn't interested or has it not gotten proper airtime?",
        ],
    ),
    RuleDefinition(
        rule_id="REV-05",
        category="revenue",
        description="Low RPR — revenue per recipient below threshold",
        metric="revenue_per_recipient",
        threshold_operator="lt",
        threshold_value=0.20,
        base_weight=10,
        campaigns=[
            "Product pairing suggestion campaigns", "Seasonal refresh campaigns",
            "Complete Your Collection series", "Customer lifestyle campaigns",
        ],
        flows=[
            "Replenishment Reminder Flow", "Cross-sell Flow",
            "Loyalty Milestone Flow", "Surprise and Delight Flow",
        ],
        data_source="Klaviyo RPR",
        qualifying_questions=[
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
    ),
    RuleDefinition(
        rule_id="REV-06",
        category="revenue",
        description="Declining Average Order Value",
        metric="aov_mom_change",
        threshold_operator="lt",
        threshold_value=-0.20,
        base_weight=20,
        campaigns=[
            "Frequently Bought Together series", "Gift guide campaigns",
            "Bundle campaigns", "Middle-price product campaigns",
        ],
        flows=["Upsell Flow", "Post-Purchase"],
        data_source="Shopify AOV",
        qualifying_questions=[
            "Did you just release any lower ticket items?",
            "Have you changed any of your prices?",
            "What external economic issues are happening?",
            "Have your products been on sale for a while?",
            "What does your post-purchase experience look like?",
            "How are you onboarding new customers?",
            "Do you have a loyalty or rewards program?",
        ],
    ),
    RuleDefinition(
        rule_id="REV-07",
        category="revenue",
        description="Declining Total Sales / Revenue",
        metric="revenue_yoy_change",
        threshold_operator="lt",
        threshold_value=-0.15,
        base_weight=35,
        campaigns=[
            "Sale", "Product features", "Seasonal campaigns",
            "Brand Education", "VIP Campaigns", "Loyalty Campaigns",
            "Product Launches", "Cross-sell/Upsell",
        ],
        flows=[
            "Welcome Flow", "Browse Abandon", "Cart Abandon",
            "Checkout Abandon", "Upsell Flow",
        ],
        creative_notes="Prominent product shots",
        data_source="Gross Revenue",
        qualifying_questions=[
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
    ),
    RuleDefinition(
        rule_id="REV-08",
        category="revenue",
        description="Declining Customer LTV",
        metric="ltv_yoy_change",
        threshold_operator="lt",
        threshold_value=-0.15,
        base_weight=10,
        campaigns=[
            "Long-term value education campaigns",
            "Loyalty program benefits campaigns",
            "Exclusive member experience campaigns",
        ],
        flows=[
            "Churn Prevention Flow", "Milestone/Anniversary campaigns",
            "Review request campaigns",
        ],
        data_source="Shopify LTV",
        qualifying_questions=[
            "Have you changed your products?",
            "Has there been a boost in traffic of unqualified traffic?",
            "Have you been running too many sales?",
        ],
    ),
    RuleDefinition(
        rule_id="REV-09",
        category="revenue",
        description="High product refund rate detected",
        metric="refund_rate",
        threshold_operator="gt",
        threshold_value=0.05,
        base_weight=15,
        campaigns=["Detailed Product Guides", "Size/Fit Finder Highlights", "Customer Feedback Campaigns"],
        flows=["Post-Purchase Education", "Customer Service Escalation"],
        data_source="Shopify refunds",
        qualifying_questions=[
            "Are refunds localized to specific SKUs?",
            "Is sizing or product quality the primary issue?"
        ],
    ),
    RuleDefinition(
        rule_id="REV-10",
        category="revenue",
        description="Low Customer Lifetime Value",
        metric="customer_ltv",
        threshold_operator="lt",
        threshold_value=120.0,
        base_weight=20,
        campaigns=["Loyalty point multipliers", "Bundle promotions", "Subscription value offers"],
        flows=["VIP Flow", "Replenishment Flow"],
        data_source="Shopify LTV",
        qualifying_questions=[
            "Are you tracking LTV by acquisition channel?",
            "Do you have an active loyalty program?"
        ],
    ),
    RuleDefinition(
        rule_id="REV-11",
        category="revenue",
        description="High Cart Abandonment Rate",
        metric="cart_abandonment_rate",
        threshold_operator="gt",
        threshold_value=0.65,
        base_weight=15,
        campaigns=["Trust building campaigns", "Payment option highlights (BNPL)", "Shipping policy updates"],
        flows=["Cart Abandonment Flow", "Checkout Abandonment Flow"],
        data_source="Shopify Cart",
        qualifying_questions=[
            "Is standard shipping too expensive or slow?",
            "Are there hidden costs revealed at checkout?"
        ],
    ),
]


# ══════════════════════════════════════════════════════
# 3.2  AUDIENCE ENGAGEMENT RULES  (8 rules, 15%)
# ══════════════════════════════════════════════════════

AUDIENCE_ENGAGEMENT_RULES: List[RuleDefinition] = [
    RuleDefinition(
        rule_id="ENG-01",
        category="audience_engagement",
        description="Low email click rate",
        metric="click_rate_avg",
        threshold_operator="lt",
        threshold_value=0.01,
        base_weight=12,
        campaigns=[
            "Newsletter", "New arrival announcement campaigns",
            "Seasonal trend campaigns", "Flash sale campaigns",
        ],
        flows=[
            "Birthday Flow", "Welcome Flow", "Browse Abandon",
            "Cart Abandon", "Checkout Abandon",
        ],
        creative_notes="Move CTA Up, Focused Email",
        data_source="Shopify repeat rate, LTV",
        qualifying_questions=[
            "Have you tested any segmentation?",
            "What audiences have you been sending to most?",
            "Which have you seen perform well in the past?",
            "Do click rates differ by segment?",
            "Have you changed anything in email creative strategy recently?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-02",
        category="audience_engagement",
        description="Low website conversion rate",
        metric="website_cvr",
        threshold_operator="lt",
        threshold_value=0.018,
        base_weight=18,
        campaigns=[
            "FOMO campaigns", "Sale campaigns",
            "Product-focused campaign", "Testimonial campaigns",
        ],
        flows=["VIP Flow", "Browse Abandon", "Cart Abandon", "Checkout Abandon"],
        creative_notes="Move CTA Up, Focused Email, Onsite Exit Intent Pop-Ups",
        data_source="Shopify CVR",
        qualifying_questions=[
            "Did anything change on the website recently?",
            "Have you increased spend in other marketing channels?",
            "What happens when someone clicks from your email to your website?",
            "Are you sending people to product pages, collection pages, or your homepage?",
            "How aligned is your email messaging with your landing page messaging?",
            "What's your shipping and return policy?",
            "Do you have exit-intent popups or cart abandonment features on your website?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-03",
        category="audience_engagement",
        description="Audience fatigue — high unsubscribe rate",
        metric="unsubscribe_rate",
        threshold_operator="gt",
        threshold_value=0.01,
        base_weight=10,
        campaigns=[
            "Survey/Feedback", "Interactive Quiz campaigns",
            "Educational content campaigns", "Sale Campaigns",
        ],
        flows=[
            "Sunset Flow (re-engagement before removal)",
            "Content Preference Flow", "Winback",
        ],
        data_source="Shopify discount usage",
        qualifying_questions=[
            "How many emails have you been sending a month over the last 6 months?",
            "What segments have you been targeting?",
            "Have you done any customer feedback recently?",
            "What's your ratio of promotional vs. educational content?",
            "How often do you repeat similar offers or messaging?",
            "Are you rotating email templates and designs?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-04",
        category="audience_engagement",
        description="Declining Average Order Value (engagement signal)",
        metric="aov_mom_change",
        threshold_operator="lt",
        threshold_value=-0.15,
        base_weight=20,
        campaigns=[
            "Frequently Bought Together series", "Gift guide campaigns",
            "Bundle campaigns", "Middle-price product campaigns",
        ],
        flows=["Upsell Flow", "Post-Purchase", "Cross-Sell", "Review request"],
        creative_notes="Shoppable emails (prominent product blocks)",
        data_source="Shopify AOV",
        qualifying_questions=[
            "Did you just release any lower ticket items?",
            "Have you changed any of your prices?",
            "What external economic issues are happening?",
            "Have your products been on sale for a while?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-05",
        category="audience_engagement",
        description="Low returning customer rate (engagement angle)",
        metric="repeat_customer_rate",
        threshold_operator="lt",
        threshold_value=0.25,
        base_weight=10,
        campaigns=[
            "Winback", "Brand Education", "What's New Campaign",
            "Testimonials Campaign", "Sale campaigns", "New product Campaigns",
        ],
        flows=[
            "Winback", "Post-Purchase",
            "Second Purchase Incentive", "Birthday flow",
        ],
        data_source="Shopify repeat rate, LTV",
        qualifying_questions=[
            "What is time to first purchase?",
            "What is time to second purchase?",
            "At what point in the customer lifecycle do you see the highest churn?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-06",
        category="audience_engagement",
        description="High monthly churn rate",
        metric="monthly_churn_rate",
        threshold_operator="gt",
        threshold_value=0.10,
        base_weight=10,
        campaigns=[
            "Exclusive retention offers", "Customer feedback survey campaigns",
            "Emotion-based education campaigns", "Loyalty Campaigns", "Founder Content",
        ],
        flows=[
            "At-Risk Customer Flow", "Churn Prevention Flow",
            "Feedback Collection Flow", "Winback", "Post-Purchase",
        ],
        creative_notes="Lifestyle content",
        qualifying_questions=[
            "What's your churn rate benchmark and target?",
            "What types of customers are more likely to churn?",
            "Are there certain products they're churning from?",
            "Is there a certain time of year where churn increases?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-07",
        category="audience_engagement",
        description="Low winback / re-engagement rate",
        metric="reengagement_rate",
        threshold_operator="lt",
        threshold_value=0.10,
        base_weight=10,
        campaigns=[
            "Come back to your best self campaigns",
            "Major discount campaigns (25-40% off)",
            "New launch announcement campaigns",
            "See what you've missed campaigns",
        ],
        flows=["Winback"],
        qualifying_questions=[
            "What's your re-engagement rate?",
            "What's the typical time between orders?",
            "Are you offering a winback discount? If so, what %?",
            "What's changed about your brand/products since these customers left?",
            "What new value can you offer that might bring them back?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-08",
        category="audience_engagement",
        description="Low overall engagement rate",
        metric="engagement_rate",
        threshold_operator="lt",
        threshold_value=0.15,
        base_weight=10,
        campaigns=[
            "Survey/Feedback", "Interactive Quiz campaigns",
            "Educational content campaigns", "Sale campaigns", "Newsletter",
        ],
        flows=["Winback", "Re-engagement Flow", "First-Purchase Flows"],
        qualifying_questions=[
            "How many emails have you been sending a month over the last 6 months?",
            "What segments have you been targeting?",
            "Have you done any customer feedback recently?",
            "Have you acquired new customers from a new source recently?",
            "What's your current open rate, click rate, and overall engagement score?",
        ],
    ),
    RuleDefinition(
        rule_id="ENG-09",
        category="audience_engagement",
        description="Low average onsite time",
        metric="onsite_time_avg",
        threshold_operator="lt",
        threshold_value=60.0,
        base_weight=10,
        campaigns=["Interactive content campaigns", "Brand storytelling", "Video-focused emails"],
        flows=["Welcome Flow", "Content Nurture Flow"],
        data_source="Google Analytics",
        qualifying_questions=[
            "Are visitors landing on product pages or the homepage?",
            "Is the page load speed slow on mobile devices?"
        ],
    ),
    RuleDefinition(
        rule_id="ENG-10",
        category="audience_engagement",
        description="High website bounce rate",
        metric="bounce_rate_avg",
        threshold_operator="gt",
        threshold_value=0.60,
        base_weight=10,
        campaigns=["Clear Value Proposition campaigns", "Bestseller feature collections"],
        flows=["Welcome Flow"],
        data_source="Google Analytics",
        qualifying_questions=[
            "Does the ad messaging align with the landing page design?",
            "Are pop-ups driving users away immediately?"
        ],
    ),
    RuleDefinition(
        rule_id="ENG-11",
        category="audience_engagement",
        description="Low product review rate",
        metric="product_review_rate",
        threshold_operator="lt",
        threshold_value=0.02,
        base_weight=10,
        campaigns=["Review incentives", "User generated content showcases"],
        flows=["Review Request Flow", "Post-Purchase Flow"],
        data_source="Shopify Reviews",
        qualifying_questions=[
            "Are you offering an incentive for reviews (points, discount)?",
            "Is the review request sent at the right time after delivery?"
        ],
    ),
]


# ══════════════════════════════════════════════════════
# 3.3  AUDIENCE GROWTH RULES  (6 rules, 30%)
# ══════════════════════════════════════════════════════

AUDIENCE_GROWTH_RULES: List[RuleDefinition] = [
    RuleDefinition(
        rule_id="AUD-01",
        category="audience_growth",
        description="Low list growth / opt-in rate",
        metric="opt_in_rate",
        threshold_operator="lt",
        threshold_value=0.05,
        base_weight=24,
        campaigns=[
            "First-time purchaser campaigns", "Brand education",
            "Product education", "Interactive Quick campaign", "Founder Content",
        ],
        flows=["Welcome Flow", "Referral Flow"],
        qualifying_questions=[
            "Do you currently have a website pop-up?",
            "What's your current list size and monthly growth rate?",
            "How many new subscribers are you gaining per month vs. losing?",
            "What's your target list size for your revenue goals?",
            "How does your current growth rate compare to 6-12 months ago?",
            "How much are you spending on paid ads to drive email signups?",
            "Are you running any referral programs or partnerships for list building?",
        ],
    ),
    RuleDefinition(
        rule_id="AUD-02",
        category="audience_growth",
        description="Low attributed email revenue",
        metric="attributed_revenue_pct",
        threshold_operator="lt",
        threshold_value=0.28,
        base_weight=23,
        campaigns=[
            "Product launch campaigns", "Sale campaigns",
            "Product Recommendation Campaigns", "Bundle deal campaigns",
            "Seasonal collection campaigns", "Loyalty campaigns",
            "Brand education", "Product education",
            "Cross-sell campaigns", "Up-sell campaigns",
        ],
        flows=[
            "Birthday Flow", "Welcome Flow", "Browse Abandon",
            "Cart Abandon", "Checkout Abandon",
            "Review Request Flow", "Post-Purchase",
        ],
        creative_notes="Clear Revenue Driving CTAs, Leverage Social Proof",
        data_source="Shopify discount usage",
        qualifying_questions=[
            "Which types of email campaigns drive the highest revenue?",
            "How often are you sending revenue-driving campaigns vs. nurture content?",
            "Are you personalizing offers based on customer purchase history?",
            "How long does it typically take for a new subscriber to make their first purchase?",
            "Are you tracking revenue from automated flows vs. campaigns?",
        ],
    ),
    RuleDefinition(
        rule_id="AUD-03",
        category="audience_growth",
        description="High list churn — unsubscribe rate too high",
        metric="unsubscribe_rate",
        threshold_operator="gt",
        threshold_value=0.01,
        base_weight=10,
        campaigns=[
            "Survey/Feedback", "Interactive Quiz campaigns",
            "Educational content campaigns", "Sale Campaigns", "Founder Content",
        ],
        flows=[
            "Sunset Flow (re-engagement before removal)",
            "Content Preference Flow", "Winback",
        ],
        data_source="Shopify discount usage",
        qualifying_questions=[
            "At what point in the subscriber lifecycle do you see the highest churn?",
            "Are there specific campaigns or email types that drive higher unsubscribes?",
            "Do you see seasonal patterns in your churn rates?",
            "How does churn correlate with your email frequency?",
            "Do you have a preference center to let people customize their experience?",
        ],
    ),
    RuleDefinition(
        rule_id="AUD-04",
        category="audience_growth",
        description="Low RPR (audience growth angle)",
        metric="revenue_per_recipient",
        threshold_operator="lt",
        threshold_value=0.25,
        base_weight=12,
        campaigns=[
            "Product pairing suggestion campaigns", "Seasonal refresh campaigns",
            "Complete Your Collection series", "Customer lifestyle campaigns",
            "Gamified challenge campaigns (e.g. 60 day challenge)",
        ],
        flows=[
            "Replenishment Reminder Flow", "Cross-sell Flow",
            "Loyalty Milestone Flow", "Post-Purchase",
        ],
        data_source="Klaviyo RPR",
        qualifying_questions=[
            "Have you changed your email send schedule?",
            "What percentage of customers make 3+ purchases?",
            "How long do your products typically last customers?",
            "Are you sending replenishment reminders based on usage timelines?",
            "Which products have the highest repurchase rates?",
        ],
    ),
    RuleDefinition(
        rule_id="AUD-05",
        category="audience_growth",
        description="Declining total sales (audience growth signal)",
        metric="revenue_yoy_change",
        threshold_operator="lt",
        threshold_value=-0.15,
        base_weight=21,
        campaigns=[
            "Sale", "Product features", "Seasonal campaigns",
            "Brand Education", "VIP Campaigns", "Loyalty Campaigns",
            "Product Launches", "Cross-sell/Upsell",
        ],
        flows=[
            "Welcome Flow", "Browse Abandon", "Cart Abandon",
            "Checkout Abandon", "Upsell Flow", "Post-Purchase", "Winback",
        ],
        creative_notes="Prominent product shots",
        data_source="Gross Revenue",
        qualifying_questions=[
            "What happened in this month last year?",
            "Did you change any other marketing channels?",
            "Are you open to a sale?",
        ],
    ),
    RuleDefinition(
        rule_id="AUD-06",
        category="audience_growth",
        description="Weak VIP program — few VIP customers",
        metric="vip_pct_of_list",
        threshold_operator="lt",
        threshold_value=0.05,
        base_weight=10,
        campaigns=[
            "VIP Sales", "VIP member appreciation campaigns",
            "Product Education", "Product recommendation campaigns",
            "Interactive Quiz campaigns",
        ],
        flows=[
            "VIP Onboarding Flow", "VIP Cross-Sell Flow",
            "Loyalty Program Flow", "Points Redemption Reminder Flow",
        ],
        qualifying_questions=[
            "What percentage of your customers are enrolled in your VIP/loyalty program?",
            "What's the engagement rate within your loyalty program?",
            "How do VIP customers perform vs. non-VIP customers (LTV, purchase frequency, AOV)?",
            "What exclusive benefits do VIP members receive?",
            "Are you giving your VIPs early access to launches and sales?",
        ],
    ),
    RuleDefinition(
        rule_id="AUD-07",
        category="audience_growth",
        description="Low social media engagement",
        metric="social_engagement_score",
        threshold_operator="lt",
        threshold_value=0.02,
        base_weight=10,
        campaigns=["Social giveaway campaigns", "Influencer collaboration highlights"],
        flows=["Welcome Flow social links", "Post-Purchase Share Flow"],
        data_source="Social Platforms",
        qualifying_questions=[
            "Are you posting consistently across your active social channels?",
            "Do your emails encourage social sharing and following?"
        ],
    ),
    RuleDefinition(
        rule_id="AUD-08",
        category="audience_growth",
        description="High customer acquisition cost",
        metric="customer_acquisition_cost",
        threshold_operator="gt",
        threshold_value=40.0,
        base_weight=15,
        campaigns=["High margin bundles", "Brand education", "Conversion rate optimization"],
        flows=["Welcome Flow", "Browse Abandon Flow"],
        data_source="Meta/Google Ads",
        qualifying_questions=[
            "Has your ad spend efficiency dropped recently?",
            "Are you heavily reliant on paid acquisition vs organic channels?"
        ],
    ),
    RuleDefinition(
        rule_id="AUD-09",
        category="audience_growth",
        description="Low referral program engagement",
        metric="referral_rate",
        threshold_operator="lt",
        threshold_value=0.015,
        base_weight=10,
        campaigns=["Refer a Friend Promos", "Double-sided rewards campaigns"],
        flows=["Referral Flow", "Loyalty Milestones"],
        data_source="Referral App",
        qualifying_questions=[
            "Is the referral incentive compelling for both the advocate and the friend?",
            "Are you actively promoting the referral program?"
        ],
    ),
]


# ══════════════════════════════════════════════════════
# 3.4  EMAIL ENGAGEMENT RULES  (7 rules, 15%)
# ══════════════════════════════════════════════════════

EMAIL_ENGAGEMENT_RULES: List[RuleDefinition] = [
    RuleDefinition(
        rule_id="OPEN-01",
        category="email_engagement",
        description="Low email open rate",
        metric="open_rate_avg",
        threshold_operator="lt",
        threshold_value=0.30,
        base_weight=5,
        campaigns=[
            "FOMO campaigns", "Sale campaigns", "Founder Content",
            "Product Education", "Brand Education", "Testimonial Campaigns",
        ],
        flows=[
            "Welcome Flow", "Browse Abandon Flow", "Cart Abandon Flow",
            "Checkout Abandon Flow", "Winback Flow", "Post-Purchase Flow",
            "Order Confirmation Flow", "Review Request Flow", "VIP Onboarding Flow",
        ],
        creative_notes="Strong subject lines, Test emojis, Send-time optimization",
        data_source="Klaviyo Open Rate",
        qualifying_questions=[
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
    ),
    RuleDefinition(
        rule_id="OPEN-02",
        category="email_engagement",
        description="Low email click rate (email engagement angle)",
        metric="click_rate_avg",
        threshold_operator="lt",
        threshold_value=0.008,
        base_weight=15,
        campaigns=[
            "Newsletter", "New arrival announcement campaigns",
            "Seasonal trend campaigns", "Flash sale campaigns",
            "Brand education campaign", "Testimonials campaign",
        ],
        flows=[
            "Birthday Flow", "Welcome Flow", "Browse Abandon",
            "Cart Abandon", "Checkout Abandon", "Review Request Flow",
        ],
        creative_notes="Move CTA Up, Focused Email",
        data_source="Shopify repeat rate, LTV",
        qualifying_questions=[
            "Have you tested any segmentation?",
            "Do click rates differ by segment?",
            "Have you changed anything in email creative strategy recently?",
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-03",
        category="email_engagement",
        description="Low website CVR (email engagement angle)",
        metric="website_cvr",
        threshold_operator="lt",
        threshold_value=0.016,
        base_weight=20,
        campaigns=[
            "FOMO campaigns", "Bundle offer campaigns",
            "Sale campaigns", "Testimonial campaigns",
        ],
        flows=[
            "VIP Flow", "Browse Abandon", "Cart Abandon",
            "Checkout Abandon", "Post-purchase", "Order upcoming",
        ],
        creative_notes="Move CTA Up, Focused Email, Onsite Pop-Ups",
        data_source="Shopify CVR",
        qualifying_questions=[
            "Did anything change on the website recently?",
            "What happens when someone clicks from your email to your website?",
            "How aligned is your email messaging with your landing page messaging?",
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-04",
        category="email_engagement",
        description="Low RPR (email engagement angle)",
        metric="revenue_per_recipient",
        threshold_operator="lt",
        threshold_value=0.18,
        base_weight=15,
        campaigns=[
            "Product pairing suggestion campaigns", "Seasonal refresh campaigns",
            "Complete Your Collection series", "Customer lifestyle campaigns",
        ],
        flows=[
            "Replenishment Reminder Flow", "Cross-sell Flow",
            "Loyalty Milestone Flow", "Surprise and Delight Flow",
        ],
        data_source="Klaviyo RPR",
        qualifying_questions=[
            "Have you changed your email send schedule?",
            "What percentage of your customers make a second purchase within 90 days?",
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-05",
        category="email_engagement",
        description="Dropping email deliverability rate",
        metric="deliverability_rate",
        threshold_operator="lt",
        threshold_value=0.68,
        base_weight=10,
        campaigns=[
            "We miss you engagement campaigns", "List preference campaigns",
            "Feedback collection campaigns", "Highest-engagement campaigns",
            "VIP campaigns",
        ],
        flows=["Re-engagement Flow", "Sunset Flow", "Welcome Flow"],
        qualifying_questions=[
            "Which email providers are showing the worst deliverability?",
            "How many emails have you been sending a month over the last 6 months?",
            "What's your current bounce rate, and how has it changed recently?",
            "When did you last clean your email list?",
            "What's your unsubscribe rate, and has it increased recently?",
            "Have you increased your email frequency recently?",
            "Are you sending to purchased lists or only opted-in subscribers?",
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-06",
        category="email_engagement",
        description="Low attributed email revenue (email angle)",
        metric="attributed_revenue_pct",
        threshold_operator="lt",
        threshold_value=0.30,
        base_weight=27,
        campaigns=[
            "Product launch campaigns", "Sale campaigns",
            "Bundle deal campaigns", "Seasonal collection campaigns",
            "Loyalty campaigns", "Brand education", "Product education",
            "Newsletter", "Cross-sell campaigns", "Up-sell campaigns",
        ],
        flows=[
            "Birthday Flow", "Browse Abandon", "Cart Abandon",
            "Checkout Abandon", "Review Request Flow", "Post-Purchase",
        ],
        creative_notes="Clear Revenue Driving CTAs, Leverage Social Proof",
        data_source="Shopify discount usage",
        qualifying_questions=[
            "Which types of email campaigns drive the highest revenue?",
            "How often are you sending revenue-driving campaigns vs. nurture content?",
            "Are you personalizing offers based on customer purchase history?",
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-07",
        category="email_engagement",
        description="Low overall engagement rate (email angle)",
        metric="engagement_rate",
        threshold_operator="lt",
        threshold_value=0.15,
        base_weight=8,
        campaigns=[
            "Survey/Feedback", "Interactive Quiz campaigns",
            "Educational content campaigns", "Sale campaigns",
        ],
        flows=["Winback", "Re-engagement Flow"],
        qualifying_questions=[
            "How many emails have you been sending a month over the last 6 months?",
            "What segments have you been targeting?",
            "Which emails or campaigns get the highest engagement?",
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-08",
        category="email_engagement",
        description="High spam complaint rate",
        metric="spam_complaint_rate",
        threshold_operator="gt",
        threshold_value=0.001,
        base_weight=15,
        campaigns=["Update email preferences", "Quality content over frequency promos"],
        flows=["Sunset Flow", "Preference Center update Flow"],
        data_source="Klaviyo deliverability",
        qualifying_questions=[
            "Are you making it difficult to unsubscribe?",
            "Are you sending to unengaged profiles that haven't opened an email in 6 months?"
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-09",
        category="email_engagement",
        description="Low Click-to-Open Rate (CTOR)",
        metric="click_to_open_rate",
        threshold_operator="lt",
        threshold_value=0.05,
        base_weight=15,
        campaigns=["Clear Value Proposition", "Single strong CTA campaigns"],
        flows=["Welcome Flow", "Promotional flows"],
        creative_notes="Make the email content match the subject line promise. Ensure one primary CTA.",
        data_source="Klaviyo reporting",
        qualifying_questions=[
            "Are your subject lines clickbaity but the email lacks substance?",
            "Is the call to action clear and above the fold?"
        ],
    ),
    RuleDefinition(
        rule_id="OPEN-10",
        category="email_engagement",
        description="Low SMS opt-in rate",
        metric="sms_optin_rate",
        threshold_operator="lt",
        threshold_value=0.03,
        base_weight=10,
        campaigns=["Exclusive SMS drops", "SMS-only VIP discounts"],
        flows=["Email to SMS transition flow", "Post-Purchase SMS collection"],
        data_source="Klaviyo SMS",
        qualifying_questions=[
            "Does your email pop-up have an SMS step?",
            "What value do subscribers get for giving their phone number?"
        ],
    ),
]


# ══════════════════════════════════════════════════════
# MASTER REGISTRY — All 29 rules combined
# ══════════════════════════════════════════════════════

ALL_RULES: List[RuleDefinition] = (
    REVENUE_RULES
    + AUDIENCE_ENGAGEMENT_RULES
    + AUDIENCE_GROWTH_RULES
    + EMAIL_ENGAGEMENT_RULES
)

RULES_BY_ID: Dict[str, RuleDefinition] = {r.rule_id: r for r in ALL_RULES}

RULES_BY_CATEGORY: Dict[str, List[RuleDefinition]] = {
    "revenue":             REVENUE_RULES,
    "audience_engagement": AUDIENCE_ENGAGEMENT_RULES,
    "audience_growth":     AUDIENCE_GROWTH_RULES,
    "email_engagement":    EMAIL_ENGAGEMENT_RULES,
}


# ── Public API ───────────────────────────────────────

def get_all_rules() -> List[RuleDefinition]:
    """Return all 29 registered rules."""
    return ALL_RULES


def get_rule_by_id(rule_id: str) -> RuleDefinition | None:
    """Lookup a rule by its ID."""
    return RULES_BY_ID.get(rule_id)


def get_rules_by_category(category: str) -> List[RuleDefinition]:
    """Return all rules in a category."""
    return RULES_BY_CATEGORY.get(category, [])
