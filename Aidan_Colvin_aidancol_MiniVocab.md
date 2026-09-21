# Aidan Colvin aidancol
# Mini Search Engine Project, Part II: Mini Controlled Vocabulary
Last Updated 09-21-2026

ADD BEFORE SUBMITTING 
If you received help from anyone, give them credits by listing their name(s) on the top of your submission. 
For each answer, indicate if you used AI for help. If yes, describe how it was used in reasonable detail.


### 1. Terms and definitions [50 points]

**Vocabulary Name:** Prescription Drug Label Attributes (PDLA)

| ID | Preferred Name | Definition & Boundaries | Alternative Names / Synonyms |
| :--- | :--- | :--- | :--- |
| **T01** | Boxed Warning | Assigned if the label contains an official FDA Boxed Warning section in `warnings` highlighting severe risks. **Exclusion:** Do not assign for standard warning text that lacks an official boxed header. | Black Box Warning, FDA Boxed Warning, Severe Risk Alert |
| **T02** | Oral Route | Assigned if the harmonized `route` field specifies the drug is taken by mouth. **Exclusion:** Do not assign for injectable, topical, ophthalmic, or inhaled routes. | Oral Administration, By Mouth, Per Os (PO) |
| **T03** | Pediatric Indication | Assigned if `indications_and_usage` explicitly approves the drug for patients under 18 years old. **Exclusion:** Do not assign if the label states pediatric safety is not established. | Pediatric Use, Pediatric Safety, Children's Usage |
| **T04** | High-Frequency Adverse Effect | Assigned if `adverse_reactions` lists side effects with a clinical trial frequency of 5% or greater. **Exclusion:** Do not assign for rare adverse events or post-marketing reports with unknown frequency. | Common Side Effects, Frequent Side Effects |
| **T05** | Pharmacologic Class | Assigned if the harmonized `pharm_class_epc` or `pharm_class_moa` field categorizes the drug by its established mechanism. **Exclusion:** Do not assign if chemical class fields are blank in openFDA. | Established Pharmacologic Class, Drug Mechanism, Pharm Class |
| **T06** | Renal Dose Adjustment | Assigned if the label includes specific dosage modifications for patients with renal impairment. **Exclusion:** Do not assign for general warnings about kidney toxicity that lack specific dosing changes. | Kidney Dose Adjustment, Renal Impairment Guidelines |
| **T07** | Controlled Substance | Assigned if the `pharm_class_cs` field lists a DEA schedule rating indicating abuse potential. **Exclusion:** Do not assign for non-controlled medications. | Scheduled Drug, DEA Scheduled, Controlled Medication |
| **T08** | Single Active Ingredient | Assigned if the `substance_name` field contains exactly one chemical entity. **Exclusion:** Do not assign for combination drugs with multiple active ingredients. | Monotherapy, Single-Ingredient Product, Standalone Drug |
| **T09** | Brand Name Product | Assigned if the `brand_name` field contains a proprietary trademarked name. **Exclusion:** Do not assign for generic-only labels. | Proprietary Drug, Trade Name, Branded Medication |
### 2. Organize your vocabulary [10 points]

**1) Structure of your vocabulary**
My vocabulary has relationships. It is organized in a hierarchy. It is not a flat list. 

* **T01: Boxed Warning**
  * **T06: Renal Dose Adjustment** (is a specific clinical safety restriction of Boxed Warning)
  * **T04: High-Frequency Adverse Effect** (is an aspect of safety risk under Boxed Warning)
* **T05: Pharmacologic Class**
  * **T07: Controlled Substance** (is a regulatory classification aspect of Pharmacologic Class)
* **T08: Single Active Ingredient**
  * **T09: Brand Name Product** (is a commercial form of Single Active Ingredient)
* **T02: Oral Route**
  * **T03: Pediatric Indication** (is an aspect of patient population targeting for Oral Route)

**Relationship Definitions:**
* **"is a specific clinical safety restriction of"**: The narrower term is a specific dosing rule. It derives from high-level safety warnings.
* **"is an aspect of safety risk under"**: The narrower term is a specific category of clinical risk. It is part of overall drug safety monitoring.
* **"is a regulatory classification aspect of"**: The narrower term is a legal DEA scheduling subgroup. It fits within broader drug mechanism classifications.
* **"is a commercial form of"**: The narrower term is a trademarked brand-name product. It is a specific version of the active chemical entity.
* **"is an aspect of patient population targeting for"**: The narrower term is a specific age group. It applies to a given administration route.

**2) Term assignment considerations**
Documents in this collection can be assigned multiple terms at the same time. The terms are not mutually exclusive. A single drug label can be tagged with T01, T02, T05, T08, and T09 simultaneously.

The vocabulary uses a hierarchy. If a document receives a narrower term, it automatically receives the broader term. Yes, if one searches for a broader term, a document with a narrower term will be returned. For example, searching for T05 (Pharmacologic Class) will return all documents tagged with T07 (Controlled Substance).
