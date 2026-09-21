# Aidan Colvin aidancol
# Mini Search Engine Project, Part II: Mini Controlled Vocabulary
Last Updated 09-21-2026

**Help received:** UPDATE ADD BEFORE SUBMITTING  --> If you received help from anyone, give them credits by listing their name(s) on the top of your submission. 

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

**AI use:** In accordance with class policy, Claude and Gemini were used predominantly in combination with class lectures, slide decks, and assignment content to proofread, correct grammar and spelling, and ensure that thoughts regarding term definitions, descriptions, and synonyms were conveyed clearly and concisely. In a limited capacity, class slides and course material were provided to the AI to pull definitions learned in class, ensuring that course concepts were correctly applied to the terms and combined with original thinking and work for this section.

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

**Two kinds of parent terms:**

The two broader terms work differently.

* **T07: Controlled Substance is an independent parent.** It has its own rule: it is assigned whenever `controlled_substance` names Schedule II, III, IV, or V. T10 marks one subset of those labels, Schedule II. T07's own rule already fires for every Schedule II label, so the T10 link never adds a T07 tag the rule would miss. The link guarantees the two terms stay consistent. Labels in Schedules III to V carry T07 alone.
* **T11: Organ Impairment Dose Adjustment is a passive container.** It has no rule of its own. It is assigned only when T06 or T12 is assigned, and it exists to group those two terms for browsing and search. Every T11 label carries T06, T12, or both.

**Why the top-level terms are not linked:**

Each top-level term describes a different property of a label: a safety signal (T01, T04), patient information (T05), route (T02), patient group (T03), dosing (T11), DEA control (T07), or product form (T08, T09). None implies another. The gabapentin label gives renal dose changes but has no boxed warning. Entresto is a brand product with two active ingredients. Linking such terms would tag labels with terms whose definitions they fail.

### 2) Term assignment considerations

**Are the terms mutually exclusive?** No. Documents in this collection can be assigned multiple terms at the same time. The system checks each term's rule on its own and gives a label every term whose definition it meets. For example, the OxyContin (oxycodone extended-release tablets) label meets T01, T02, T05, T07, T08, T09, and T10.

**Logical constraints:** No two PDLA terms exclude each other, because each describes a different property of a label. The constraints that do exist come from the hierarchy and from the drugs themselves:

* A label cannot carry T10 without T07, or T11 without T06 or T12.
* A drug product sits in one DEA schedule. So a T07 label either carries T10 or falls in Schedules III to V, never both.

**Does a narrower term bring its broader term?** Yes. If a document receives a narrower term, it automatically receives the broader term. If one searches for a broader term, a document with a narrower term will be returned.

* T10 brings T07. A search for Controlled Substance returns every Schedule II label, along with Schedule III to V labels.
* T06 and T12 bring T11. A search for Organ Impairment Dose Adjustment returns every label with a renal or hepatic dose change.

This does not work in reverse. A search for T10 does not return Schedule IV labels, and a search for T06 does not return labels with only a hepatic dose change.

I chose this rule because a user who asks for controlled substances expects the most tightly controlled drugs in the results. Leaving Schedule II labels out of a Controlled Substance search would hide them.

**How the search engine applies the rule: expansion at indexing time.** Broader terms are added when labels are tagged and indexed, not when a user searches.

1. The tagger runs each term's rule on each label.
2. Each time it assigns a narrower term, it also writes the broader term to that label's index entry. When it detects T06 or T12, it writes T11. When it detects T10, it writes T07, which T07's own rule has already written.
3. At search time, a query for T11 is a single lookup of the stored T11 tag. It returns the same documents that `T11 OR T06 OR T12` would return under query expansion, because the index already holds every broader tag.

I chose indexing over query expansion for three reasons:

* It matches the term definitions. T11 is defined as assigned when a label gets T06 or T12, which is an indexing rule.
* Every stored tag is complete. Facet counts, browsing, and AND or OR combinations work on the stored tags with no rewriting of the user's query.
* The cost is small. If the hierarchy changes, the collection must be re-tagged. With one drug class and one label per ingredient, that is a quick rerun.

**Missing data:**

* Labels with no `openfda` object are already excluded by the Part 1 scope filter, since they cannot be matched to a drug class.
* Inside the collection, if a field a term's rule needs is missing, the system omits the term. It never guesses. For example, a label with an empty `openfda.route` does not get T02, even if its text says the drug is taken by mouth.
* This favors precision over recall. A user who filters on a term gets only labels that meet the term's rule, with no false positives from guessed tags. The cost is some false negatives, so a missing term does not prove the opposite. Keyword search still reaches those labels, since controlled vocabulary search and keyword search work side by side.

**AI use:** In accordance with class policy, Claude and Gemini were used predominantly in combination with class lectures, slide decks, and assignment content to proofread, correct grammar and spelling, and ensure that thoughts regarding vocabulary structure, hierarchy, and term assignment rules were conveyed clearly and concisely. In a limited capacity, class slides and course material were provided to the AI to pull definitions learned in class, ensuring that course concepts like flat lists, hierarchies, and mutual exclusivity were correctly applied and combined with original thinking and work for this section.

---

## 3. Example usage of your vocabulary [20 points]

Both scenarios search the Part 1 collection: human prescription drug labels in one drug class, with one label per active ingredient. In the planned search interface, vocabulary terms appear as filters beside the results, grouped by the property they describe in Section 2, such as safety signal, route, or dosing. A user can apply filters to the whole collection or to the results of a keyword search.

