# Archives of Nethys → Obsidian statblocks

Convert one Archives of Nethys PF2e NPC or monster URL into one Markdown document containing **Normal, Weak, and Elite** `pf2e-stats` blocks, in that order.

The tool downloads and parses each variant's HTML independently. It never calculates levels, bonuses, HP, damage, DCs, or MAP. It needs Python 3.10+ and Beautiful Soup; no API key, account, browser automation, or server is needed.

## Quick start

Open a terminal in this folder. On macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python aon_to_obsidian.py "https://2e.aonprd.com/NPCs.aspx?ID=3479&NoRedirect=1" -o Apothecary.md
```

On Windows (PowerShell or Command Prompt):

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe aon_to_obsidian.py "https://2e.aonprd.com/NPCs.aspx?ID=3479&NoRedirect=1" -o Apothecary.md
```

Always quote the URL: shells treat `&` specially. After setup, only the last command is needed. Replace the URL and output filename for another creature. Omitting `-o` uses the creature's name. You can write directly into your Obsidian vault using a quoted output path.

```sh
.venv/bin/python aon_to_obsidian.py "https://2e.aonprd.com/Monsters.aspx?ID=3082" -o "/home/michaellofink/Documents/PF2e-Duet-Campaign-Notes/Campaign/Resources/Beastiary/Level X/CreatureType/Lich.md"
```

Open the resulting `.md` file in Obsidian with the same `pf2e-stats` renderer you use for your Apothecary example. Without a compatible renderer, the contents display as readable fenced code blocks. Visual rendering inside Obsidian has **not** been tested here.

Ready-made live exports are in [examples/Apothecary.md](examples/Apothecary.md), [examples/Lich.md](examples/Lich.md), and [examples/Ice-Linnorm.md](examples/Ice-Linnorm.md).

### Embed a single variant in Obsidian

Each block has its own level-two heading outside the code fence. For a note named `Apothecary.md`, use:

```text
![[Apothecary#Normal Apothecary]]
![[Apothecary#Weak Apothecary]]
![[Apothecary#Elite Apothecary]]
```

The document has no extra overall title because Obsidian already displays the filename. The creature name inside each `pf2e-stats` block remains part of the statblock. All variant and appendix headings share the same level, so embedding Elite does not also include the attribution appendix.

## Options and offline use

```text
URL                       Required NPCs.aspx or Monsters.aspx URL with ID
-o, --output PATH         Output Markdown filename
--force                   Replace an existing output (otherwise it is protected)
--timeout SECONDS         Per-attempt HTTP timeout; default 30
--save-html-dir DIRECTORY Save the three downloaded HTML inputs
--html-dir DIRECTORY      Read normal.html, weak.html, elite.html without networking
-h, --help                Show help
```

Save inputs for later reuse:

```sh
.venv/bin/python aon_to_obsidian.py "https://2e.aonprd.com/NPCs.aspx?ID=3479" --save-html-dir saved-apothecary -o Apothecary.md
```

Convert saved inputs while offline, or use the supplied validation snapshots:

```sh
.venv/bin/python aon_to_obsidian.py "https://2e.aonprd.com/NPCs.aspx?ID=3479" --html-dir tests/fixtures/apothecary -o Apothecary.md --force
```

For manually saved HTML, use complete HTML source from **each** corresponding page, named `normal.html`, `weak.html`, and `elite.html`. The URL still identifies the expected creature; the parser checks the ID and adjustment labels. Use a new snapshot folder to retain earlier captures. The output records source URLs, conversion time, and input SHA-256 hashes. For offline inputs, conversion time is not a claim about when they were downloaded.

## What is retained

- Creature name, level, rarity/size/other traits, book/page citations, and source links.
- Recall Knowledge exactly as AoN provides it, including rarity notes; no inferred Lore DCs.
- Senses, languages, skills including situational modifiers, attributes, items, and special abilities.
- AC, saves, HP, weaknesses, resistances, immunities, regeneration, reactions, and other defensive text.
- Movement, attacks, printed MAP pairs, dice expressions, traits, effects, and offensive abilities.
- Spell traditions, ranks, slots/counts, constant spells, cantrips, spell DCs, attack modifiers, and links.
- One/two/three-action, free-action, and reaction symbols as backticked tokens such as `[one-action]`.
- AoN's Weak/Elite warning about unapplied non-Strike damage and any printed spell damage reminders.

