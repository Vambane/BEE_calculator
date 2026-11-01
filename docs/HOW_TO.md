# How to use BEE Check

A short guide for a first pass on the calculator. This is a **planning estimate**, not a verification certificate — confirm figures with your B-BBEE verification agency.

---

## 1. Agree to the privacy notice

On **Profile**, read the short privacy notice and tick the consent box. Fields stay locked until you do. You can open the full [Privacy policy](?page=privacy) any time.

---

## 2. Fill in your company (Profile)

Enter what you know:

- **Company name** (optional, helps you recognise the session)
- **Sector** (defaults to Generic Codes)
- **Total revenue** — the app shows your size badge (EME / QSE / Generic) from that figure
- **Black ownership %**
- Optional bases (payroll, NPAT, procurement spend, headcount) if you will enter **rand** amounts later

### Loss or low profit

Supplier Development, Enterprise Development and SED targets are a % of NPAT. Statement 400 cl. 3.2.1 switches them to a **Turnover basis** when:

- there was **no profit last year** (enter a negative NPAT), or
- **no profit on average over five years** (enter the 5-year average), or
- the margin is **below a quarter of the industry norm** (enter the norm, from Stats SA)

Open **Loss or low profit?** under NPAT and enter what applies, plus the **qualifying year margin**: NPAT / Turnover of the most recent year in which the margin was at least a quarter of the norm. The app then scores those targets against a deemed NPAT of that margin x Turnover, and says so on Results. Without a qualifying year it uses a quarter of the industry norm, flagged as an interpretation to confirm with your verification agency.

Then use **Continue** at the bottom of the page.

---

## 3. Deemed level or full scorecard?

If the app puts you on a **deemed (affidavit) path** (common for **EMEs**, and for some **black-owned QSEs**), you only need **Profile** and **Results** — no element-by-element steps.

If you want a **points breakdown** instead (Ownership, Management, Skills, and the rest of the card), tick:

> **Score on the full scorecard even if a deemed (affidavit) level applies**

on Profile, then Continue. The sidebar will show the element steps for your size and sector. For an **EME** that ticks this, the measured steps follow the **QSE** scorecard.

Whether a deemed route applies to *your* facts is a verification question — this tool only follows the options you select.

---

## 4. Procurement from a supplier list

On **Enterprise & Supplier Development** (or **Preferential Procurement** on sector cards), open **Calculate procurement from a supplier list** instead of typing procurement percentages:

1. **Download template (CSV)**, fill it in Excel or Google Sheets (one row per supplier for the measurement year), save as CSV and upload it. You can also type or edit rows directly in the table.
2. Per supplier, take these from their certificate or affidavit:

| Column | What to enter |
|--------|---------------|
| **Spend (R)** | Total paid in the measurement year, net of credit notes |
| **B-BBEE level** | 1 to 8, or **NC** (or blank) if there is no valid certificate or affidavit |
| **Size** | EME, QSE, Large, or Unknown |
| **Black ownership %** / **Black women ownership %** | From the certificate (women cannot exceed black ownership) |
| **Designated group** | Yes if at least 51% owned by black people from designated groups (youth, people with disabilities, unemployed, rural, military veterans) |
| **Empowering supplier** | As stated on the certificate; blank means yes. EMEs always count as empowering (cl. 3.3.4) |
| **1.2x multiplier** | Yes if Statement 400 cl. 3.5 applies: a Supplier Development beneficiary, or a black-owned QSE/EME, with a 3-year contract; or a supplier at least 51% black owned or black women owned on flow-through |
| **TMPS exclusion** | Blank to include. Otherwise one of the codes below |

TMPS exclusions (Statement 400 cl. 5.4.2 and 6):

