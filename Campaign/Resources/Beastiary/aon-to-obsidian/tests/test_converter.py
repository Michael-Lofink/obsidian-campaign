"""Real downloaded-page regression tests plus isolated failure/formatting cases."""
import contextlib
import io
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import urljoin
from unittest.mock import patch

from bs4 import BeautifulSoup, Tag

from aon_to_obsidian import (ConversionError, Renderer, VARIANTS, document, main,
                             parse_page, variant_urls)

FIXTURES = Path(__file__).parent / "fixtures"
CREATURES = {"apothecary": "NPCs.aspx?ID=3479", "lich": "Monsters.aspx?ID=3082",
             "ice-linnorm": "Monsters.aspx?ID=3084"}


def get_blocks(creature):
    urls = variant_urls("https://2e.aonprd.com/" + CREATURES[creature])
    return [parse_page((FIXTURES / creature / (v + ".html")).read_bytes(), urls[v], v)
            for v in VARIANTS]


def plain_md(text):
    text = re.sub(r"\[([^\]]*)\]\(https?://[^\s)]*\)", r"\1", text)
    return text.replace("**", "").replace("_", "").replace("`", "").replace("==", "")


class LivePageRegressionTests(unittest.TestCase):
    def test_apothecary_all_three_variants(self):
        # Independently transcribed from downloaded AoN pages, not calculated.
        expected = [(-1, 13, 5, 14, 8, (8,3,5), (5,8,10,8),
                     'stone pestle +4 [-1/-6]', 'fist +5 [+1/-3]', 'acid flask +5 [+0/-5]', '1d6'),
                    (-2, 12, 3, 12, 8, (6,1,3), (3,6,8,6),
                     'stone pestle +2 [-3/-8]', 'fist +3 [-1/-5]', 'acid flask +3 [-2/-7]', '1d6-2'),
                    (1, 15, 7, 16, 18, (10,5,7), (7,10,12,10),
                     'stone pestle +6 [+1/-4]', 'fist +7 [+3/-1]', 'acid flask +7 [+2/-3]', '1d6+2')]
        for block, (level, recall, perception, ac, hp, saves, skills, stone, fist, acid, dmg) in zip(get_blocks('apothecary'), expected):
            with self.subTest(variant=block.variant):
                text = plain_md(block.markdown)
                self.assertEqual(block.level, level)
                for value in [f'Recall Knowledge DC {recall}', f'Perception +{perception}',
                              f'AC {ac}; Fort +{saves[0]}, Ref +{saves[1]}, Will +{saves[2]}',
                              f'HP {hp}; Resistances poison 2', stone, fist, acid,
                              f'Damage {dmg} bludgeoning', 'Medium Human Humanoid',
                              f'Crafting +{skills[0]} (+{skills[1]} for alchemy and medication), Medicine +{skills[2]}, Nature +{skills[3]}',
                              'Str +0 Dex +1 Con +1 Int +3 Wis +3 Cha +1',
                              'Medical Specialist', 'Medical Wisdom',
                              '1 acid plus 1d6 persistent acid and 1 splash acid']:
                    self.assertIn(value, text)
                self.assertEqual(block.markdown.count('`[one-action]`'), 3)
                self.assertIn('[_NPC Core pg. 60_](https://2e.aonprd.com/Sources.aspx?ID=236)', block.markdown)
                self.assertIn("[healer's toolkit](https://2e.aonprd.com/Equipment.aspx?ID=2727)", block.markdown)
                self.assertEqual(block.warnings, [])

    def test_lich_spells_reactions_and_defenses(self):
        for b, level, hp, ac, dc, attack, siphon in zip(get_blocks('lich'), [12,11,13], [190,170,210], [31,29,33], [36,34,38], [26,24,28], [34,32,36]):
            with self.subTest(variant=b.variant):
                text = plain_md(b.markdown)
                self.assertEqual(b.level, level)
                for part in [f'HP {hp}', f'AC {ac}', f'Arcane Prepared Spells DC {dc}, attack +{attack}',
                             f'Siphon Life DC {siphon}', 'physical 10 (except magical bludgeoning)',
                             '6th chain lightning, dominate, vampiric exsanguination',
                             '5th howling blizzard (×2), toxic cloud, wall of ice',
                             'Cantrips (6th) detect magic, frostbite, message, shield, telekinetic hand',
                             "On a success, the action isn't disrupted."]:
                    self.assertIn(part, text)
                self.assertIn('**Counterspell** `[reaction]` **Trigger**', b.markdown)
                self.assertIn('**Drain Soul Cage** `[free-action]` 6th rank', b.markdown)
                self.assertEqual(b.markdown.count('https://2e.aonprd.com/Spells.aspx?'), 27)
                if b.variant != 'normal':
                    self.assertIn('(-4 dmg)' if b.variant == 'weak' else '(+4 dmg)', text)
                    self.assertIn('NOT factored in', text)
                self.assertNotIn('Load Spell Descriptions', text)
                self.assertNotIn('Creating a Lich', text)

    def test_all_selected_source_text_and_hyperlinks_survive(self):
        # Independent full-body audit: compare ordered source text to output text,
        # ignoring presentation punctuation only. Numeric/sign checks are separate.
        for creature in CREATURES:
            for block in get_blocks(creature):
                with self.subTest(creature=creature, variant=block.variant):
                    raw = (FIXTURES / creature / (block.variant + '.html')).read_bytes()
                    soup = BeautifulSoup(raw, 'html.parser')
                    heading = soup.select_one('.monster-statblock-name')
                    parts = []
                    for n in heading.next_siblings:
                        if isinstance(n, Tag) and 'monster-family' in n.get('class', []):
                            break
                        if isinstance(n, Tag) and 'creature-spellbook-wrapper' in n.get('class', []):
                            continue
                        parts.append(str(n))
                    selected = BeautifulSoup(''.join(parts), 'html.parser')
                    source = selected.get_text().replace('Changes are marked. ', '')
                    result = plain_md(block.markdown.split('\n\n---\n\n', 1)[1].removesuffix('\n```'))
                    normalize = lambda s: re.sub(r'[^\w]', '', s, flags=re.UNICODE).replace('_', '')
                    self.assertEqual(normalize(source), normalize(result))
                    # Preserve signs too; only generated section rules are removed.
                    signed = lambda s: re.sub(r'[^\w+−-]', '', s).replace('_', '')
                    self.assertEqual(signed(source), signed(result.replace('\n\n---\n\n', '')))
                    for link in selected.find_all('a', href=True):
                        target = urljoin(block.url, link['href'])
                        self.assertTrue(target in block.markdown or target in block.references,
                                        f'Missing hyperlink {target}')
                    self.assertEqual(block.warnings, [])

    def test_ice_linnorm_keeps_source_dice_and_non_strike_damage(self):
        for b, hp, dice, dc in zip(get_blocks('ice-linnorm'), [330,310,350],
                                  ['3d12+17','3d12-2+17','3d12+2+17'], [38,36,40]):
            with self.subTest(variant=b.variant):
                text = plain_md(b.markdown)
                self.assertIn(f'HP {hp}', text)
                self.assertIn(f'Damage {dice} piercing', text)
                self.assertIn(f'Primal Innate Spells DC {dc}', text)
                self.assertIn('**Icemire Breath** `[two-actions]`', b.markdown)
                self.assertIn('15d6 cold damage', text)
                self.assertIn('Stage 1 5d6 cold damage and drained 1', text)
                self.assertIn('Stage 2 7d6 cold damage and drained 2', text)
                self.assertIn("The linnorm can't use Icemire Breath again for 1d4 rounds.", text)

    def test_live_generated_examples_match_downloaded_fixtures(self):
        for creature, filename in [('apothecary','Apothecary.md'), ('lich','Lich.md'), ('ice-linnorm','Ice-Linnorm.md')]:
            example = (FIXTURES.parent.parent/'examples'/filename).read_text()
            found = re.findall(r'```pf2e-stats\n.*?\n```', example, re.S)
            self.assertEqual(found, [b.markdown for b in get_blocks(creature)])

    def test_document_structure_and_notes(self):
        for creature in CREATURES:
            text = document(get_blocks(creature), 'Input: test fixtures')
            self.assertEqual(text.count('```pf2e-stats\n'), 3)
            self.assertEqual(text.count('\n```'), 6)
            self.assertEqual(text.count('\n\n---\n\n'), 9)
            self.assertEqual(text.count('NOT factored in'), 2)
            self.assertIn('Licenses.aspx', text)
            self.assertIn('sha256', text)
            self.assertNotIn('Changes are marked', text)
            self.assertNotIn('****', text)


