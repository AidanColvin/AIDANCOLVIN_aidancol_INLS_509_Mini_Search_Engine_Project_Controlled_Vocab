"""Black-box grader for TEST_PACK.md: scores what the public site showed (captured by the browser runner) against the answer key and the rulebook."""

from __future__ import annotations

import json
import re
import statistics
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

PACK_GRADE_RANK: dict[str, int] = {"A": 1, "B": 2, "C": 3, "D": 4}
KEY_TO_PACK: dict[str, str] = {"minor": "A", "moderate": "B", "major": "C", "contraindicated": "D"}
SITE_TO_PACK: dict[str, str] = {"E": "D", "D": "C", "C": "B", "B": "B", "A": "A"}
CONTROL_LISTS: frozenset[str] = frozenset({"L11", "L29"})
STRIP_WORDS: frozenset[str] = frozenset(
    {"er", "ir", "sr", "xl", "xr", "dr", "cd", "la", "otc", "generic", "sodium", "carbonate", "succinate", "etexilate",
     "sublingual", "nasal", "propionate", "sulfate", "chloride", "mofetil", "tartrate", "hydrochloride", "hcl",
     "disoproxil", "fumarate", "potassium", "mixed", "salts"}
)
KEEP_WHOLE: frozenset[str] = frozenset({"potassium chloride", "calcium carbonate", "ferrous sulfate", "insulin glargine", "folic acid", "isosorbide mononitrate", "ethinyl estradiol"})
UNRESOLVED = re.compile(r"Not found in the FDA labels|Not a medication name we know", re.I)
PRIMARY_SOURCE = re.compile(r"dailymed\.nlm\.nih\.gov|pubmed|ncbi\.nlm\.nih\.gov|fda\.gov|medlineplus\.gov|nih\.gov", re.I)
DRUG_SPECIFIC = re.compile(r"dailymed\.nlm\.nih\.gov/dailymed/(drugInfo|lookup)|pubmed\.ncbi\.nlm\.nih\.gov/\d+|accessdata\.fda\.gov", re.I)

CATEGORY_WORDS: dict[str, str] = {
    "serotonin syndrome": r"serotonin",
    "CNS depression": r"CNS depress|central nervous system depress|sedat|somnolen|drows|respirat|depressant",
    "respiratory depression": r"respirat|breathing",
    "QT prolongation": r"\bQT|torsade",
    "bleeding": r"bleed|hemorrha|haemorrha|anticoagul|antiplatelet",
    "CYP inhibition": r"CYP|cytochrome|inhibit\w*|increase\w* (?:the )?(?:plasma |serum |blood )?(?:concentration|exposure|level|AUC)",
    "CYP induction": r"induc\w*|decrease\w* (?:the )?(?:plasma |serum )?(?:concentration|exposure|level)",
    "P-gp": r"P-gp|P-glycoprotein",
    "hyperkalemia": r"hyperkal|potassium",
    "hypoglycemia": r"hypoglyc|blood (?:sugar|glucose)",
    "hypotension": r"hypotens|blood pressure|syncope|orthostat",
    "bradycardia/AV block": r"bradycard|AV block|atrioventricular|heart block|conduction|heart rate",
    "nephrotoxicity": r"renal|kidney|nephro",
    "ototoxicity": r"ototox|hearing|oto",
    "myelosuppression": r"myelosupp|pancytop|bone.marrow|neutropen|agranulocyt|leukopen|thrombocytopen|hematolog",
    "myopathy/rhabdomyolysis": r"myopath|rhabdomyol|muscle",
    "lithium toxicity": r"lithium",
    "digoxin toxicity": r"digoxin|digitalis",
    "seizure threshold": r"seizure|convuls",
    "anticholinergic burden": r"anticholinergic|muscarin",
    "hyperammonemia": r"ammoni",
    "adrenal suppression": r"adrenal|cortisol|Cushing",
    "metabolic acidosis": r"acidosis",
    "therapeutic antagonism": r"antagon|oppos|counteract|block\w* the effect|reduc\w* (?:the )?(?:effect|efficacy)|withdrawal",
    "opposing pharmacology": r"antagon|oppos|counteract|reduc\w* (?:the )?(?:effect|efficacy)",
    "efficacy loss": r"reduc\w* (?:the )?(?:effect|efficacy|concentration|exposure|level)|decreas\w* (?:the )?(?:plasma )?(?:effect|efficacy|concentration|exposure|level)|induc\w*|contracept|loss of",
    "absorption/timing": r"absor|bioavailab|chelat|separat\w*|hours? (?:before|after)",
    "duplicate therapy": r"duplicat|same (?:drug|class|ingredient)|share\w* an active ingredient|active metabolite|metabolite|two entries|therapeutic duplication",
    "duplicate entry": r"duplicat|same (?:drug|ingredient)|share\w* an active ingredient|two entries|entered twice|add together",
    "dose ceiling": r"maximum|exceed\w*|ceiling|above the|over the (?:labeled )?(?:max|limit)",
    "dosing frequency": r"week",
    "unit normalization": r"duplicat|same (?:drug|ingredient)|share\w* an active ingredient|two entries",
    "combination parsing": r"butalbital",
    "electrolyte": r"hyponatr|hypokal|hypomagnes|electrolyte|sodium|potassium|SIADH",
}
DUPLICATE_CATEGORIES: frozenset[str] = frozenset({"duplicate entry", "duplicate therapy", "unit normalization"})
HANDLING_CATEGORIES: frozenset[str] = frozenset({"dosing frequency", "combination parsing"})