### Scenario 1: Single-term search

* **Natural language question:** I am a pharmacist checking a new prescription for a patient with severe chronic kidney disease. The patient's creatinine clearance is 25 mL/min. I want to see which drugs in the collection have labels that tell me exactly how to lower the dose or space out doses for patients with impaired kidney function.
* **Selected term:** `T06: Renal Dose Adjustment`
* **How the user applies it:** The user selects Renal Dose Adjustment from the dosing filters. The search engine returns every label that carries the stored T06 tag.
* **Expected documents:** FDA prescription drug labels whose dosing text in `dosage_and_administration`, `use_in_specific_populations`, or `precautions` ties a kidney function level to a lower dose, a longer time between doses, or a lower maximum dose. Kidney function levels include creatinine clearance ranges; mild, moderate, or severe renal impairment; and end-stage renal disease or dialysis. A typical match has a table of doses by creatinine clearance range. Each result would show the drug's brand and generic names and a snippet of its renal dosing text.
* **Not retrieved:**
  * Labels that mention renal excretion or kidney toxicity but give no dose change.
  * Labels that state no dose change is needed in renal impairment.
  * Labels that only say the drug is contraindicated or should be avoided in severe renal impairment, with no adjusted dose.
  * Labels with only a hepatic dose change (T12).
* **Why the term works better than keyword search here:** A keyword search for "renal" or "kidney" also returns labels that mention the kidneys only in pharmacokinetics, adverse reactions, or clinical trial exclusions. Those labels do not answer how to dose this patient, so precision drops. T06 is assigned only when the label ties a kidney function level to a dose change, so every result answers the pharmacist's question as far as the tagging rule is applied correctly.
* **Hierarchy note:** T06 is a type of T11, so the index writes T11 on every T06 label. Each result therefore also carries T11. A user who wanted kidney or liver dose changes would select T11 instead, which returns both T06 and T12 labels.

### Scenario 2: Two-term combination search

* **Natural language question:** My father's doctor plans to start him on a new medication from this drug class. He cannot give himself injections, so it needs to be something he takes by mouth at home. Before the appointment, I want to find the oral options in this class that carry an FDA boxed warning, read those warnings, and bring my questions about them to the doctor.
* **Selected terms:** `T01: Boxed Warning` and `T02: Oral Route`
* **Operator:** **AND**. The search returns only documents that have both Term A (T01) and Term B (T02). In set terms, the result is the intersection of the two tag sets: T01 ∩ T02.
* **How the user applies it:** The user selects Oral Route from the route filters and Boxed Warning from the safety signal filters. The interface joins the two selections with AND.
* **Expected documents:** FDA prescription drug labels in the collection for oral medications, such as tablets, capsules, or oral solutions, that also carry an official boxed warning. Each has ORAL among its routes in `openfda.route` and text in `boxed_warning`. A label that lists ORAL along with another route, such as intravenous, still appears. Brand and generic labels both appear, as do single-ingredient and combination products, since no product-form terms (T08, T09) are selected. These are the labels whose boxed warnings the user reads before the appointment.
* **Not retrieved:**
  * Oral drugs in the class with no boxed warning.
  * Drugs with a boxed warning that are not taken by mouth, such as injection-only, topical, or inhaled products.
  * Sublingual or buccal products, which do not get T02.
* **Why AND, not OR:** OR would return the union of the two tag sets, T01 ∪ T02: every oral drug in the class plus every drug in the class with a boxed warning. That adds injection-only drugs with a box, which he cannot take, and oral drugs with no box, which the question does not ask about. OR raises recall for either condition but lowers precision for this question. AND keeps only the drugs that answer both parts.
* **Why the terms work better than keyword search here:** A keyword search for "oral" also matches labels that mention oral contraceptives in drug interactions or oral candidiasis as a side effect, whatever the drug's route. A keyword search for "boxed warning" can miss labels, because the box itself is headed "WARNING" plus its topic, and older labels may never use the phrase "boxed warning." T02 reads the route field and T01 reads the `boxed_warning` field, so neither depends on the label's wording.
* **Hierarchy note:** neither T01 nor T02 has a broader or narrower term, so the hierarchy does not widen or narrow this search.

**AI use:** In accordance with class policy, Claude and Gemini were used predominantly in combination with class lectures, slide decks, and assignment content to proofread, correct grammar and spelling, and ensure that thoughts were conveyed clearly and concisely. In a limited capacity, class slides and course material were provided to the AI to pull definitions learned in class, ensuring that course concepts were correctly applied and combined with original thinking and work for this section.

---

UPDATE THIS SECTION BEFORE SUBMITTING 

### 4. Peer exchange [20 points]
Invite a peer classmate as a hypothetical user of your search engine.

Describe your planned document collection to them: What documents will be in the collection? Why do you think they are interesting? Also, describe your controlled vocabulary to them: What does each term mean? In what scenarios can they be useful?

Ask the user to come up with a scenario in which they would use your controlled vocabulary when searching or refining results. Ask them to explain their question in complete sentences, and take note of the term(s) they selected.

Answer the following questions:
* <u>What is the name and PID of your user?</u>
* <u>Who invited you as a user to use their search engines (if any)? What are their names and PIDs?</u>
* <u>What was your user's question in natural language?</u>
* <u>What terms did they select to represent that question?</u>

---
