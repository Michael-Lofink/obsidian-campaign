# Validation record

Validation performed October 10, 2026, on Linux, Python 3.14.8, Beautiful Soup 4.15.0.

## Live sources checked

Each source was fetched separately with no adjustment, `Weak=true`, and `Elite=true`, always with `NoRedirect=1`:

| Creature | AoN page | Normal / Weak / Elite levels | HP | AC |
| --- | --- | --- | --- | --- |
| Apothecary | [NPCs.aspx ID=3479](https://2e.aonprd.com/NPCs.aspx?ID=3479&NoRedirect=1) | -1 / -2 / 1 | 8 / 8 / 18 | 14 / 12 / 16 |
| Lich, remastered | [Monsters.aspx ID=3082](https://2e.aonprd.com/Monsters.aspx?ID=3082&NoRedirect=1) | 12 / 11 / 13 | 190 / 170 / 210 | 31 / 29 / 33 |
| Ice Linnorm, remastered | [Monsters.aspx ID=3084](https://2e.aonprd.com/Monsters.aspx?ID=3084&NoRedirect=1) | 17 / 16 / 18 | 330 / 310 / 350 | 41 / 39 / 43 |

All nine downloads were parsed successfully, without parser warnings. The finished CLI then fetched all nine URLs again and wrote the included example files. Their statblock contents match the saved HTML conversions exactly. HTML document hashes can differ because AoN includes unrelated page/session state; the output preserves the exact hash of its actual input.

## Apothecary comparison with the supplied example

The live source agrees with the supplied example on levels, Recall Knowledge DCs (13/12/15), Perception, situational Crafting bonuses, the other skills, attributes, AC/saves/resistance, items, abilities, attack modifiers, all three MAP pairs, Strike damage, and acid-flask effects.

**Difference:** Normal and Weak HP are **8** on the retrieved source, versus **9** in the supplied example. Elite HP is **18** in both. The converter follows the live source; it does not try to decide which value the book intended.

Formatting differences are deliberate: retained inline links, readable spaces around action tokens, separate paragraphs for abilities/attacks, the source's comma before acid-flask Effect, and an attribution/link appendix. Duplicate parentheses in the source's Crafting modifier are normalized to the single pair in the example. Numeric values are not normalized or recalculated.

## Complex content checked

**Lich:** All 26 spell-list links plus the scroll's spell link; spell ranks and cantrip rank; repeated spell counts; spell DC and attack adjustments; printed `(-4 dmg)` / `(+4 dmg)` reminders; Counterspell reaction and trigger/effect text; free-action Drain Soul Cage; Siphon Life DC; Steady Spellcasting; senses, languages, items, Frightful Presence, defenses, and hand attack/MAP.

AoN abbreviates some Lich abilities in its individual statblock. For example, it prints Drain Soul Cage as “6th rank” and Siphon Life as a DC. The export preserves those entries; it does not pull the longer family rules into the statblock or invent descriptions.

**Ice Linnorm:** Multi-mode movement; regeneration, immunities and weaknesses; Reactive Strike reaction; reach and agile attack traits/MAP; innate and constant spells; Constrict; venom stages and duration; complete two-action Icemire Breath text, including ongoing damage, escape conditions, and recharge. The source's unsimplified adjusted dice and unchanged non-Strike damage are preserved along with its caveat.

## Automated coverage

Run `python -m unittest discover -s tests -v` using the configured environment. The 14 tests cover:

- Independent full-body comparison of the ordered source text against Markdown for all nine pages, ignoring presentation punctuation; an additional comparison retains plus/minus signs.
- Every hyperlink in the selected source statblocks appears inline or in the additional-link registry.
- Explicit expected Apothecary values transcribed from the live pages, including situational skills and all attacks/MAP.
- Explicit complex spellcasting/ability checks for Lich and Ice Linnorm.
- Three fenced blocks, ordering, headings, separators, attribution, provenance, and two adjustment warnings.
- All five action tokens; negative damage split across AoN highlighting spans; nested list indentation (synthetic cases).
- Unsupported URL modes/hosts, duplicate IDs, missing required data, tables, unknown action symbols, wrong creature/variant, and missing Recall Knowledge.
- Offline operation, output overwrite protection, and no Markdown output when an input is missing.
- Included live-generated example blocks match the fixture conversions.

The three-action glyph and nested-list cases are synthetic tests, not claims about those features being present in these live creatures. No whole-catalog, Obsidian rendering, UI, or Windows/macOS runtime validation was performed. No calculated variant was used as a fallback.
