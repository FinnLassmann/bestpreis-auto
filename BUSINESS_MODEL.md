# Business Model: White-Label Dealer Storefronts for EU-Reimport

## One-Liner

Modern, conversion-optimized white-label websites for EU-Reimport car dealers —
sitting on top of their existing DMS (Autrado/audaris), not replacing it.

---

## Problem

EU-Reimport dealers in Germany use platforms like **Autrado** (€149-489/mo) or
**audaris** for inventory management AND their website. The result:

- **Generic templates** — every Autrado dealer site looks identical
- **Poor mobile UX** — most buyers come from phones (MyDealz, Google, WhatsApp links)
- **No price transparency** — the #1 reason people buy EU-Reimport (savings vs. UVP) is buried or absent
- **Weak SEO** — shared templates, thin content, no structured data
- **No conversion optimization** — sites are inventory catalogs, not sales funnels

Dealers know their sites are bad. They lose leads to mobile.de/AutoScout24 — and
pay listing fees there instead of converting on their own domain.

---

## Solution

A **white-label storefront** that:

1. **Pulls inventory** from the dealer's existing DMS (Autrado API, audaris API, or CSV/Excel import)
2. **Displays it beautifully** — mobile-first, fast, modern React frontend
3. **Highlights savings** — UVP vs. dealer price, percentage saved, prominently displayed
4. **Captures leads** — integrated inquiry forms with email/WhatsApp notifications
5. **Runs on their domain** — `www.eu-mayer.de`, not `eu-mayer.autrado.de`

We do NOT replace Autrado/audaris. We replace the **frontend layer only**.
Dealers keep their DMS, their B2B marketplace access, their portal exports.
They just get a better shop window.

---

## Target Customer

**Tier 1 (launch):** Small EU-Reimport dealers (5-50 vehicles)
- Currently on Autrado with the default template
- 1-5 employees, owner-operated
- No in-house tech/marketing team
- Examples: EU-Mayer (Aschaffenburg), similar operations nationwide

**Tier 2 (growth):** Mid-size EU-Reimport specialists (50-500 vehicles)
- Multiple brands, possibly multiple locations
- Already paying for mobile.de/AutoScout24 listings
- Want to reduce dependency on marketplaces
- Examples: APEG (Allgäu), similar regional players

**Tier 3 (later):** Brand-affiliated dealers wanting a better web presence
- Currently on audaris or OEM-mandated platforms
- Higher willingness to pay, but longer sales cycles

---

## Competitive Landscape

| Provider       | What They Do                        | Price        | Weakness                           |
|----------------|-------------------------------------|--------------|------------------------------------|
| **Autrado**    | DMS + website + B2B marketplace     | €149-489/mo  | Generic templates, poor UX, bundled lock-in |
| **audaris**    | DMS + website + CRM (upmarket)      | On request   | Enterprise-focused, expensive, complex |
| **Symfio**     | DMS + website                       | On request   | Small player, limited templates    |
| **CarCopy**    | Modular DMS                         | Modular      | No real website product            |
| **Carcuro**    | Budget DMS                          | €480/year    | No website builder                 |
| **Us**         | **Website only** (plugs into DMS)   | €99-199/mo   | New, unproven, no DMS              |

**Key positioning:** We're the only one that decouples the website from the DMS.
Everyone else bundles them. This is our wedge.

---

## Pricing

| Plan        | Price/mo | Includes                                           |
|-------------|----------|-----------------------------------------------------|
| **Starter** | €99      | White-label site, up to 50 vehicles, lead forms, basic SEO |
| **Pro**     | €199     | Up to 500 vehicles, analytics dashboard, WhatsApp integration, priority support |
| **Custom**  | On request | Multi-location, custom design, API access          |

No setup fee. Month-to-month. This removes friction — dealers can try risk-free.

**Revenue target:** 50 dealers × €150 avg = **€7,500 MRR** within 12 months.

---

## Go-to-Market

