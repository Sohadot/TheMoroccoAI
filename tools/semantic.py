"""Semantic-risk checks for Arabic and French translations (Sprint 19B-5; policy TMA-DEC-008).

    findings(source, text, lang, terms=None) -> [Finding(code, severity, message), ...]

Two severities, deliberately different in strength:

- error: a deterministic, reliable mismatch with the English source: a month name, a number, a scale word
  (million, billion), a canonical classification code, or an approved glossary label that is missing or changed.
  An approved unit with an error fails validation and is never rendered.
- warning: a lexical signal that meaning MAY have changed: negation, hedging, plans or targets presented as
  done, attribution, verification language, added causation, comparisons, legal terminology, acronyms,
  unusual length, untranslated English. Warnings are shown to the human reviewer and must be acknowledged in
  the approval (approval.acknowledged_warnings); they are review aids, not verdicts.

Limits, stated plainly: these are word lists and patterns. They miss paraphrases, cannot read context, and can
fire on correct translations. Passing them is not evidence of equivalence; meaning is established only by the
documented human approval. No network call, no model, no external service. Standard library only.
"""
import re
from collections import Counter, namedtuple

Finding = namedtuple("Finding", "code severity message")
PLACEHOLDER = re.compile(r"\{[a-z_][a-z0-9_]*\}")
DIGITS = re.compile(r"\d+")
IDENTIFIERS = re.compile(r"MAI-[A-Z0-9]+(?:-[A-Z0-9]+)*|https?://\S+")
CLASSIFICATION_CODES = ("VERIFIED FACT", "OFFICIAL TARGET", "ANNOUNCED PLAN", "INDEPENDENT ANALYSIS", "UNVERIFIED CLAIM")
MONTHS_EN = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December")
# Accepted month names: Moroccan usage first, then the forms common elsewhere in Modern Standard Arabic.
MONTHS = {
    "ar": (("يناير", "كانون الثاني"), ("فبراير", "شباط"), ("مارس", "آذار"), ("أبريل", "ابريل", "نيسان"),
           ("ماي", "مايو", "أيار"), ("يونيو", "يونيه", "حزيران"), ("يوليوز", "يوليو", "تموز"), ("غشت", "أغسطس", "آب"),
           ("شتنبر", "سبتمبر", "أيلول"), ("أكتوبر", "اكتوبر", "تشرين الأول"), ("نونبر", "نوفمبر", "تشرين الثاني"),
           ("دجنبر", "ديسمبر", "كانون الأول")),
    "fr": (("janvier",), ("février",), ("mars",), ("avril",), ("mai",), ("juin",), ("juillet",), ("août",),
           ("septembre",), ("octobre",), ("novembre",), ("décembre",)),
}
SCALE = {"million": {"ar": ("مليون", "ملايين"), "fr": ("million",)},
         "billion": {"ar": ("مليار", "مليارات"), "fr": ("milliard",)}}

# Lexical signals by category: (English pattern, {lang: target pattern}). Arabic patterns match whole tokens
# with the usual attached prefixes (و ف ب ل ك ال); French patterns match word starts.
_AR_PREFIX = r"(?:^|(?<=[\s\(\[«\"'،؛:.]))(?:و|ف)?(?:ب|ل|ك)?(?:ال)?"
_AR_END = r"(?=$|[\s\)\]»\"'،؛:.؟!])"


def _ar(*words):
    return re.compile(_AR_PREFIX + "(?:" + "|".join(map(re.escape, words)) + ")" + _AR_END)


def _ar_stem(*stems):
    return re.compile(_AR_PREFIX + "(?:" + "|".join(map(re.escape, stems)) + r")\w*")


def _fr(*stems):
    return re.compile(r"(?i)(?<![\w])(?:" + "|".join(map(re.escape, stems)) + r")")


def _en(*words):
    return re.compile(r"(?i)(?<![\w-])(?:" + "|".join(words) + r")(?![\w])")