# Rulebook rows 1-36 as drug classes (Section 3 of TEST_PACK.md). Each row is a list of "sides"; the row applies when
# every side has at least one drug on the list (drawn from different entries), or, for burden rows, when min_count drugs match.
OPIOIDS = {"oxycodone", "hydrocodone", "fentanyl", "methadone", "tramadol", "meperidine", "morphine", "codeine", "buprenorphine", "hydromorphone", "tapentadol", "oxymorphone"}
BENZOS = {"alprazolam", "clonazepam", "lorazepam", "diazepam", "temazepam", "triazolam", "midazolam", "chlordiazepoxide", "clobazam"}
GABAPENTINOIDS = {"gabapentin", "pregabalin"}
STRONG_3A4_INHIBITORS = {"clarithromycin", "ritonavir", "cobicistat", "itraconazole", "voriconazole", "ketoconazole", "posaconazole"}
CYP1A2_INHIBITORS = {"ciprofloxacin", "fluvoxamine"}
ANTICHOLINERGICS = {"diphenhydramine", "hydroxyzine", "promethazine", "amitriptyline", "nortriptyline", "doxepin", "imipramine", "oxybutynin", "tolterodine", "paroxetine", "benztropine", "trihexyphenidyl", "olanzapine", "quetiapine", "clozapine", "cyclobenzaprine", "meclizine"}
SSRIS = {"sertraline", "fluoxetine", "paroxetine", "citalopram", "escitalopram", "fluvoxamine"}
SNRIS = {"venlafaxine", "duloxetine", "desvenlafaxine", "levomilnacipran", "milnacipran"}
MAOIS = {"phenelzine", "tranylcypromine", "isocarboxazid", "selegiline", "rasagiline", "linezolid", "methylene blue", "safinamide"}
SEROTONERGIC_PARTNERS = {"tramadol", "meperidine", "linezolid", "methylene blue", "dextromethorphan", "lithium", "phenelzine", "tranylcypromine", "isocarboxazid", "selegiline", "rasagiline", "sumatriptan", "rizatriptan", "zolmitriptan", "methadone", "fentanyl", "buspirone", "trazodone"}
THRESHOLD_LOWERING = {"bupropion", "tramadol", "clozapine", "olanzapine", "quetiapine", "haloperidol", "amitriptyline", "theophylline", "ciprofloxacin", "levofloxacin", "meperidine", "prednisone", "methylprednisolone", "dexamethasone"}
CYP2D6_INHIBITORS = {"paroxetine", "fluoxetine", "bupropion", "quinidine"}
NSAIDS = {"ibuprofen", "naproxen", "meloxicam", "celecoxib", "ketorolac", "diclofenac", "aspirin", "indomethacin", "etodolac", "nabumetone"}
ANTICOAGULANTS = {"warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban", "enoxaparin", "heparin"}
ANTIPLATELETS = {"aspirin", "clopidogrel", "prasugrel", "ticagrelor"}
WARFARIN_2C9 = {"sulfamethoxazole", "trimethoprim", "fluconazole", "metronidazole", "amiodarone", "rifampin"}
DOAC_3A4_PGP = {"ketoconazole", "itraconazole", "ritonavir", "cobicistat", "dronedarone"}
PGP_INHIBITORS = {"dronedarone", "ketoconazole", "verapamil", "amiodarone", "clarithromycin", "cyclosporine", "quinidine"}
ACEI_ARB = {"lisinopril", "enalapril", "ramipril", "benazepril", "captopril", "quinapril", "losartan", "valsartan", "irbesartan", "olmesartan", "candesartan", "telmisartan"}
DIURETICS = {"furosemide", "bumetanide", "torsemide", "hydrochlorothiazide", "chlorthalidone", "spironolactone", "eplerenone", "indapamide", "metolazone"}
MRAS = {"spironolactone", "eplerenone"}
THIAZIDES = {"hydrochlorothiazide", "chlorthalidone", "indapamide", "metolazone"}
LOOPS = {"furosemide", "bumetanide", "torsemide"}
DIGOXIN_RAISERS = {"amiodarone", "dronedarone", "verapamil", "diltiazem", "clarithromycin", "itraconazole"}
BETA_BLOCKERS = {"metoprolol", "carvedilol", "propranolol", "atenolol", "bisoprolol", "nadolol", "labetalol", "nebivolol", "sotalol"}
NONDHP_CCB = {"verapamil", "diltiazem"}
NITRATES = {"nitroglycerin", "isosorbide mononitrate", "isosorbide dinitrate"}
PDE5 = {"sildenafil", "tadalafil", "vardenafil", "avanafil", "riociguat"}
ALPHA1 = {"tamsulosin", "doxazosin", "prazosin", "terazosin", "alfuzosin", "silodosin"}
ANTIHYPERTENSIVES = ACEI_ARB | DIURETICS | BETA_BLOCKERS | NONDHP_CCB | NITRATES | PDE5 | {"amlodipine", "nifedipine", "clonidine", "guanfacine", "hydralazine"}
QT_DRUGS = {"methadone", "ondansetron", "haloperidol", "quetiapine", "citalopram", "escitalopram", "azithromycin", "clarithromycin", "erythromycin", "levofloxacin", "ciprofloxacin", "moxifloxacin", "fluconazole", "ketoconazole", "itraconazole", "voriconazole", "posaconazole", "hydroxychloroquine", "amiodarone", "dronedarone", "sotalol", "dofetilide"}
SYMPATHOMIMETICS = {"pseudoephedrine", "phenylephrine", "amphetamine", "dextroamphetamine", "lisdexamfetamine", "methylphenidate", "ephedrine"}
MAOI_24 = {"phenelzine", "tranylcypromine", "isocarboxazid", "selegiline", "linezolid"}
SULFONYLUREAS = {"glipizide", "glyburide", "glimepiride"}
SU_RAISERS = {"fluconazole", "sulfamethoxazole", "trimethoprim", "clarithromycin"}
STATINS_3A4 = {"simvastatin", "lovastatin", "atorvastatin"}
STATIN_RAISERS = {"clarithromycin", "itraconazole", "ritonavir", "cobicistat", "cyclosporine", "ketoconazole", "posaconazole", "voriconazole", "erythromycin", "gemfibrozil"}
COLCHICINE_RAISERS = {"clarithromycin", "cyclosporine", "ritonavir", "cobicistat", "ketoconazole", "itraconazole", "voriconazole", "posaconazole", "erythromycin", "diltiazem", "verapamil"}
XO_INHIBITORS = {"allopurinol", "febuxostat"}
THIOPURINES = {"azathioprine", "mercaptopurine"}
MTX_PARTNERS = {"sulfamethoxazole", "trimethoprim", "omeprazole", "esomeprazole", "pantoprazole", "lansoprazole", "amoxicillin", "piperacillin", "penicillin"} | NSAIDS
VALPROATE = {"valproate", "valproic acid", "divalproex"}
CARBAPENEMS = {"meropenem", "ertapenem", "imipenem", "doripenem"}
INDUCERS = {"rifampin", "carbamazepine", "phenytoin", "phenobarbital", "st john's wort"}
INDUCER_VICTIMS = {"apixaban", "rivaroxaban", "dabigatran", "edoxaban", "tacrolimus", "cyclosporine", "darunavir", "ritonavir", "atazanavir", "ethinyl estradiol", "norgestimate", "methadone"}
CALCINEURIN = {"tacrolimus", "cyclosporine"}
CNI_RAISERS = {"fluconazole", "ketoconazole", "itraconazole", "voriconazole", "posaconazole", "clarithromycin", "diltiazem", "verapamil"}
FLUOROQUINOLONES = {"ciprofloxacin", "levofloxacin", "moxifloxacin", "ofloxacin"}
SYSTEMIC_STEROIDS = {"prednisone", "prednisolone", "methylprednisolone", "dexamethasone", "hydrocortisone"}