| Code | Exclude |
|------|---------|
| `tax` | Taxes, levies and municipal rates |
| `payroll` | Salaries, wages and director emoluments (pension and medical aid stay **in** TMPS) |
| `pass_through` | Third-party procurement your client records as its expense, not yours |
| `associated` | Investments in or loans to an Associated Enterprise |
| `contribution` | ED, SD or SED contributions (they score elsewhere) |
| `import` | Imports meeting cl. 6.5: no local production (capital goods for local value-add, or other imports backed by an ESD plan) |
| `state_monopoly` | An organ of state or public entity with a statutory or regulated monopoly |
| `other` | Anything else your verifier agrees to exclude |

3. The app shows **TMPS** (total spend less exclusions), the **recognised spend** for each procurement indicator (spend x the supplier's recognition %: Level 1 135%, Level 2 125%, Level 3 110%, Level 4 100%, Level 5 80%, Level 6 60%, Level 7 50%, Level 8 10%, no certificate 0%; x 1.2 where the multiplier is ticked), the **% of TMPS** and the points.
4. **Use these figures** sets TMPS in your Profile and fills the procurement indicators. Supplier and Enterprise Development stay as you entered them.
5. **Download this list (CSV)** saves your working so you can upload it next time. The list is kept for this session only.

How it counts: only Empowering Suppliers count, on every procurement measure; a designated-group supplier must also be at least 51% black owned. The same list works on every loaded scorecard (Generic, QSE and sector codes). You are responsible for the evidence behind exclusions and multipliers: confirm both with your verification agency.

---

## 5. Contributions at benefit factors

On **Enterprise & Supplier Development** and **Socio-Economic Development**, open **Value contributions with benefit factors**. Add one line per contribution at its face value, choose what it counts towards (e.g. Supplier Development) and its type. The app applies the gazetted factor:

| Type | ESD (Annexe 400(B)) | SED (Annexe 500(A)) |
|------|---------------------|---------------------|
| Grant, direct costs, discount beyond normal | 100% | 100% |
| Overhead costs (incl. dedicated staff) | 70% | 80% |
| Interest-free loan, no security | 70% of the outstanding amount | not SED |
| Standard loan | 50% of the outstanding amount | not SED |
| Guarantee | 50% (Generic, 2019); 3% on cards that follow the 2013 Codes | not SED |
| Minority equity investment | 70% | not SED |
| Loan at a lower interest rate | prime minus the actual rate, of the outstanding amount | not SED |
| Investment at a lower dividend | ordinary dividend rate minus the actual rate | not SED |
| Professional services free or at a discount | 60% | 80% |
| Employee time (monthly salary / 160 x hours) | 60% | 80% |

**Use these values** fills the indicators with the recognised totals (as rand, or as % of NPAT, which respects the Turnover basis above). Shorter payment periods to Supplier Development beneficiaries use their own formula: add them by hand. Sector codes may set their own factors; the app uses the generic ones and says so.

---

## 6. Moving around

| Control | What it does |
|---------|----------------|
| **Continue** / **Back** | Step forward or back. Continue runs the usual checks for that step. |
| **Sidebar step names** | Jump to a step you have **already reached**. Your inputs stay filled in. Steps you have not opened yet stay locked. |
| **Start over** | Clears this company’s inputs and any PDF unlock, then returns to Profile. Use this between two different companies in the same browser. It does **not** change the draft-rules toggle. |

Consent still applies: without the privacy tick, you cannot leave Profile.

---

## 7. Results and the PDF

**Results** shows your recognition level, points, and gaps (when you are on a scored path). Empty steps count as zero until you enter indicators or points.

To download a PDF of this session:

1. Enter a work email on the unlock form  
2. Continue — the email **unlocks the download** for this session  

We do **not** email the report in v1. An optional marketing tick does **not** add you to a mailing list.

---

## 8. Privacy and starting again

- [Privacy policy](?page=privacy) — what we collect for this session  
- **Start over** in the sidebar — clear the session and begin a new company  

Questions about scoring rules or your certificate belong with your verification agency, not this guide.
