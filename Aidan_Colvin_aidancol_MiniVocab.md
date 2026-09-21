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
| **T01** | Boxed Warning | Assigned if the label contains an official FDA Boxed Warning section in `warnings` highlighting severe risks[cite: 1]. **Exclusion:** Do not assign for standard warning text that lacks an official boxed header. | Black Box Warning, FDA Boxed Warning, Severe Risk Alert |
| **T02** | Oral Route | Assigned if the harmonized `route` field specifies the drug is taken by mouth[cite: 1, 2]. **Exclusion:** Do not assign for injectable, topical, ophthalmic, or inhaled routes. | Oral Administration, By Mouth, Per Os (PO) |
| **T03** | Pediatric Indication | Assigned if `indications_and_usage` explicitly approves the drug for patients under 18 years old[cite: 1]. **Exclusion:** Do not assign if the label states pediatric safety is not established. | Pediatric Use, Pediatric Safety, Children's Usage |
| **T04** | High-Frequency Adverse Effect | Assigned if `adverse_reactions` lists side effects with a clinical trial frequency of 5% or greater[cite: 1]. **Exclusion:** Do not assign for rare adverse events or post-marketing reports with unknown frequency. | Common Side Effects, Frequent Side Effects |
| **T05** | Pharmacologic Class | Assigned if the harmonized `pharm_class_epc` or `pharm_class_moa` field categorizes the drug by its established mechanism[cite: 2, 3, 4]. **Exclusion:** Do not assign if chemical class fields are blank in openFDA. | Established Pharmacologic Class, Drug Mechanism, Pharm Class |
| **T06** | Renal Dose Adjustment | Assigned if the label includes specific dosage modifications for patients with renal impairment. **Exclusion:** Do not assign for general warnings about kidney toxicity that lack specific dosing changes. | Kidney Dose Adjustment, Renal Impairment Guidelines |
| **T07** | Controlled Substance | Assigned if the `pharm_class_cs` field lists a DEA schedule rating indicating abuse potential[cite: 2, 3, 4]. **Exclusion:** Do not assign for non-controlled medications. | Scheduled Drug, DEA Scheduled, Controlled Medication |
| **T08** | Single Active Ingredient | Assigned if the `substance_name` field contains exactly one chemical entity[cite: 1, 2, 3]. **Exclusion:** Do not assign for combination drugs with multiple active ingredients. | Monotherapy, Single-Ingredient Product, Standalone Drug |
| **T09** | Brand Name Product | Assigned if the `brand_name` field contains a proprietary trademarked name[cite: 1, 2]. **Exclusion:** Do not assign for generic-only labels. | Proprietary Drug, Trade Name, Branded Medication |