@dataclass(frozen=True)
class RuleRow:
    """One rulebook row: its number, name, the drug sides that trigger it, and the words that name its syndrome."""

    number: int
    name: str
    sides: tuple[frozenset[str], ...]
    syndrome: str
    min_count: int = 0
    pool: frozenset[str] = frozenset()


def row(number: int, name: str, syndrome: str, *sides: set[str], min_count: int = 0, pool: set[str] | None = None) -> RuleRow:
    """
    Takes a row number, name, syndrome regex, drug sides, and an optional burden pool with its minimum count.
    Builds the RuleRow.
    Gives the RuleRow.
    """
    return RuleRow(number, name, tuple(frozenset(side) for side in sides), syndrome, min_count, frozenset(pool or set()))


RULEBOOK: tuple[RuleRow, ...] = (
    row(1, "Opioid + benzodiazepine", r"respirat|CNS depress|sedat|overdose", OPIOIDS, BENZOS),
    row(2, "Opioid + gabapentinoid", r"respirat|CNS depress|sedat", OPIOIDS, GABAPENTINOIDS),
    row(3, "Oxycodone/fentanyl/methadone + strong CYP3A4 inhibitor", r"CYP3A4|3A4|concentration|respirat|opioid toxic", {"oxycodone", "fentanyl", "methadone"}, STRONG_3A4_INHIBITORS),
    row(4, "Tizanidine + ciprofloxacin or fluvoxamine", r"CYP1A2|1A2|hypotens|contraindicat", {"tizanidine"}, CYP1A2_INHIBITORS),
    row(5, "Clozapine + fluvoxamine or ciprofloxacin", r"CYP1A2|1A2|clozapine (?:level|concentration)|seizure", {"clozapine"}, CYP1A2_INHIBITORS),
    row(6, "Anticholinergic burden", r"anticholinergic|muscarin", min_count=3, pool=ANTICHOLINERGICS),
    row(7, "SSRI/SNRI or MAOI + serotonergic drug", r"serotonin", SSRIS | SNRIS | MAOIS, SEROTONERGIC_PARTNERS | SSRIS | SNRIS),
    row(8, "Tramadol/bupropion + threshold-lowering drug or CYP2D6 inhibitor", r"seizure|convuls|2D6", {"tramadol", "bupropion"}, THRESHOLD_LOWERING | CYP2D6_INHIBITORS),
    row(9, "Warfarin + NSAID", r"bleed|hemorrha", {"warfarin"}, NSAIDS),
    row(10, "Warfarin + CYP2C9 inhibitor (or rifampin)", r"INR|bleed|2C9|prothrombin", {"warfarin"}, WARFARIN_2C9),
    row(11, "DOAC + strong CYP3A4/P-gp inhibitor", r"bleed|P-gp|3A4", {"apixaban", "rivaroxaban", "dabigatran", "edoxaban"}, DOAC_3A4_PGP | PGP_INHIBITORS),
    row(12, "Anticoagulant + DAPT or antiplatelet + NSAID", r"bleed", ANTICOAGULANTS, ANTIPLATELETS, NSAIDS | ANTIPLATELETS),
    row(13, "SSRI + NSAID or anticoagulant", r"bleed", SSRIS, NSAIDS | ANTICOAGULANTS),
    row(14, "Triple whammy: ACEi/ARB + diuretic + NSAID", r"renal|kidney", ACEI_ARB, DIURETICS, NSAIDS),
    row(15, "ACEi/ARB or TMP-SMX + MRA (hyperkalemia)", r"hyperkal|potassium", ACEI_ARB | {"trimethoprim", "potassium chloride"}, MRAS | {"trimethoprim", "potassium chloride"}),
    row(16, "Lithium + NSAID, ACEi/ARB, or thiazide", r"lithium", {"lithium"}, NSAIDS | ACEI_ARB | THIAZIDES),
    row(17, "Thiazide + SSRI (hyponatremia)", r"hyponatr|sodium|SIADH", THIAZIDES, SSRIS | {"carbamazepine", "oxcarbazepine"}),
    row(18, "Digoxin + P-gp inhibitor or loop/thiazide", r"digoxin", {"digoxin"}, DIGOXIN_RAISERS | LOOPS | THIAZIDES),
    row(19, "Metformin + AKI cause", r"lactic|renal|kidney", {"metformin"}, NSAIDS | {"iodinated contrast"}),
    row(20, "Beta-blocker + verapamil or diltiazem", r"bradycard|AV block|atrioventricular|heart block|conduction", BETA_BLOCKERS, NONDHP_CCB),
    row(21, "Nitrate + PDE5 inhibitor or riociguat", r"hypotens|blood pressure", NITRATES, PDE5),
    row(22, "Alpha-1 blocker + PDE5 inhibitor or antihypertensive", r"hypotens|orthostat|syncope|blood pressure", ALPHA1, ANTIHYPERTENSIVES),
    row(23, "Stacked QT prolongers", r"\bQT|torsade", min_count=2, pool=QT_DRUGS),
    row(24, "MAOI + sympathomimetic", r"hypertensi", MAOI_24, SYMPATHOMIMETICS),
    row(25, "Clonidine + beta-blocker", r"rebound|hypertensi|bradycard", {"clonidine"}, BETA_BLOCKERS),
    row(26, "Sulfonylurea + CYP2C9 inhibitor or beta-blocker", r"hypoglyc", SULFONYLUREAS, SU_RAISERS | BETA_BLOCKERS),
    row(27, "Statin + CYP3A4 inhibitor, gemfibrozil, or amiodarone/verapamil/diltiazem", r"myopath|rhabdo", STATINS_3A4, STATIN_RAISERS | {"amiodarone", "verapamil", "diltiazem"}),
    row(28, "Colchicine + CYP3A4/P-gp inhibitor", r"colchicine|toxicit|3A4|P-gp", {"colchicine"}, COLCHICINE_RAISERS),
    row(29, "Xanthine oxidase inhibitor + thiopurine", r"myelosupp|pancytop|bone marrow|azathioprine|mercaptopurine", XO_INHIBITORS, THIOPURINES),
    row(30, "Methotrexate + TMP-SMX, NSAID, PPI, or penicillin", r"methotrexate|myelosupp|toxicit", {"methotrexate"}, MTX_PARTNERS),
    row(31, "Clopidogrel + omeprazole or esomeprazole", r"2C19|clopidogrel|antiplatelet", {"clopidogrel"}, {"omeprazole", "esomeprazole"}),
    row(32, "Valproate + carbapenem", r"valpro|seizure", VALPROATE, CARBAPENEMS),
    row(33, "Inducer + DOAC, calcineurin inhibitor, PI, OC, or methadone", r"induc|decreas|reduc|efficacy|contracept", INDUCERS, INDUCER_VICTIMS),
    row(34, "Calcineurin inhibitor + azole, clarithromycin, diltiazem, or verapamil", r"tacrolimus|cyclosporine|concentration|nephrotox", CALCINEURIN, CNI_RAISERS),
    row(35, "Codeine/tramadol + CYP2D6 inhibitor", r"2D6|efficacy|analges", {"codeine", "tramadol"}, CYP2D6_INHIBITORS),
    row(36, "Fluoroquinolone + systemic corticosteroid", r"tendon|tendin", FLUOROQUINOLONES, SYSTEMIC_STEROIDS),
)


