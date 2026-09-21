# Aidan Colvin aidancol
# Mini Search Engine Project, Part 1 (Revised): Document Collection Foraging
Last Updated 09-21-2026

**Source:** [FDA Drug Labels](https://open.fda.gov/apis/drug/label/)

#### What the Collection Is About

These are FDA drug labels: the prescribing information that comes with a medication. Each record is one version of one label, submitted to FDA in Structured Product Labeling (SPL) format. One label can cover several products and package sizes (NDCs).

The main text sits in these fields:

* `indications_and_usage`: What the drug treats
* `adverse_reactions`: Side effects
* `warnings_and_cautions` (newer, PLR-format labels) or `warnings` (older labels): Precautions and risk information
* `boxed_warning`: The most serious risks, when the label has a boxed warning
* `contraindications`: Situations, and other drugs, the product must not be used with
* `drug_interactions`: How the drug interacts with other drugs and foods, and how to manage it

Most records also carry structured attributes in an `openfda` object:

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

A central question for all three groups is whether a patient's medications are safe to take together.

#### Document Count & Scope Filtering

**Does it contain more than 50 documents?**
Yes. The Label endpoint holds 262,883 labels as of its September 18, 2026 update, prescription and over-the-counter combined. Human prescription labels are a large subset, about 54,000 by my Part 1 estimate.

To narrow down the dataset, the collection will be filtered by:

1. Keeping human prescription labels only (`openfda.product_type` is HUMAN PRESCRIPTION DRUG).
2. Keeping labels that have the `openfda` object, since the system needs its ingredient names and identifiers to match the same drug across labels.
3. Retaining only the newest label per active-ingredient set. A combination product counts as its own ingredient set, so combinations stay in the collection.

**Why not one drug class:** My original Part 1 restricted the collection to a single drug class. Interactions often cross classes, such as an antidepressant taken with a muscle relaxant, so a one-class collection would miss the combinations users most need to find.

**AI use:** My original Part 1 used AI only for spelling, grammar, and phrasing. For this revision, I decided to widen the scope to all drug classes. I used Claude (Anthropic) to check my field names against the openFDA Label documentation and to draft the revised field descriptions and scope filters.