class RobustnessTests(unittest.TestCase):
    def setUp(self):
        self.raw = (FIXTURES/'apothecary'/'normal.html').read_bytes()
        self.url = 'https://2e.aonprd.com/NPCs.aspx?ID=3479'

    def test_url_normalization(self):
        urls = variant_urls('http://2e.aonprd.com/npcs.aspx?Weak=true&ID=3479&Elite=true#foo')
        self.assertEqual(urls['normal'], self.url + '&NoRedirect=1')
        self.assertEqual(urls['elite'], self.url + '&Elite=true&NoRedirect=1')
        self.assertEqual(variant_urls(self.url+r'\&NoRedirect=1')['normal'], urls['normal'])

    def test_invalid_urls(self):
        for url in ['file:///tmp/a.html', 'https://example.com/NPCs.aspx?ID=1',
                    'https://2e.aonprd.com/Spells.aspx?ID=1', self.url+'&PWL=true',
                    self.url+'&ID=2', self.url.replace('3479','x'),
                    'https://user@2e.aonprd.com/NPCs.aspx?ID=1']:
            with self.subTest(url=url), self.assertRaises(ConversionError):
                variant_urls(url)

    def test_missing_core_fields_and_bad_layout_fail(self):
        for data in [b'<html>Challenge page</html>', self.raw.replace(b'<b>HP</b>', b'<b>Missing</b>'),
                     self.raw.replace(b'<b>HP</b> 8', b'<b>HP</b> unknown'),
                     self.raw.replace(b'<hr />', b'<br />'),
                     self.raw.replace(b'<b>Speed</b>', b'<table><tr><td>Test</td></tr></table><b>Speed</b>')]:
            with self.subTest(data=data[:20]), self.assertRaises(ConversionError):
                parse_page(data, self.url, 'normal')

    def test_wrong_variant_or_identity_fails(self):
        with self.assertRaises(ConversionError):
            parse_page(self.raw, self.url, 'weak')
        with self.assertRaises(ConversionError):
            parse_page(self.raw, self.url.replace('3479','1'), 'normal')
        blocks = get_blocks('apothecary')
        blocks[2] = get_blocks('lich')[2]
        with self.assertRaises(ConversionError):
            document(blocks, 'test')

    def test_missing_recall_warns_without_inventing(self):
        data = self.raw.replace(b'Recall Knowledge', b'Unrecognized label')
        block = parse_page(data, self.url, 'normal')
        self.assertIn('Recall Knowledge not present', block.warnings[0])
        self.assertIn('**Unrecognized label** DC 13', block.markdown)

    def test_all_action_tokens_nested_lists_and_negative_dice(self):
        renderer = Renderer(self.url)
        for token in ['one-action','two-actions','three-actions','free-action','reaction']:
            fragment = BeautifulSoup(f'<b>Ability <span class="action">[{token}]</span></b>', 'html.parser')
            self.assertEqual(renderer.render(fragment.b).strip(), f'**Ability** `[{token}]`')
        fragment = BeautifulSoup('<span>2d8<span class="EWChange"><b>-2</b></span></span>', 'html.parser')
        self.assertEqual(renderer.render(fragment.span), '2d8-2')
        fragment = BeautifulSoup('<ul><li>Success<ul><li>Effect</li></ul></li><li>Failure</li></ul>', 'html.parser')
        result = renderer.render(fragment.ul)
        self.assertIn('\n- Success', result)
        self.assertIn('\n  - Effect', result)

    def test_unknown_action_fails(self):
        fragment = BeautifulSoup('<span class="action">mystery</span>', 'html.parser')
        with self.assertRaises(ConversionError):
            Renderer(self.url).render(fragment.span)

    def test_cli_offline_and_no_partial_or_overwritten_output(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            output = Path(temp)/'test.md'
            args = [self.url, '--html-dir', str(FIXTURES/'apothecary'), '-o', str(output)]
            with patch('aon_to_obsidian.fetch', side_effect=AssertionError('Network called offline')):
                self.assertEqual(main(args), 0)
                self.assertEqual(output.read_text().count('```pf2e-stats'), 3)
                self.assertEqual(main(args), 1)
                self.assertEqual(main(args+['--force']), 0)
                output.unlink()
                self.assertEqual(main([self.url, '--html-dir', temp, '-o', str(output)]), 1)
                self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
