# Mini Search Engine Project Part 1: Document Collection Foraging

*AI was used in a limited capacity primarily for spelling, grammar & phrasing.*

# Prescription Medication

**Source:** [FDA Drug Labels](https://open.fda.gov/apis/drug/label/)

## What the Collection Is About
These are FDA drug labels—the prescribing information that comes with a medication. Each record corresponds to one drug product. 

The main text sits in three fields:
* `indications_and_usage`: What the drug treats
* `adverse_reactions`: Side effects
* `warnings`: Precautions and risk information

Each record also contains the following structured attributes:
* `brand_name`
* `generic_name`
* `substance_name`
* `route`
* `dosage_form`

## Who Will Search It
* Pharmacists and their supporting staff
* Healthcare providers (including doctors, nurses, and clinical staff)
* Patients and family members

## Document Count & Scope Filtering
**Does it contain more than 50 documents?**  
Yes, approximately 54,000 records. 

To narrow down the dataset, the collection will be filtered by:
1. Restricting the records to a single drug class.
2. Retaining only one label per active ingredient.
