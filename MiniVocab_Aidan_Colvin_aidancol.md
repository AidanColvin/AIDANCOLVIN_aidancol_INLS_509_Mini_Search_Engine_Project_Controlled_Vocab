# Aidan Colvin aidancol
# Mini Search Engine Project, Part II: Mini Controlled Vocabulary
Last Updated 09-21-2026

ADD BEFORE SUBMITTING 
If you received help from anyone, give them credits by listing their name(s) on the top of your submission. 
For each answer, indicate if you used AI for help. If yes, describe how it was used in reasonable detail.


**Help received:** UPDATE 

**AI use:** Stated at the end of each section.

---

## Part 1: Document Collection Foraging

### Prescription Medication

**Source:** [FDA Drug Labels](https://open.fda.gov/apis/drug/label/)

#### What the Collection Is About

These are FDA drug labels: the prescribing information that comes with a medication. Each record is one version of one label, submitted to FDA in Structured Product Labeling (SPL) format. One label can cover several products and package sizes (NDCs).

The main text sits in these fields:

* `indications_and_usage`: What the drug treats
* `adverse_reactions`: Side effects
* `warnings_and_cautions` (newer, PLR-format labels) or `warnings` (older labels): Precautions and risk information
* `boxed_warning`: The most serious risks, when the label has a boxed warning

Each record also carries structured attributes in its `openfda` object:

* `brand_name`
* `generic_name`
* `substance_name`
* `route`
* `pharm_class_epc`
* `application_number`

openFDA adds the `openfda` object only when applicable, so some labels lack it. Dosage form is described in text, in `dosage_forms_and_strengths`.

#### Who Will Search It

* Pharmacists and their supporting staff
* Healthcare providers (including doctors, nurses, and clinical staff)
* Patients and family members

#### Document Count & Scope Filtering

**Does it contain more than 50 documents?**
Yes. The Label endpoint holds 262,883 labels as of its September 18, 2026 update, prescription and over-the-counter combined. Human prescription labels are a large subset, about 54,000 by my Part 1 estimate.

To narrow down the dataset, the collection will be filtered by:

1. Keeping human prescription labels only (`openfda.product_type` is HUMAN PRESCRIPTION DRUG).
2. Restricting the records to a single drug class, matched on `openfda.pharm_class_epc`. Labels without the `openfda` object are left out, since they cannot be matched to a class.
3. Retaining only one label per active ingredient. A combination product counts as its own ingredient set, so combinations stay in the collection.

**AI use:** My original Part 1 used AI only for spelling, grammar, and phrasing. For this update, I used Claude (Anthropic) to check my field names against the openFDA Label field reference and openFDA's source mapping of label sections to fields, and to draft the updated field descriptions.

---

## 1. Terms and definitions [50 points]

**Vocabulary name:** Prescription Drug Label Attributes (PDLA)

PDLA tags the label properties that pharmacists, clinicians, and patients filter on: safety signals, route, patient group, dosing, DEA control, and product form. Each term is assigned by a fixed rule over named openFDA fields, so the same label always gets the same terms.

Two rules apply to every term:

* If a field a rule needs is missing, do not assign the term.
* A missing term means the label or its openFDA record did not show the condition. It does not prove the opposite.

### Overview

| ID | Preferred name | Broader term | Fields used |
| :--- | :--- | :--- | :--- |
| T01 | Boxed Warning | None | `boxed_warning` |
| T02 | Oral Route | None | `openfda.route` |
| T03 | Pediatric Indication | None | `indications_and_usage`, `pediatric_use` |
| T04 | High-Frequency Adverse Effect | None | `adverse_reactions`, `adverse_reactions_table` |
| T05 | Medication Guide | None | `spl_medguide` |
| T06 | Renal Dose Adjustment | T11 | `dosage_and_administration`, `use_in_specific_populations`, `precautions` |
| T07 | Controlled Substance | None | `controlled_substance` |
| T08 | Single Active Ingredient | None | `openfda.substance_name` |
| T09 | Brand Name Product | None | `openfda.brand_name`, `openfda.generic_name`, `openfda.application_number` |
| T10 | Schedule II Controlled Substance | T07 | `controlled_substance` |
| T11 | Organ Impairment Dose Adjustment | None | Assigned through T06 and T12 |
| T12 | Hepatic Dose Adjustment | T11 | `dosage_and_administration`, `use_in_specific_populations`, `precautions` |

### Term definitions

#### T01: Boxed Warning

* **ID:** T01
* **Preferred name:** Boxed Warning
* **Definition:** The label carries an official FDA boxed warning. This is the boxed statement at the top of the prescribing information that flags risks that can cause death or serious injury.
* **Assign when:** `boxed_warning` has text.
* **Do not assign when:** a serious risk appears only in `warnings_and_cautions` or `warnings` with no box.
* **Alternative names:** Black Box Warning, BBW, FDA Boxed Warning
* **Useful for:** finding the drugs with the most serious labeled risks.

#### T02: Oral Route

* **ID:** T02
* **Preferred name:** Oral Route
* **Definition:** The drug is taken by mouth.
* **Assign when:** the harmonized `openfda.route` field includes ORAL, even if other routes are also listed.
* **Do not assign when:** no listed route is ORAL, such as injectable, topical, ophthalmic, or inhaled products. Sublingual and buccal are separate routes in FDA's route list, so they do not get this term.
* **Alternative names:** Oral Administration, By Mouth, Per Os (PO)
* **Useful for:** patients and caregivers who want tablets, capsules, or liquids taken by mouth.

#### T03: Pediatric Indication

* **ID:** T03
* **Preferred name:** Pediatric Indication
* **Definition:** The label says the drug is safe and effective for at least one pediatric age group. For prescription drug labeling, FDA generally defines pediatric patients as birth to 16 years, meaning younger than 17.
* **Assign when:** `indications_and_usage` names pediatric patients for at least one indication, or `pediatric_use` states that safety and effectiveness have been established in a pediatric age group.
* **Do not assign when:** the label states that pediatric safety and effectiveness have not been established; the label contraindicates use in children; or the label gives pediatric study or drug-level data but no established use. A statement such as "not established in patients younger than 12" does not qualify by itself, because it does not say use was established at any pediatric age. Approval that starts at age 17 is adult approval under FDA's definition.
* **Alternative names:** Pediatric Approval, Approved for Children, Children's Usage
* **Not alternative names:** "Pediatric Use" and "Pediatric Safety." Pediatric Use is the label section that also holds "not established" statements, so it would match labels this term excludes.
* **Useful for:** pediatric clinicians and parents looking for drugs labeled for children.

#### T04: High-Frequency Adverse Effect

* **ID:** T04
* **Preferred name:** High-Frequency Adverse Effect
* **Definition:** At least one adverse reaction occurred in 10% or more of patients taking the drug in a clinical trial reported on the label. The 10% cutoff is the "very common" band (1 in 10 or more) in the CIOMS III frequency categories used in EU product labeling. US labels report percentages rather than these band names, so the cutoff is applied to the reported percentages.
* **Assign when:** `adverse_reactions` or `adverse_reactions_table` reports 10% or more for any reaction in the drug group of a clinical trial. The placebo rate does not change the decision.
* **Do not assign when:** every reported rate is below 10%; reactions come only from postmarketing reports with unknown frequency; or the label lists reactions without percentages.
* **Alternative names:** Very Common Side Effects, Very Common Adverse Reactions, High-Incidence Side Effects
* **Not alternative names:** "Common Side Effects" and "Frequent Side Effects." In CIOMS III, common and frequent both mean 1% to under 10%.
* **Useful for:** patients and prescribers weighing how likely side effects are before starting a drug.

#### T05: Medication Guide

* **ID:** T05
* **Preferred name:** Medication Guide
* **Definition:** The label includes an FDA Medication Guide. This is a plain-language patient handout that FDA requires for certain drugs with serious risks. Under 21 CFR Part 208, it must be given to the patient when the drug is dispensed.
* **Assign when:** `spl_medguide` has text.
* **Do not assign when:** the only patient material is a patient package insert (`spl_patient_package_insert`) or patient counseling text. These are different documents.
* **Alternative names:** MedGuide, Med Guide, FDA Medication Guide
* **Useful for:** pharmacists who must hand out the guide at pickup, and patients who want a plain-language summary of a drug's main risks.

#### T06: Renal Dose Adjustment

* **ID:** T06
* **Preferred name:** Renal Dose Adjustment
* **Broader term:** T11: Organ Impairment Dose Adjustment
* **Definition:** The label gives specific dosage modifications for patients with renal impairment.
* **Assign when:** dosing text in `dosage_and_administration`, `use_in_specific_populations`, or `precautions` (older-format labels) ties a kidney function level to a lower dose, a longer time between doses, or a lower maximum dose. Kidney function levels include creatinine clearance or eGFR ranges; mild, moderate, or severe renal impairment; and dialysis.
* **Do not assign when:** the label gives general warnings about kidney toxicity with no dose change; the label says no dose change is needed; or the label only says to avoid the drug, or that it is contraindicated, below a kidney function level. That tells the user not to use the drug, not how to dose it.
* **Alternative names:** Kidney Dose Adjustment, Renal Dosing, Renal Impairment Dosing
* **Useful for:** pharmacists and prescribers dosing patients with chronic kidney disease.

#### T07: Controlled Substance

* **ID:** T07
* **Preferred name:** Controlled Substance
* **Definition:** The DEA controls the drug under the Controlled Substances Act because of its potential for abuse or dependence.
* **Assign when:** `controlled_substance`, the Controlled Substance subsection of the label, names DEA Schedule II, III, IV, or V.
* **Do not assign when:** `controlled_substance` is missing or says the drug is not scheduled; or the label discusses abuse or dependence in `drug_abuse_and_dependence`, `abuse`, or `dependence` but names no schedule.
* **Field note:** `openfda.pharm_class_cs` is not used. "CS" there means chemical structure, not controlled substance.
* **Alternative names:** Scheduled Drug, DEA Scheduled, Controlled Medication
* **Useful for:** pharmacists handling storage, record-keeping, and refill rules, and prescribers screening for abuse risk.

#### T08: Single Active Ingredient

* **ID:** T08
* **Preferred name:** Single Active Ingredient
* **Definition:** The product contains exactly one active ingredient.
* **Assign when:** `openfda.substance_name` has exactly one entry. A salt form counts as one ingredient, since it appears as one entry, such as METFORMIN HYDROCHLORIDE.
* **Do not assign when:** the field has two or more entries, meaning a combination drug such as sacubitril and valsartan.
* **Alternative names:** Single-Ingredient Product, Single-Entity Drug
* **Not an alternative name:** "Monotherapy." It means treating a patient with one drug, not a product with one ingredient. A single-ingredient drug can still be part of combination therapy.
* **Useful for:** separating plain products from combination products when checking a patient's drug list for duplicate ingredients.

#### T09: Brand Name Product

* **ID:** T09
* **Preferred name:** Brand Name Product
* **Definition:** The product is sold under a proprietary trademarked name rather than its generic name.
* **Assign when:** `openfda.brand_name` differs from `openfda.generic_name` (ignoring case).
* **Do not assign when:** `brand_name` repeats the generic name, or `openfda.application_number` starts with ANDA, the approval pathway for generics. If `application_number` is missing, the name check decides.
* **Why the name check:** openFDA copies `brand_name` from the proprietary name in the NDC Directory, and some products list their generic name there. A filled `brand_name` alone does not prove a trademark.
* **Alternative names:** Proprietary Drug, Trade Name, Branded Medication
* **Useful for:** users who know a drug only by its brand name, and anyone comparing brand and generic labels.

#### T10: Schedule II Controlled Substance

* **ID:** T10
* **Preferred name:** Schedule II Controlled Substance
* **Broader term:** T07: Controlled Substance
* **Definition:** The DEA places the drug in Schedule II, the most restricted schedule for drugs with an accepted medical use. Examples include oxycodone, fentanyl, and amphetamine.
* **Assign when:** `controlled_substance` names Schedule II (CII).
* **Do not assign when:** the schedule is III, IV, or V.
* **Alternative names:** C-II, CII, Schedule 2
* **Useful for:** pharmacists and patients, since Schedule II prescriptions cannot be refilled.

#### T11: Organ Impairment Dose Adjustment

* **ID:** T11
* **Preferred name:** Organ Impairment Dose Adjustment
* **Narrower terms:** T06: Renal Dose Adjustment, T12: Hepatic Dose Adjustment
* **Definition:** The label gives specific dosage modifications for patients with reduced kidney or liver function.
* **Assign when:** the label gets T06 or T12. T11 has no rule of its own.
* **Do not assign when:** the dose change is for another reason, such as age, weight, or a drug interaction, or for another organ, such as the heart.
* **Alternative names:** Organ Function Dose Adjustment, Kidney or Liver Dose Adjustment
* **Useful for:** one filter that answers whether a drug needs a dose change when the kidneys or liver are impaired.

#### T12: Hepatic Dose Adjustment

* **ID:** T12
* **Preferred name:** Hepatic Dose Adjustment
* **Broader term:** T11: Organ Impairment Dose Adjustment
* **Definition:** The label gives specific dosage modifications for patients with hepatic impairment.
* **Assign when:** dosing text in `dosage_and_administration`, `use_in_specific_populations`, or `precautions` (older-format labels) ties a liver function level to a lower dose, a longer time between doses, or a lower maximum dose. Liver function levels include Child-Pugh class A, B, or C, and mild, moderate, or severe hepatic impairment.
* **Do not assign when:** the label warns about liver injury but gives no dose change; the label says no dose change is needed; or the label only says to avoid the drug, or that it is contraindicated, at a liver function level.
* **Alternative names:** Liver Dose Adjustment, Hepatic Dosing, Hepatic Impairment Dosing
* **Useful for:** dosing patients with cirrhosis or other liver disease.

**AI use:** I chose the vocabulary's focus and drafted nine terms. I used Claude (Anthropic) to check each term's rule against the openFDA Label field reference and FDA labeling guidance, and to draft the final definitions, boundaries, and alternative names. Claude supplied the field mappings for Boxed Warning and Controlled Substance, proposed T05 (Medication Guide) and T10 to T12, and set T04's cutoff from the CIOMS III frequency categories.

---

## 2. Organize your vocabulary [10 points]

### 1) Structure of your vocabulary

My vocabulary has relationships. It is a shallow hierarchy, not a flat list: nine top-level terms, with three narrower terms under two of them. Every link uses one relationship, "is a type of."

* **T01: Boxed Warning**
* **T02: Oral Route**
* **T03: Pediatric Indication**
* **T04: High-Frequency Adverse Effect**
* **T05: Medication Guide**
* **T07: Controlled Substance**
  * **T10: Schedule II Controlled Substance** (is a type of Controlled Substance)
* **T08: Single Active Ingredient**
* **T09: Brand Name Product**
* **T11: Organ Impairment Dose Adjustment**
  * **T06: Renal Dose Adjustment** (is a type of Organ Impairment Dose Adjustment)
  * **T12: Hepatic Dose Adjustment** (is a type of Organ Impairment Dose Adjustment)

**Relationship definition:**

* **"is a type of":** every label that meets the narrower term's definition also meets the broader term's definition. The narrower term picks out a subset. Schedule II is one of the DEA schedules, so every Schedule II label is a controlled substance label. A renal dose adjustment is one kind of organ impairment dose adjustment, so every T06 label is a T11 label.

**Why the top-level terms are not linked:**

Each top-level term describes a different property of a label: a safety signal (T01, T04), patient information (T05), route (T02), patient group (T03), dosing (T11), DEA control (T07), or product form (T08, T09). None implies another. The gabapentin label gives renal dose changes but has no boxed warning. Entresto is a brand product with two active ingredients. Linking such terms would tag labels with terms whose definitions they fail.

### 2) Term assignment considerations

**Are the terms mutually exclusive?** No. Documents in this collection can be assigned multiple terms at the same time. A label gets every term whose definition it meets. For example, the OxyContin (oxycodone extended-release tablets) label meets T01, T02, T05, T07, T08, T09, and T10.

**Does a narrower term bring its broader term?** Yes. If a document receives a narrower term, it automatically receives the broader term. If one searches for a broader term, a document with a narrower term will be returned.

* T10 brings T07. A search for Controlled Substance returns every Schedule II label, along with Schedule III to V labels.
* T06 and T12 bring T11. A search for Organ Impairment Dose Adjustment returns every label with a renal or hepatic dose change.

This does not work in reverse. A search for T10 does not return Schedule IV labels, and a search for T06 does not return labels with only a hepatic dose change.

I chose this rule because a user who asks for controlled substances expects the most tightly controlled drugs in the results. Leaving Schedule II labels out of a Controlled Substance search would hide them.

**AI use:** I decided that labels should carry multiple terms and that narrower terms should return under broader ones. I used Claude (Anthropic) to test each proposed link against the term definitions, and it drafted the final hierarchy, relationship definition, and assignment rules.

---

## 3. Example usage of your vocabulary [20 points]

### Scenario 1: Single-term search

* **Natural language question:** I am a pharmacist checking a new prescription for a patient with severe chronic kidney disease. The patient's creatinine clearance is 25 mL/min. I want to see which drugs in the collection have labels that tell me how to lower the dose or space out doses for patients with impaired kidney function.
* **Selected term:** `T06: Renal Dose Adjustment`
* **Expected documents:** FDA prescription drug labels whose dosing text ties a kidney function level to a lower dose, a longer time between doses, or a lower maximum dose. A typical match has a table of doses by creatinine clearance range.
* **Not retrieved:** labels that only warn about kidney toxicity, labels that say no dose change is needed, labels that only say to avoid the drug in kidney disease, and labels with only a hepatic dose change (T12).
* **Hierarchy note:** each result also carries T11. A user who wanted kidney or liver dose changes would select T11 instead.

### Scenario 2: Two-term combination search

* **Natural language question:** My father takes several pills each day. I want to know which medications taken by mouth carry an FDA boxed warning, so I can check whether any of his are on that list and read those warnings first.
* **Selected terms:** `T01: Boxed Warning` **AND** `T02: Oral Route`. The AND operator returns only documents that have both Term A and Term B.
* **Expected documents:** FDA prescription drug labels for oral medications, such as tablets or capsules, that also carry an official boxed warning. These labels have ORAL among their routes and text in `boxed_warning`. Brand and generic labels both appear, since Brand Name Product (T09) is not selected.
* **Not retrieved:** oral drugs with no boxed warning, and drugs with a boxed warning that are not taken by mouth, such as injection-only products.

**AI use:** The two scenario topics are mine: renal dosing, and oral drugs with boxed warnings. I used Claude (Anthropic) to match each question to the term definitions and to draft the final questions, expected documents, and excluded documents.