### Phase 1: Free Pilot (Month 1-2)
- Pick 3 dealers with the worst websites (easy to find)
- Build their storefront for free
- Measure: lead conversion rate vs. old site, page speed, mobile usability
- Get testimonials and case study data

### Phase 2: Cold Outreach (Month 3-4)
- Use pilot data to pitch: "EU-Mayer got 3x more leads after switching"
- Target Autrado dealers specifically (identifiable by template/URL patterns)
- LinkedIn + cold email to dealer owners
- Offer: first month free, cancel anytime

### Phase 3: Partnerships (Month 5+)
- Approach Autrado about becoming an official "premium frontend" partner
- List on automotive software directories
- Content marketing: "Why your EU-Reimport site loses customers" blog/guides

---

## Technical Architecture (Adjusted for SaaS)

```
┌─────────────────────────────────────────────┐
│              Dealer's Domain                 │
│         (e.g. www.eu-mayer.de)              │
├─────────────────────────────────────────────┤
│          White-Label Frontend               │
│     React + Vite + TailwindCSS              │
│     (themed per dealer: logo, colors)       │
├─────────────────────────────────────────────┤
│              Backend API                     │
│           FastAPI (multi-tenant)             │
│     /api/{dealer_slug}/vehicles             │
│     /api/{dealer_slug}/leads                │
├─────────────────────────────────────────────┤
│            PostgreSQL                        │
│     (tenant-aware: dealer_id on all tables) │
├─────────────────────────────────────────────┤
│          Inventory Sync Layer               │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Autrado  │ │ audaris  │ │ CSV/Excel   │ │
│  │   API    │ │   API    │ │   Upload    │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
└─────────────────────────────────────────────┘
```

### What Changes from Current Prototype

| Current (aggregator)          | New (white-label SaaS)                  |
|-------------------------------|-----------------------------------------|
| Single site, multiple sources | Multiple sites, one source each         |
| We own the domain             | Dealer owns the domain                  |
| Our brand                     | Dealer's brand (logo, colors, fonts)    |
| Scraping without permission   | API integration with permission         |
| No revenue model              | SaaS subscription                       |
| Legal grey area               | Fully legitimate                        |

### Key Technical Additions Needed

1. **Multi-tenancy** — `dealer_id` on all DB tables, tenant resolution via domain/subdomain
2. **Theming engine** — per-dealer colors, logo, favicon, fonts (CSS variables)
3. **Inventory sync** — scheduled pull from Autrado/audaris APIs (replace scraping)
4. **Dealer admin panel** — manage inventory, view leads, update settings
5. **Lead notifications** — email + WhatsApp webhook on new inquiry

---

## Why This Beats the Aggregator Play

| Factor              | Aggregator                  | White-Label SaaS           |
|---------------------|-----------------------------|----------------------------|
| Revenue             | Unclear (ads? leads?)       | SaaS subscriptions (clear) |
| Customer            | Consumers (fickle)          | Dealers (sticky)           |
| Competition         | AutoScout24 (impossible)    | Autrado frontend (beatable)|
| Legal risk          | Scraping without consent    | API with dealer agreement  |
| Moat                | None (data is public)       | Switching cost + relationships |
| Unit economics      | Need millions of users      | Need 50 dealers            |
| Path to marketplace | Would need to start over    | Can layer on top later     |

---

## Open Questions

- [ ] Does Autrado have a public API, or do we need to reverse-engineer/partner?
- [ ] What's the actual conversion rate on current Autrado template sites?
- [ ] Would dealers pay for this alongside their Autrado subscription, or only instead?
- [ ] How do we handle UVP data? (DAT.de API? OEM configurators? Manual entry?)
- [ ] DNS/hosting: do we manage dealer domains, or just provide a CNAME?

---

## Next Steps

1. Validate with 1-2 real dealers: would they pay €99-199/mo for a better site?
2. Build a single white-label demo (pick the worst Autrado site we can find)
3. Adapt current codebase: add multi-tenancy, theming, dealer admin
4. Approach Autrado about API access / partnership