@dataclass
class Entry:
    """One comma-separated entry of a test list: the brand as typed, the generic in parentheses, and its ingredients."""

    raw: str
    brand: str
    generic: str
    ingredients: list[str] = field(default_factory=list)


def ingredients_of(name: str) -> list[str]:
    """
    Takes a drug name such as "divalproex sodium DR" or "sulfamethoxazole/trimethoprim".
    Splits combination names on "/" and drops salt and release-form words.
    Gives the lowercase ingredient names, empty for an empty name.
    """
    parts = re.split(r"\s*/\s*|\s+and\s+", name.lower())
    found: list[str] = []
    for part in parts:
        part = re.sub(r"\(.*?\)", "", part).strip()
        whole = next((keep for keep in KEEP_WHOLE if part.startswith(keep)), None)
        if whole:
            found.append(whole)
            continue
        words = [word for word in re.split(r"\s+", part) if word and word not in STRIP_WORDS]
        if words:
            found.append(" ".join(words))
    return [VALPROATE_ALIAS.get(item, item) for item in found]


VALPROATE_ALIAS: dict[str, str] = {"valproic acid": "divalproex", "valproate": "divalproex"}


def parse_entry(raw: str) -> Entry:
    """
    Takes one entry such as "Zyprexa (olanzapine) 10 mg once daily = 10 mg/day".
    Reads the brand before the parentheses and the generic inside them; "(generic)" means the brand is the generic.
    Gives the Entry with its ingredient list.
    """
    match = re.match(r"\s*(.*?)\s*\((.*?)\)", raw)
    if not match:
        return Entry(raw, raw.split(" ")[0], raw.split(" ")[0], ingredients_of(raw.split(" ")[0]))
    brand, generic = match.group(1), match.group(2)
    if generic.strip().lower() == "generic":
        generic = brand
    return Entry(raw, brand, generic, ingredients_of(generic))


