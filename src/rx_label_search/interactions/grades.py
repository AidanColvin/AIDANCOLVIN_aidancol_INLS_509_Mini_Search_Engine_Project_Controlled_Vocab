"""Pure severity grading, A to E, from the label section and the label's own words about using the drugs together."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rx_label_search.records import Alert, AlertEvidence

GRADE_ORDER: tuple[str, ...] = ("A", "B", "C", "D", "E")


@dataclass(frozen=True)
class GradeInfo:
    """One severity grade: its letter, short name, meaning, and the Lexicomp level it lines up with."""

    letter: str
    name: str
    meaning: str
    lexicomp: str


GRADES: dict[str, GradeInfo] = {
    "E": GradeInfo("E", "Avoid combination", "Do not use these drugs together.", "X"),
    "D": GradeInfo("D", "Consider changing therapy", "Dangerous: avoid, or use only with a specific reason and close monitoring.", "D"),
    "C": GradeInfo("C", "Monitor closely", "Clinically significant: adjust the dose or timing, or monitor a named measure.", "C"),
    "B": GradeInfo("B", "Monitor", "Real but manageable: monitor.", "C"),
    "A": GradeInfo("A", "Minor", "Minor: usually no action needed.", "B"),
}

_WARNING_SECTIONS: frozenset[str] = frozenset({"warnings_and_cautions", "warnings", "precautions"})
_SECTION_NAMES: dict[str, str] = {
    "contraindications": "Contraindications",
    "boxed_warning": "Boxed Warning",
    "warnings_and_cautions": "Warnings and Precautions",
    "warnings": "Warnings",
    "precautions": "Precautions",
    "drug_interactions": "Drug Interactions",
}
_AVOID = re.compile(r"\b(avoid\w*|not recommended|(?:do|must|should) not (?:be )?(?:use|used|take|taken|co-?administer\w*|combine\w*))\b", re.I)
_TOGETHER = re.compile(r"\b(concomitant\w*|combination\w*|combined|co-?administ\w*|together|with other|in combination)\b", re.I)
_ACTION = re.compile(r"\b(monitor\w*|caution\w*|closely|dose (?:reduction|adjustment)|(?:reduce|adjust|lower|decrease)\w* (?:the )?(?:dose|dosage))\b", re.I)


@dataclass(frozen=True)
class MemberGrade:
    """The grade one alert member's label sentence earns, and why."""

    letter: str
    basis: str


def section_name(section: str) -> str:
    """
    Takes a label field name such as "warnings_and_cautions".
    Looks up the section's display name.
    Gives the display name, or the field name unchanged when it is not one of the graded sections.
    """
    return _SECTION_NAMES.get(section, section)


def avoid_together_phrase(sentence: str) -> str | None:
    """
    Takes one label sentence.
    Finds an "avoid", "not recommended", or "do not use" statement, counting it only when the same sentence is about using drugs together.
    Gives the matched avoid phrase, or None when the sentence has none or speaks only about the patient.
    """
    avoid = _AVOID.search(sentence)
    if avoid is None or _TOGETHER.search(sentence) is None:
        return None
    return avoid.group(0)


def action_phrase(sentence: str) -> str | None:
    """
    Takes one label sentence.
    Finds a monitor, caution, or dose-adjustment instruction in it.
    Gives the matched phrase, or None when the sentence states no action.
    """
    found = _ACTION.search(sentence)
    return None if found is None else found.group(0)


def grade_member(member: AlertEvidence, kind: str) -> MemberGrade | None:
    """
    Takes one alert member and the alert's kind.
    Grades its sentence: a pair contraindication is E; a boxed warning or an avoid-together statement is D; a warning section is C; a drug-interactions sentence with an action is B, without one A.
    Gives the MemberGrade, or None when the member carries no sentence or its section is not graded.
    """
    if not member.sentence or not member.section:
        return None
    where = f"{section_name(member.section)} section of the {member.drug_name} label"
    if member.section == "contraindications" and kind == "pair":
        return MemberGrade("E", f"The {where} names this combination as contraindicated.")
    if member.section == "contraindications":
        return MemberGrade("D", f"The risk is stated in the {where}.")
    if member.section == "boxed_warning":
        return MemberGrade("D", f"The risk is a boxed warning in the {member.drug_name} label.")
    avoid = avoid_together_phrase(member.sentence)
    if avoid is not None:
        return MemberGrade("D", f'The {where} says "{avoid}" about using them together.')
    if member.section in _WARNING_SECTIONS:
        return MemberGrade("C", f"The risk is stated in the {where}.")
    if member.section == "drug_interactions":
        action = action_phrase(member.sentence)
        if action is not None:
            return MemberGrade("B", f'The {where} says "{action}".')
        return MemberGrade("A", f"The {where} notes the interaction without an action.")
    return None


def duplication_grade(alert: Alert) -> MemberGrade:
    """
    Takes one duplication alert.
    Grades it C, since two entries of one drug add to a single higher daily dose.
    Gives the MemberGrade, naming whether the entries share an ingredient or one is the other's active metabolite.
    """
    if alert.risk == "active_metabolite":
        return MemberGrade("C", "One drug is the other's active metabolite, so they act as one drug at a higher dose.")
    return MemberGrade("C", "Two entries share an active ingredient, so their daily amounts add together.")


def grade_alert(alert: Alert) -> MemberGrade:
    """
    Takes one alert.
    Grades every member's sentence and keeps the most severe, so an alert is as serious as its strongest label statement.
    Gives the MemberGrade, grade A with a stated basis when no member's sentence can be graded.
    """
    if alert.grade in GRADES:
        return MemberGrade(alert.grade, alert.basis or GRADES[alert.grade].meaning)
    if alert.kind == "duplication":
        return duplication_grade(alert)
    graded = [grade for grade in (grade_member(member, alert.kind) for member in alert.members) if grade is not None]
    if not graded:
        return MemberGrade("A", "No member sentence came from a graded label section.")
    return max(graded, key=lambda grade: GRADE_ORDER.index(grade.letter))


def grade_fields(alert: Alert) -> dict[str, str]:
    """
    Takes one alert.
    Grades it and spells the grade out for the API.
    Gives the grade letter, name, meaning, the Lexicomp level it lines up with, and the basis sentence.
    """
    grade = grade_alert(alert)
    info = GRADES[grade.letter]
    return {
        "grade": info.letter,
        "grade_name": info.name,
        "grade_meaning": info.meaning,
        "grade_lexicomp": info.lexicomp,
        "grade_basis": grade.basis,
    }