The format follows the supplied Apothecary example: `# Name`, `## Creature N`, highlighted traits, bold labels, and blank lines around `---` section separators. It retains more inline hyperlinks than the handwritten example. Links belonging to plain field labels, header traits, or MAP pairs are retained under **Additional source links**, outside the three statblocks, so these fields remain legible.

Presentation cleanup removes AoN's adjustment highlighting and the resulting obsolete “Changes are marked” sentence, reduces duplicate simple parentheses, removes commas between attributes, and renders the Recall Knowledge bullet as `*`. It does not correct source rules or simplify dice expressions.

## Limits and errors

- Verified against the current AoN HTML structure on **October 10, 2026**. This is not a claim of full-catalog compatibility. See [VALIDATION.md](VALIDATION.md).
- The exact supplied ID is pinned with `NoRedirect=1`. A legacy ID stays legacy even if the browser normally redirects it to a remastered replacement. Use the remastered ID if that is the edition you want.
- An input containing `Weak=true` or `Elite=true` still exports all three variants. Proficiency Without Level (`PWL`) and other query modes are rejected to avoid silently changing the requested rules.
- This exports the printed statblock. It does not include introductory lore, family rules, related-creature tables, images, or dynamically loaded spell descriptions. Abbreviated abilities remain abbreviated when AoN prints them that way. Use the retained links and top-level source-page links for referenced rules, including unlinked family abilities.
- Source errors remain source errors. For example, the retrieved Ice Linnorm HP line has an unclosed parenthesis; its Weak jaws damage is printed as `3d12-2+17`. Neither is silently repaired.
- Missing essential numeric fields, incorrect creature/variant identity, unfamiliar core layout, unknown action glyphs, and tables inside the statblock stop the export. All three pages must pass before Markdown is written. No substitute data is invented.
- Missing Recall Knowledge is reported as a warning; no DC is calculated. Unknown wrapper tags keep their text and produce a formatting warning. Unsupported images keep alt text with a warning. Warnings appear both in the terminal and the document.
- AoN downtime, network restrictions, or an anti-bot page can prevent live retrieval. The tool does not bypass challenges; retry later or use saved HTML. Downloads are sequential with a pause, bounded timeouts, and limited retries for transient errors.
- No Obsidian app/plugin rendering, Windows execution, or macOS execution was tested in this environment. Linux Python 3.14.8 was used for validation.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests use the nine saved AoN pages and do not need network access. They check full selected text and hyperlink preservation, key stats, signed modifiers and dice, spellcasting, action markup, document structure, offline CLI behavior, and refusal of malformed inputs. The example blocks are compared with conversion of the saved snapshots. The live CLI was also run for all three creatures; those outputs are included.

## Attribution and source licensing

Pathfinder game content belongs to Paizo Inc.; the HTML was obtained from [Archives of Nethys](https://2e.aonprd.com/). This is an unofficial personal-use conversion utility, not a Paizo or AoN product. No payment or hosted republication is part of this tool.

The converter and original tests are available under the [MIT license](LICENSE). That license **does not** cover the downloaded game text, HTML snapshots, or converted example statblocks. Their original rights and applicable licenses continue to apply. Citations and hyperlinks are retained; every export links to the [AoN licensing and copyright notices](https://2e.aonprd.com/Licenses.aspx). A full, unmodified snapshot of that page is included at `tests/fixtures/AoN-Licenses.html` for reference alongside the private validation fixtures.

These artifacts are intended for your campaign notes. A source link alone is not a replacement for license text, copyright notices, attribution, or other conditions required for redistribution. If you later publish a collection, consult the original book's applicable ORC/OGL and other licensing notices; this converter does not classify licensed versus reserved material or construct a publication-ready license declaration.