def load_pack(path: Path) -> tuple[dict[str, str], dict[str, dict]]:
    """
    Takes the path to TEST_PACK.md.
    Reads the Section 5 lists and the Section 6 answer key.
    Gives the lines by list ID and the answer key by list ID.
    """
    text = path.read_text(encoding="utf-8")
    section5 = text.split("## Section 5")[1].split("## Section 6")[0]
    lines = section5.splitlines()
    lists: dict[str, str] = {}
    for index, line in enumerate(lines):
        if re.fullmatch(r"[LG]\d\d", line.strip()):
            cursor = index + 1
            while not lines[cursor].strip():
                cursor += 1
            lists[line.strip()] = lines[cursor].strip()
    key_json = text.split("## Section 6")[1].split("```json", 1)[1].split("```", 1)[0]
    return lists, json.loads(key_json)["answer_key"]


def site_pack_grade(site_letter: str | None) -> str | None:
    """
    Takes the site's A-E grade letter.
    Maps it onto the pack's A-D scale.
    Gives the pack letter, or None when the site showed no grade.
    """
    return SITE_TO_PACK.get((site_letter or "").strip().upper())


def display_ingredients(display: str, entries: list[Entry], meds: list[dict]) -> set[str]:
    """
    Takes a drug name as the site displayed it in an alert, the list's entries, and the site's medication cards.
    Resolves it to ingredients through the card that shows it, the typed brand, or a generic named inside it.
    Gives the set of ingredient names, empty when nothing matches.
    """
    low = display.lower().strip()
    found: set[str] = set()
    for med in meds:
        if (med.get("brand") or "").lower().strip() == low and med.get("generic"):
            found.update(ingredients_of(med["generic"]))
    for entry in entries:
        brand = entry.brand.lower()
        if low == brand or low.startswith(brand + " ") or low.startswith(brand + "(") or entry.raw.lower().startswith(low):
            found.update(entry.ingredients)
    vocabulary = {item for entry in entries for item in entry.ingredients}
    found.update(item for item in vocabulary if re.search(r"\b" + re.escape(item) + r"\b", low))
    return found


def alert_ingredients(alert: dict, entries: list[Entry], meds: list[dict]) -> set[str]:
    """
    Takes one captured alert, the list's entries, and the medication cards.
    Resolves every drug named in the alert heading.
    Gives the union of their ingredients.
    """
    names = [name.strip() for name in re.split(r",\s*", alert.get("drugs") or "") if name.strip()]
    found: set[str] = set()
    for name in names:
        found |= display_ingredients(name, entries, meds)
    return found


def alert_text(alert: dict) -> str:
    """
    Takes one captured alert.
    Joins every visible text field of the alert.
    Gives the joined text.
    """
    keys = ("category", "grade_text", "basis", "quote", "why_title", "why_text", "source", "action", "includes")
    return " ".join(str(alert.get(key) or "") for key in keys)


def category_pattern(category: str) -> str:
    """
    Takes an answer-key category such as "efficacy loss".
    Joins the category's own words with its keyword family, so a site that names the category outright is credited.
    Gives the regular expression.
    """
    return "|".join(filter(None, (re.escape(category), CATEGORY_WORDS.get(category, ""))))


def is_duplication(alert: dict) -> bool:
    """
    Takes one captured alert.
    Checks the alert's classes and text for a duplication alert.
    Gives True for a duplication alert.
    """
    return "duplication" in (alert.get("classes") or "") or bool(re.search(CATEGORY_WORDS["duplicate therapy"], alert_text(alert), re.I))


def score_item(item: dict, alerts: list[dict], alert_sets: list[set[str]], site: dict, entries: list[Entry]) -> dict:
    """
    Takes one expected answer-key item, the site's alerts with their ingredient sets, the captured page, and the list's entries.
    Scores it HIT, PARTIAL, or MISS by the pack's rules.
    Gives the item with its status, the site's matching grade and category, and a reason.
    """
    expected = set()
    for drug in item["drugs"]:
        expected.update(ingredients_of(drug))
    want = KEY_TO_PACK[item["severity"]]
    category = item["category"]
    result = {**item, "pack_grade": want, "status": "MISS", "site_grade": None, "site_category": None, "reason": "not flagged"}
    if category in HANDLING_CATEGORIES:
        return score_handling(item, result, site, expected)
    best_rank = -1
    for alert, found in zip(alerts, alert_sets):
        if not expected <= found:
            continue
        if category in DUPLICATE_CATEGORIES and not is_duplication(alert):
            continue
        got = site_pack_grade(alert.get("grade"))
        got_rank = PACK_GRADE_RANK.get(got or "", 0)
        category_ok = bool(re.search(category_pattern(category), alert_text(alert), re.I))
        grade_ok = got_rank >= PACK_GRADE_RANK[want]
        grade_one = got_rank == PACK_GRADE_RANK[want] - 1
        if category_ok and grade_ok:
            status, rank, reason = "HIT", 3, "same drugs, equivalent category, same or higher grade"
        elif category_ok and grade_one:
            status, rank, reason = "PARTIAL", 2, "right drugs and category, grade one lower"
        elif grade_ok:
            status, rank, reason = "PARTIAL", 2, "right drugs and grade, category not named"
        else:
            status, rank, reason = "MISS", 1, "drugs flagged but grade two or more lower and category not named" if not category_ok else "drugs flagged but grade two or more lower"
        if rank > best_rank:
            best_rank = rank
            result.update(status=status, site_grade=f"{alert.get('grade')} (= {got})", site_category=alert.get("category"), reason=reason)
    if best_rank < 0:
        partial = [found & expected for found in alert_sets if len(found & expected) >= 2]
        if partial and len(expected) >= 3:
            result["reason"] = f"only a subset flagged together: {sorted(max(partial, key=len))}"
    return result