SIGNALS = {
    "NEGATION": (_en("not", "no", "never", "none", "nothing", "cannot", "without", "neither", "nor", r"\w+n't", "non", "absence", "absent"),
                 {"ar": _ar("لا", "لم", "لن", "ليس", "ليست", "ليسا", "غير", "دون", "بدون", "عدم", "لا يوجد"),
                  "fr": _fr("ne ", "n'", "n’", "pas ", "pas.", "pas,", "jamais", "aucun", "sans ", "ni ", "non ", "non-", "absence")}),
    "HEDGE": (_en("may", "might", "could", "possibly", "possible", "likely", "unlikely", "appears?", "seems?", "suggests?"),
              {"ar": _ar_stem("قد ", "ربما", "يحتمل", "محتمل", "احتمال", "يبدو", "يرجح", "مرجح", "يشير", "تشير"),
               "fr": _fr("peut", "peuvent", "pourrai", "possible", "probab", "sembl", "paraît", "suggère", "indique")}),
    "PLAN": (_en("will", "plans?", "planned", "aims?", "intends?", "targets?", "expected", "announced", "proposed", r"by \d{4}"),
             {"ar": _ar_stem("سوف", "يعتزم", "تعتزم", "يهدف", "تهدف", "هدف", "أهداف", "مستهدف", "خطة", "مخطط",
                             "مزمع", "متوقع", "المتوقع", "أعلن", "معلن", "إعلان", "مقترح", "بحلول", "مرتقب"),
              "fr": _fr("prévu", "prévoit", "vise", "objectif", "cible", "sera", "seront", "devrai", "annonc", "envisag",
                        "projet", "d'ici", "d’ici", "proposé", "attendu")}),
    "ATTRIBUTION": (_en("reported", "reportedly", "according to", "states?", "stated", "says", "said", "claims?", "claimed",
                        "presented", "describes?", "its authors"),
                    {"ar": _ar_stem("وفق", "بحسب", "حسب", "أفاد", "يفيد", "تفيد", "يذكر", "تذكر", "ذكر", "ادعا", "يدعي", "تدعي",
                                    "يقول", "تقول", "صرح", "قدم", "يقدم", "تقدم", "يصف", "تصف", "مؤلف", "أعلن", "تعلن", "يعلن"),
                     "fr": _fr("selon", "d'après", "d’après", "indique", "déclar", "affirm", "rapport", "signal", "présent",
                               "revendiqu", "décri", "auteur", "annonc")}),
    "VERIFICATION": (_en("verified", "verify", "verification", "confirmed", "reconfirmed", "established", "documented",
                         "unverified"),
                     {"ar": _ar_stem("تحقق", "متحقق", "التحقق", "مؤكد", "تأكيد", "أكد", "ثبت", "يثبت", "مثبت", "موثق", "توثيق", "وثق"),
                      "fr": _fr("vérifi", "confirm", "établi", "document", "attest", "constat")}),
    "COMPARISON": (_en("more than", "less than", "fewer than", "at least", "at most", "up to", "exceeds?", "higher than",
                       "lower than", "over"),
                   {"ar": _ar_stem("أكثر", "أقل", "على الأقل", "على الأكثر", "يتجاوز", "تتجاوز", "يفوق", "تفوق", "أعلى", "أدنى",
                                   "ما يصل", "حتى", "فوق", "يزيد", "تزيد"),
                    "fr": _fr("plus de", "moins de", "au moins", "au plus", "jusqu'à", "jusqu’à", "dépass", "supérieur",
                              "inférieur", "excède")}),
    "LEGAL": (_en("law", "laws", "decree", "regulations?", "legal", "legally", "statute", "binding", "compliance",
                  "personal data", "legal entity"),
              {"ar": _ar_stem("قانون", "القانون", "مرسوم", "تنظيم", "نظام", "قانوني", "ملزم", "امتثال", "معطيات", "البيانات الشخصية",
                              "شخص اعتباري", "كيان قانوني"),
               "fr": _fr("loi", "décret", "règlement", "réglement", "juridique", "légal", "contraign", "conformité",
                         "données personnelles", "personne morale", "entité juridique")}),
}
CAUSATION = (_en("because", "caused", "causes?", "due to", "leads? to", "led to", "results? in", "therefore", "thanks to"),
             {"ar": _ar_stem("بسبب", "نتيجة", "يؤدي", "تؤدي", "أدى", "أدت", "لذلك", "بفضل", "بالتالي"),
              "fr": _fr("à cause", "en raison", "grâce à", "entraîn", "provoqu", "conduit à", "donc", "par conséquent", "causé")})
# Acronyms that are normally translated, with their accepted renderings.
TRANSLATED_ACRONYMS = {
    "AI": {"ar": ("الذكاء الاصطناعي", "ذكاء اصطناعي", "للذكاء الاصطناعي", "بالذكاء الاصطناعي"), "fr": ("IA", "intelligence artificielle")},
    "GDP": {"ar": ("الناتج الداخلي الخام", "الناتج المحلي الإجمالي"), "fr": ("PIB",)},
    "MAD": {"ar": ("درهم", "MAD"), "fr": ("dirham", "MAD")},
    "JSON": {"ar": ("JSON",), "fr": ("JSON",)},
}
LENGTH_BOUNDS = {"ar": (0.45, 1.9), "fr": (0.75, 1.9)}


def _visible(text):
    return PLACEHOLDER.sub(" ", text)


def _month_positions(source):
    """English month names: capitalised words. 'May' at the start of a sentence with no number beside it is
    read as the modal verb and not counted."""
    found = []
    for i, name in enumerate(MONTHS_EN):
        for m in re.finditer(rf"(?<![\w-]){name}(?![\w-])", source):
            if name == "May" and re.search(r"(?:^|[.!?:]\s+)$", source[:m.start()]) \
                    and not re.match(r"\s+\d", source[m.end():]):
                continue
            found.append(i)
    return Counter(found)


def _target_months(text, lang):
    text = IDENTIFIERS.sub(" ", text)  # 'MAI-EV-0048' is not the French month 'mai'
    found = Counter()
    for i, names in enumerate(MONTHS[lang]):
        for name in sorted(names, key=len, reverse=True):
            n = len(re.findall(rf"(?<!\w){re.escape(name)}(?!\w)", text, flags=re.I))
            if n:
                found[i] += n
                break
    return found