def score_handling(item: dict, result: dict, site: dict, expected: set[str]) -> dict:
    """
    Takes a dosing-frequency or combination-parsing item, its result shell, the captured page, and its ingredients.
    Checks the medication cards: a weekly drug must show a weekly amount and no daily total; a combination must show every component.
    Gives the result marked HIT or MISS with a reason.
    """
    cards = [med for med in site.get("meds") or [] if expected & set(ingredients_of(med.get("generic") or "")) or any(e in (med.get("text") or "").lower() for e in expected)]
    text = " ".join(med.get("text") or "" for med in cards)
    if item["category"] == "dosing frequency":
        weekly = bool(re.search(r"/\s*week|per week|weekly", text, re.I))
        daily = bool(re.search(r"\d\s*(mg|mcg)\s*(/|per)\s*day", text, re.I))
        ok = weekly and not daily and not re.search(r"not found", text, re.I)
        result.update(status="HIT" if ok else "MISS", reason="card shows a weekly amount and no daily total" if ok else "card does not show a weekly amount without a daily total")
        return result
    components = {"butalbital", "acetaminophen", "caffeine"} if "butalbital" in expected else expected
    shown = {c for c in components if c in text.lower()}
    ok = shown == components and not re.search(r"not found", text, re.I)
    result.update(status="HIT" if ok else "MISS", reason=f"components shown: {sorted(shown)}")
    return result


def amounts_in(text: str) -> list[tuple[float, str]]:
    """
    Takes page text.
    Finds every amount with a unit and converts mass to mg.
    Gives (value, unit class) pairs where the class is mg, mEq, units, mcg/h, or MME, each suffixed "/week" when stated per week.
    """
    found: list[tuple[float, str]] = []
    pattern = r"(\d[\d,]*\.?\d*)\s*(mcg/h|mcg|mg|g|mEq|units?|MME)\b(\s*(?:/|per)\s*(?:week|wk))?"
    for number, unit, weekly in re.findall(pattern, text, re.I):
        value = float(number.replace(",", ""))
        unit_low = unit.lower()
        scale = {"mcg": 0.001, "g": 1000.0}.get(unit_low, 1.0)
        unit_class = {"mcg": "mg", "g": "mg", "unit": "units", "units": "units", "meq": "mEq", "mme": "MME", "mcg/h": "mcg/h"}.get(unit_low, "mg")
        found.append((round(value * scale, 4), unit_class + ("/week" if weekly else "")))
    return found


def score_totals(totals: dict[str, str], site: dict) -> list[dict]:
    """
    Takes the answer key's totals for one list and the captured page.
    Checks whether the page shows each per-molecule amount (units normalized) on a card or alert that names that molecule.
    Gives one row per totals entry with the expected text, whether it was found, and what the site showed.
    """
    rows: list[dict] = []
    resolved = [med for med in site.get("meds") or [] if not UNRESOLVED.search(med.get("text") or "")]
    blocks = [(med.get("text") or "").replace(med.get("brand") or "", "", 1) + " " + (med.get("generic") or "") for med in resolved]
    blocks += [alert_text(alert) + " " + (alert.get("drugs") or "") for alert in site.get("alerts") or []]
    blocks += list(site.get("totals") or []) + ([site["totalMme"]] if site.get("totalMme") else [])
    for molecule, expected_text in totals.items():
        names = [name for name in re.split(r"\s*/\s*|\s+moiety", molecule.lower()) if name and name != "combined opioid"]
        want = amounts_in(expected_text.split("=")[-1] if "MME" in expected_text and molecule == "combined opioid" else expected_text)
        weekly = [(value, unit) for value, unit in want if unit.endswith("/week")]
        if weekly:
            want = weekly[:1]
        elif "per week" in expected_text:
            want = [(value, unit + "/week") for value, unit in want[:1]]
        elif "/" in molecule and len(want) >= 2:
            want = want[:2]
        else:
            want = want[:1]
        relevant = [block for block in blocks if not names or any(name in block.lower() for name in names)]
        shown = [pair for block in relevant for pair in amounts_in(block)]
        if molecule == "risperidone moiety":
            ok = any("risperidone" in block.lower() and "paliperidone" in block.lower() for block in blocks)
        else:
            ok = bool(want) and all(any(abs(value - got) < 1e-6 and unit == got_unit for got, got_unit in shown) for value, unit in want)
        rows.append({"molecule": molecule, "expected": expected_text, "correct": ok, "site_shows": ", ".join(sorted({f"{v:g} {u}" for v, u in shown})) or "nothing for this molecule"})
    return rows


def covers_expected(found: set[str], key: dict) -> bool:
    """
    Takes an alert's ingredients and a list's answer-key entry.
    Checks whether the alert names every drug of some expected item, which makes it an expected flag even when one product on it also holds a should-not-flag ingredient (Truvada's emtricitabine next to its tenofovir).
    Gives True when some expected item is covered.
    """
    return any({i for drug in item["drugs"] for i in ingredients_of(drug)} <= found for item in key.get("expected") or [])


def false_positive_checks(list_id: str, key: dict, alerts: list[dict], alert_sets: list[set[str]]) -> list[dict]:
    """
    Takes a list ID, its answer-key entry, and the site's alerts with ingredient sets.
    Applies the control-list rule and the should_not_flag entries at pack grade B or above.
    Gives one row per false positive.
    """
    rows: list[dict] = []
    for alert, found in zip(alerts, alert_sets):
        grade = site_pack_grade(alert.get("grade"))
        if PACK_GRADE_RANK.get(grade or "", 0) < 2:
            continue
        if list_id in CONTROL_LISTS:
            rows.append({"rule": "control list: any flag at B or above", "drugs": alert.get("drugs"), "site_grade": alert.get("grade"), "category": alert.get("category")})
            continue
        for rule in key.get("should_not_flag") or []:
            drugs = set(ingredients_of(re.split(r" at | \(|;", rule)[0].replace(" with ", "/")))
            if drugs and drugs <= found and not (len(drugs) == 1 and is_duplication(alert)) and not (len(drugs) == 1 and covers_expected(found, key)):
                rows.append({"rule": rule, "drugs": alert.get("drugs"), "site_grade": alert.get("grade"), "category": alert.get("category")})
    return rows


def rows_for(ingredients_by_entry: list[set[str]]) -> list[RuleRow]:
    """
    Takes each entry's ingredient set for one list.
    Finds the rulebook rows whose sides are each met by a different entry, or whose burden pool reaches its count.
    Gives the matching rows in rulebook order.
    """
    matched: list[RuleRow] = []
    for rule in RULEBOOK:
        if rule.min_count:
            hits = {item for entry in ingredients_by_entry for item in entry if item in rule.pool}
            if len(hits) >= rule.min_count:
                matched.append(rule)
            continue
        if sides_met(rule.sides, ingredients_by_entry):
            matched.append(rule)
    return matched


def sides_met(sides: tuple[frozenset[str], ...], entries: list[set[str]]) -> bool:
    """
    Takes a row's drug sides and each entry's ingredients.
    Tries to assign each side to a distinct entry and a distinct drug, so one drug entered twice never meets a row by itself.
    Gives True when every side is met by a different entry holding a different drug.
    """
    def assign(index: int, used: frozenset[int], drugs: frozenset[str]) -> bool:
        if index == len(sides):
            return True
        return any(
            assign(index + 1, used | {position}, drugs | {drug})
            for position, entry in enumerate(entries) if position not in used
            for drug in entry & sides[index] if drug not in drugs
        )
    return assign(0, frozenset(), frozenset())


def row_drugs(rule: RuleRow, entries: list[set[str]]) -> set[str]:
    """
    Takes a rulebook row and each entry's ingredients.
    Collects the list's drugs that belong to the row.
    Gives the set of those ingredient names.
    """
    pool = rule.pool if rule.min_count else frozenset().union(*rule.sides)
    return {item for entry in entries for item in entry if item in pool}


def check_links(urls: list[str], cache_path: Path) -> dict[str, int]:
    """
    Takes URLs and a JSON cache file.
    Requests every URL not already cached, eight at a time.
    Gives the HTTP status by URL, 0 for a network failure.
    """
    cache: dict[str, int] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = [url for url in set(urls) if url not in cache]

    def fetch(url: str) -> tuple[str, int]:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (test-pack link check)"})
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return url, response.status
        except urllib.error.HTTPError as error:
            return url, error.code
        except (urllib.error.URLError, TimeoutError, OSError):
            return url, 0

    with ThreadPoolExecutor(max_workers=8) as pool:
        for url, status in pool.map(fetch, todo):
            cache[url] = status
    cache_path.write_text(json.dumps(cache, indent=1, sort_keys=True))
    return cache


def grade_run(pack_path: Path, run_dir: Path) -> dict:
    """
    Takes TEST_PACK.md and a run folder holding raw/<ID>.json captures.
    Scores every list and computes the pack's metrics.
    Gives the full evaluation as a dict and writes it to evaluation.json in the run folder.
    """
    lists, key = load_pack(pack_path)
    all_links: list[str] = []
    captures: dict[str, dict] = {}
    for list_id in lists:
        capture_path = run_dir / "raw" / f"{list_id}.json"
        captures[list_id] = json.loads(capture_path.read_text()) if capture_path.exists() else {"alerts": [], "meds": [], "links": [], "error": "no capture"}
        all_links.extend(link["href"] for link in captures[list_id].get("links") or [])
    status_by_url = check_links(all_links, run_dir / "link_status.json")
    per_list: dict[str, dict] = {}
    for list_id, line in lists.items():
        site = captures[list_id]
        entries = [parse_entry(part) for part in line.split(", ")]
        alerts = site.get("alerts") or []
        alert_sets = [alert_ingredients(alert, entries, site.get("meds") or []) for alert in alerts]
        items = [score_item(item, alerts, alert_sets, site, entries) for item in key[list_id]["expected"]]
        grouping = []
        for item in items:
            expected = {i for drug in item["drugs"] for i in ingredients_of(drug)}
            if len(set(item["drugs"])) >= 3 and item["category"] not in DUPLICATE_CATEGORIES | HANDLING_CATEGORIES | {"dose ceiling"}:
                present = any(
                    expected <= found and re.search(category_pattern(item["category"]), alert_text(alert), re.I)
                    and re.search(r"\b(\d+|two|three|four|five|six)\b\s+(?:[\w-]+\s+){0,3}?(?:drugs|medications|medicines|\w+ants|\w+s)\b", alert.get("category") or "", re.I)
                    for alert, found in zip(alerts, alert_sets)
                )
                grouping.append({"drugs": item["drugs"], "category": item["category"], "present": present})
        links_by_alert = []
        for alert in alerts:
            specific = [link["href"] for link in alert.get("links") or [] if DRUG_SPECIFIC.search(link["href"])]
            primary = [link["href"] for link in alert.get("links") or [] if PRIMARY_SOURCE.search(link["href"])]
            links_by_alert.append({
                "drugs": alert.get("drugs"), "grade": alert.get("grade"),
                "specific_working": any(200 <= status_by_url.get(url, 0) < 300 for url in specific),
                "primary_working": any(200 <= status_by_url.get(url, 0) < 300 for url in primary),
            })
        by_entry = [set(entry.ingredients) for entry in entries]
        rulebook = []
        for rule in rows_for(by_entry):
            drugs = row_drugs(rule, by_entry)
            flagged = [alert for alert, found in zip(alerts, alert_sets) if len(found & drugs) >= 2 or (len(drugs) == 1 and drugs <= found)]
            named = any(re.search(rule.syndrome, alert_text(alert), re.I) for alert in flagged)
            rulebook.append({"row": rule.number, "name": rule.name, "drugs": sorted(drugs), "flagged": bool(flagged), "named": named})
        unresolved_cards = {(med.get("brand") or "").strip() for med in site.get("meds") or [] if UNRESOLVED.search(med.get("text") or "")}
        not_found = [entry.raw for entry in entries if entry.raw.strip() in unresolved_cards or re.search(re.escape(entry.raw) + r"\s*:\s*not found", site.get("text") or "")]
        per_list[list_id] = {
            "input": line, "items": items, "false_positives": false_positive_checks(list_id, key[list_id], alerts, alert_sets),
            "totals": score_totals(key[list_id].get("totals") or {}, site), "grouping": grouping, "links": links_by_alert,
            "rulebook": rulebook, "not_found": not_found, "alerts": [{"grade": a.get("grade"), "pack_grade": site_pack_grade(a.get("grade")), "drugs": a.get("drugs"), "category": a.get("category"), "ingredients": sorted(s)} for a, s in zip(alerts, alert_sets)],
            "seconds": site.get("secondsToResults"), "focused": site.get("focusedOnLoad"), "defects": site.get("defects") or [],
            "console_errors": site.get("consoleErrors") or [], "bad_responses": site.get("badResponses") or [],
            "theme": key[list_id].get("theme"),
        }
    summary = summarize(per_list, lists, key)
    result = {"summary": summary, "lists": per_list}
    (run_dir / "evaluation.json").write_text(json.dumps(result, indent=1))
    return result