def findings(source, text, lang, terms=None, required=()):
    """Semantic-risk findings for one translated unit. `terms` maps an English term form (as it appears in
    English prose) to its approved label in `lang`. For the forms in `required` (the unit is linked to that
    glossary term) a missing label is an error; elsewhere it is a warning, because prose may use the word
    generically or in an inflected form the check cannot recognise."""
    if lang not in MONTHS or not isinstance(text, str) or not isinstance(source, str):
        return []
    out = []
    src, tgt = _visible(source), _visible(text)

    # ── errors: deterministic mismatches ──
    months_src, months_tgt = _month_positions(source), _target_months(text, lang)
    for i in sorted(set(months_src) | set(months_tgt)):
        if months_src[i] != months_tgt[i]:
            out.append(Finding("DATE_MONTH", "error", f"month {MONTHS_EN[i]} occurs {months_src[i]} time(s) in English and "
                               f"{months_tgt[i]} time(s) in the translation"))
    missing = Counter(DIGITS.findall(src)) - Counter(DIGITS.findall(tgt))
    if missing:
        out.append(Finding("NUMBER_MISSING", "error", f"numbers {sorted(missing)} of the English source are missing"))
    for word, forms in SCALE.items():
        n_src = len(re.findall(rf"(?i)\b{word}s?\b", src))
        n_tgt = sum(len(re.findall(re.escape(f), tgt, flags=re.I)) for f in forms[lang])
        if n_src and n_tgt < n_src:
            out.append(Finding("SCALE_WORD", "error", f"'{word}' ({n_src}x) is not rendered with {list(forms[lang])}: "
                               "the quantity's scale may have changed"))
    for code in CLASSIFICATION_CODES:
        if source.count(code) != text.count(code):
            out.append(Finding("CLASSIFICATION_CODE", "error", f"classification code {code!r} must stay verbatim"))
    for english, label in sorted((terms or {}).items()):
        if english in required and label.lower() not in tgt.lower():
            out.append(Finding("TERM_MISSING", "error", f"the approved {lang} label {label!r} for {english!r} is not used"))

    # ── warnings: lexical signals for the human reviewer ──
    for code, (en_pattern, targets) in SIGNALS.items():
        n_src, n_tgt = len(en_pattern.findall(src)), len(targets[lang].findall(tgt))
        if n_src and not n_tgt:
            out.append(Finding(f"{code}_LOST", "warning", f"the English has {code.lower()} language "
                               f"({', '.join(sorted(set(m.strip().lower() for m in en_pattern.findall(src))))}); the translation shows none"))
        elif code == "NEGATION" and n_tgt and not n_src:
            out.append(Finding("NEGATION_ADDED", "warning", "the translation has negation that the English does not"))
    for english, label in sorted((terms or {}).items()):
        if english not in required and re.search(rf"(?i)(?<![\w-]){re.escape(english)}s?(?![\w-])", src) \
                and label.lower() not in tgt.lower():
            out.append(Finding("TERM_NOT_USED", "warning", f"{english!r} occurs; the approved {lang} label {label!r} does not"))
    if CAUSATION[1][lang].search(tgt) and not CAUSATION[0].search(src):
        out.append(Finding("CAUSATION_ADDED", "warning", "the translation states a cause or consequence that the English does not"))
    acronyms = set(re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", src)) - set(" ".join(CLASSIFICATION_CODES).split())
    for acronym in sorted(a for a in acronyms if not re.fullmatch(r"[IVXLC]+", a)):  # Roman numerals are not acronyms
        forms = TRANSLATED_ACRONYMS.get(acronym, {}).get(lang, ())
        if acronym not in tgt and not any(f.lower() in tgt.lower() for f in forms):
            out.append(Finding("ACRONYM_MISSING", "warning", f"{acronym!r} does not appear in the translation; check the "
                               "institution or abbreviation is rendered correctly"))
    words = len(re.findall(r"[A-Za-z]{2,}", src))
    if len(src.strip()) >= 40 and words >= 6:
        low, high = LENGTH_BOUNDS[lang]
        ratio = len(tgt.strip()) / max(1, len(src.strip()))
        if not low <= ratio <= high:
            out.append(Finding("LENGTH_RATIO", "warning", f"translation length is {ratio:.2f}x the English: possible omission or addition"))
    latin_run = re.search(r"(?:\b[A-Za-z]{3,}\b[\s,]+){3,}\b[A-Za-z]{3,}\b", tgt) if lang == "ar" else None
    if latin_run or (words >= 3 and src.strip() == tgt.strip()):
        out.append(Finding("UNTRANSLATED", "warning", "English text appears untranslated"))
    return out


def warning_codes(found):
    return sorted({f.code for f in found if f.severity == "warning"})


def error_messages(found):
    return [f"{f.code}: {f.message}" for f in found if f.severity == "error"]