def summarize(per_list: dict[str, dict], lists: dict[str, str], key: dict) -> dict:
    """
    Takes the per-list scores.
    Computes recall by grade, precision, false positives, totals, duplicates, grouping, links, rulebook coverage, and timing.
    Gives the metrics as a dict.
    """
    recall: dict[str, dict[str, int]] = {grade: {"expected": 0, "hit": 0, "partial": 0} for grade in "DCBA"}
    for scores in per_list.values():
        for item in scores["items"]:
            bucket = recall[item["pack_grade"]]
            bucket["expected"] += 1
            bucket["hit"] += item["status"] == "HIT"
            bucket["partial"] += item["status"] == "PARTIAL"
    precision: dict[str, dict[str, int]] = {grade: {"shown": 0, "supported": 0} for grade in "DCBA"}
    for list_id, scores in per_list.items():
        expected_sets = [{i for d in item["drugs"] for i in ingredients_of(d)} for item in key[list_id]["expected"]]
        for alert in scores["alerts"]:
            grade = alert["pack_grade"] or "A"
            found = set(alert["ingredients"])
            supported = any((exp <= found) or (len(found) >= 2 and found <= exp) for exp in expected_sets)
            precision[grade]["shown"] += 1
            precision[grade]["supported"] += supported
    totals = [row for scores in per_list.values() for row in scores["totals"]]
    duplicates = [item for scores in per_list.values() for item in scores["items"] if item["category"] in DUPLICATE_CATEGORIES | HANDLING_CATEGORIES]
    grouping = [row for scores in per_list.values() for row in scores["grouping"]]
    links = [row for scores in per_list.values() for row in scores["links"]]
    cd_links = [row for row in links if PACK_GRADE_RANK.get(site_pack_grade(row["grade"]) or "", 0) >= 3]
    coverage: dict[int, dict] = {rule.number: {"name": rule.name, "applies": 0, "flagged": 0, "named": 0, "lists": []} for rule in RULEBOOK}
    for list_id, scores in per_list.items():
        for entry in scores["rulebook"]:
            cell = coverage[entry["row"]]
            cell["applies"] += 1
            cell["flagged"] += entry["flagged"]
            cell["named"] += entry["named"]
            cell["lists"].append(f"{list_id}{'' if entry['named'] else ('~' if entry['flagged'] else '✗')}")
    seconds = [scores["seconds"] for scores in per_list.values() if isinstance(scores["seconds"], (int, float))]
    control_fp = sum(len(per_list[list_id]["false_positives"]) for list_id in CONTROL_LISTS if list_id in per_list)
    return {
        "recall": recall, "precision": precision,
        "false_positives_total": sum(len(scores["false_positives"]) for scores in per_list.values()), "false_positives_controls": control_fp,
        "totals_correct": sum(row["correct"] for row in totals), "totals_expected": len(totals),
        "duplicate_cases": len(duplicates), "duplicate_resolved": sum(item["status"] == "HIT" for item in duplicates),
        "grouping_expected": len(grouping), "grouping_present": sum(row["present"] for row in grouping),
        "flags_shown": len(links), "flags_with_working_primary_link": sum(row["primary_working"] for row in links),
        "flags_with_working_specific_link": sum(row["specific_working"] for row in links),
        "cd_flags": len(cd_links), "cd_flags_with_working_specific_link": sum(row["specific_working"] for row in cd_links),
        "coverage": coverage, "median_seconds": statistics.median(seconds) if seconds else None, "worst_seconds": max(seconds) if seconds else None,
        "lists_scored": len(per_list), "entries_not_found": sum(len(scores["not_found"]) for scores in per_list.values()),
        "entries_total": sum(len(line.split(", ")) for line in lists.values()),
        "focused_on_load": sum(bool(scores["focused"]) for scores in per_list.values()),
    }


if __name__ == "__main__":
    evaluation = grade_run(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps({k: v for k, v in evaluation["summary"].items() if k != "coverage"}, indent=1))
