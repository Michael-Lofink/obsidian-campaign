#!/usr/bin/env python3
"""Convert three independently obtained AoN creature pages to pf2e-stats Markdown."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

BASE = "https://2e.aonprd.com/"
VARIANTS = ("normal", "weak", "elite")
MAX_BYTES = 8 * 1024 * 1024
ACTION_NAMES = {
    "single action": "one-action", "one action": "one-action",
    "two actions": "two-actions", "three actions": "three-actions",
    "reaction": "reaction", "free action": "free-action",
}


class ConversionError(ValueError):
    """A page cannot be converted without guessing or losing important data."""


def variant_urls(value: str) -> dict[str, str]:
    """Pin the exact ID/edition; discard adjustment switches, reject other modes."""
    value = html.unescape(value.strip()).replace(r"\&", "&")
    p = urlsplit(value)
    if (p.scheme not in {"http", "https"} or p.hostname != "2e.aonprd.com"
            or p.username or p.password or p.port not in {None, 80, 443}):
        raise ConversionError("Use an http(s) URL on 2e.aonprd.com.")
    paths = {"/npcs.aspx": "NPCs.aspx", "/monsters.aspx": "Monsters.aspx"}
    if p.path.lower() not in paths:
        raise ConversionError("Only NPCs.aspx and Monsters.aspx URLs are supported.")
    query: dict[str, str] = {}
    for key, val in parse_qsl(p.query, keep_blank_values=True):
        key = key.lower()
        if key in query:
            raise ConversionError(f"Duplicate URL parameter: {key}")
        if key not in {"id", "weak", "elite", "noredirect"}:
            raise ConversionError(f"Unsupported URL parameter: {key}. Remove it (PWL is not supported).")
        query[key] = val
    if not re.fullmatch(r"[1-9]\d*", query.get("id", "")):
        raise ConversionError("The URL must contain one positive numeric ID.")
    prefix = BASE + paths[p.path.lower()]
    return {v: prefix + "?" + urlencode({"ID": query["id"],
                **({v.title(): "true"} if v != "normal" else {}), "NoRedirect": "1"})
            for v in VARIANTS}


class SameSiteRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if (target.scheme != "https" or target.hostname != "2e.aonprd.com"
                or target.username or target.password or target.port not in {None, 443}):
            raise ConversionError("AoN redirected outside its HTTPS host; stopped.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, timeout: float = 30) -> bytes:
    opener = build_opener(SameSiteRedirect())
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "AoN-to-Obsidian/1.0 (personal statblock export)",
                                        "Accept": "text/html"})
            with opener.open(req, timeout=timeout) as response:
                if response.headers.get_content_type() not in {"text/html", "application/xhtml+xml"}:
                    raise ConversionError("AoN did not return HTML.")
                data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise ConversionError("Page exceeds the 8 MiB limit.")
                return data
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise ConversionError(f"AoN HTTP {exc.code} for {url}") from exc
            retry = exc.headers.get("Retry-After", "")
            time.sleep(min(30, int(retry)) if retry.isdigit() else 2 ** (attempt + 1))
        except (URLError, TimeoutError, OSError) as exc:
            if attempt == 2:
                raise ConversionError(f"Could not download {url}: {exc}") from exc
            time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Renderer:
    url: str
    references: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def link_url(self, node: Tag) -> str:
        target = urljoin(self.url, node.get("href", "").replace("\\", "/"))
        if urlsplit(target).scheme not in {"https", "http"}:
            raise ConversionError(f"Unsupported hyperlink in statblock: {node.get('href')}")
        return target.replace("(", "%28").replace(")", "%29").replace(" ", "%20")

    def remember_links(self, node: Tag) -> None:
        for a in ([node] if node.name == "a" else node.find_all("a", href=True)):
            if a.get("href"):
                label = compact(a.get_text("", strip=False))
                if re.fullmatch(r"[+−-]?\d+/[+−-]?\d+", label):
                    label = "Multiple attack penalty"
                self.references.setdefault(self.link_url(a), label)

    def render(self, node, plain: bool = False) -> str:
        if isinstance(node, Comment):
            return ""
        if isinstance(node, NavigableString):
            return re.sub(r"\s+", " ", str(node))
        classes = node.get("class", [])
        if node.name in {"script", "style", "iframe", "input", "button"}:
            raise ConversionError(f"Unexpected <{node.name}> inside statblock.")
        if "action" in classes or (node.name == "img" and "action" in str(node).lower()):
            token = compact(node.get_text())
            match = re.fullmatch(r"\[(one-action|two-actions|three-actions|reaction|free-action)\]", token)
            if match:
                action = match.group(1)
            else:
                label = node.get("title", node.get("alt", node.get("aria-label", ""))).lower()
                action = ACTION_NAMES.get(label)
            if not action:
                raise ConversionError(f"Unknown action symbol: {node}")
            return f" `[{action}]` "
        if node.name == "img":
            alt = node.get("alt", "")
            self.warnings.append(f"Image represented by alt text only: {alt or '(no alt text)'}")
            return f" [Image: {alt or 'unlabeled'}] "
        if node.name == "br":
            return "\n"
        if node.name == "hr":
            return "\n\n---\n\n"
        if any(c.startswith("trait") for c in classes):
            self.remember_links(node)
            return "==" + compact(node.get_text()) + "== "
        if "EWChange" in classes:
            # AoN's bold/color change highlighting must not split signs and dice.
            return "".join(self.render(c, plain=True) for c in node.children)
        if node.name == "a":
            label = "".join(self.render(c, plain=plain) for c in node.children)
            if not node.get("href"):
                return label
            target = self.link_url(node)
            # Keep literal MAP pairs and bold field labels as in the supplied example.
            if plain or re.fullmatch(r"[+−-]?\d+/[+−-]?\d+", compact(node.get_text())):
                self.remember_links(node)
                return label
            return f"[{label.strip()}]({target})"
        if node.name in {"b", "strong"}:
            content = "".join(self.render(c, plain=True) for c in node.children).strip()
            if plain:
                return content
            # Actions belong outside the bold name, including AoN's nested markup.
            content = re.sub(r"\s*(`\[[a-z-]+\]`)\s*", r"** \1 **", content)
            return ("**" + content + "**").replace("****", "")
        content = "".join(self.render(c, plain=plain) for c in node.children)
        if node.name in {"i", "em"}:
            return content if plain or not content.strip() else "_" + content.strip() + "_"
        if node.name in {"ul", "ol"}:
            return "\n" + content + "\n"
        if node.name == "li":
            # Preserve nested indentation and ordered-list numbering.
            depth = sum(p.name in {"ul", "ol"} for p in node.parents) - 1
            marker = (str(len(node.find_previous_siblings("li")) + 1) + "."
                      if node.parent.name == "ol" else "-")
            return "\n" + "  " * max(0, depth) + marker + " " + content.strip() + "\n"
        if node.name == "table":
            raise ConversionError("A table occurs inside the statblock; manual conversion is required.")
        if node.name in {"p", "div", "blockquote"} or "hanging-indent" in classes:
            return "\n" + content.strip() + "\n"
        if node.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            return "\n\n**" + content.strip() + "**\n"
        if node.name == "sup":
            return "<sup>" + content + "</sup>"
        if node.name not in {"span", "u", "small", "sub", "s", "del"}:
            self.warnings.append(f"Unrecognized <{node.name}> retained as text; check formatting.")
        if node.name in {"s", "del"}:
            return "~~" + content + "~~"
        if node.name == "sub":
            return "<sub>" + content + "</sub>"
        return content


@dataclass
class Statblock:
    name: str
    level: int
    markdown: str
    url: str
    variant: str
    sha256: str
    warnings: list[str]
    references: dict[str, str]


def parse_page(data: bytes, url: str, variant: str) -> Statblock:
    if variant not in VARIANTS:
        raise ConversionError(f"Unknown variant: {variant}")
    soup = BeautifulSoup(data, "html.parser", from_encoding="utf-8")
    titles = soup.select(".monster-statblock-name")
    if len(titles) != 1:
        raise ConversionError("Expected exactly one AoN statblock heading; page layout, error, or challenge page is unsupported.")
    title = titles[0]
    name_link = title.find("a", href=True)
    level_match = re.search(r"\bCreature\s+(-?\d+)\s*$", title.get_text(" ", strip=True))
    if name_link is None or level_match is None:
        raise ConversionError("Could not identify creature name and level.")
    if variant_urls(urljoin(url, name_link["href"]))["normal"] != variant_urls(url)["normal"]:
        raise ConversionError("AoN returned a different creature ID/edition than requested.")
    name = compact(name_link.get_text())
    level = int(level_match.group(1))
    nodes = []
    for node in title.next_siblings:
        if isinstance(node, Tag) and "monster-family" in node.get("class", []):
            break
        if isinstance(node, Tag) and "creature-spellbook-wrapper" in node.get("class", []):
            continue  # Lazy-loaded UI, not part of the printed statblock.
        nodes.append(node)
    fragment = BeautifulSoup("".join(str(n) for n in nodes), "html.parser")
    fields = {compact(b.get_text()): b for b in fragment.find_all(["b", "strong"])
              if not b.find_parent(class_="EWChange")}
    required = {"Source", "Perception", "Str", "Dex", "Con", "Int", "Wis", "Cha",
                "AC", "Fort", "Ref", "Will", "HP", "Speed"}
    missing = required - fields.keys()
    if missing:
        raise ConversionError("Missing required fields: " + ", ".join(sorted(missing)))
    if len(fragment.find_all("hr")) != 2:
        raise ConversionError("Expected two statblock section separators; refusing an ambiguous layout.")
    if not fragment.select('[class^="trait"]'):
        raise ConversionError("Could not locate traits.")
    for v in ("weak", "elite"):
        if (v.title() in fields) != (variant == v):
            raise ConversionError(f"Requested {variant}, but page adjustment label does not match.")
    if variant != "normal" and not name.startswith(variant.title() + " "):
        raise ConversionError("Variant name is not marked Weak/Elite.")
    if variant != "normal" and "NOT factored in" not in fragment.get_text():
        raise ConversionError("Weak/Elite non-Strike damage warning is missing; refusing to guess.")
    renderer = Renderer(url)
    body = "".join(renderer.render(n) for n in fragment.children)
    body = "\n".join(re.sub(r"[ \t]+", " ", line).rstrip() if not re.match(r"\s+[-\d]", line)
                     else line.rstrip() for line in body.splitlines())
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    # Presentation-only differences from AoN, never numeric adjustments.
    body = body.replace("Changes are marked. ", "")
    body = re.sub(r"\(\(([^()]+)\)\)", r"(\1)", body)
    body = re.sub(r", (?=\*\*(?:Dex|Con|Int|Wis|Cha)\*\*)", " ", body)
    body = body.replace(" • ", " * ")
    for label in ("Perception", "Str", "Dex", "Con", "Int", "Wis", "Cha", "AC", "Fort", "Ref", "Will", "HP"):
        if not re.search(r"\*\*" + label + r"\*\*\s+[+−-]?\d", body):
            raise ConversionError(f"{label} has no recognizable numeric value; manual review required.")
    if not fragment.find("a", href=re.compile(r"Sources\.aspx", re.I)):
        raise ConversionError("Source citation has no recognizable source hyperlink.")
    if "Recall Knowledge" not in fields:
        renderer.warnings.append("Recall Knowledge not present in the parsed statblock; no DC was calculated.")
    if "```" in body:
        raise ConversionError("Unexpected Markdown fence in source text.")
    block = f"```pf2e-stats\n# {name}\n## Creature {level}\n\n---\n\n{body}\n```"
    return Statblock(name, level, block, url, variant, hashlib.sha256(data).hexdigest(),
                     list(dict.fromkeys(renderer.warnings)), renderer.references)


def document(blocks: list[Statblock], origin: str) -> str:
    if [b.variant for b in blocks] != list(VARIANTS):
        raise ConversionError("Exactly normal, weak, and elite blocks are required, in that order.")
    base = blocks[0].name
    if [b.name for b in blocks] != [base, "Weak " + base, "Elite " + base]:
        raise ConversionError("The three pages do not identify the same creature.")
    if not blocks[1].level < blocks[0].level < blocks[2].level:
        raise ConversionError("Variant levels are inconsistent; refusing to export.")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [f"Converted from Archives of Nethys on {stamp}. {origin}.", "",
             " | ".join(f"[{b.variant.title()}]({b.url})" for b in blocks), ""]
    for b in blocks:
        heading = f"Normal {b.name}" if b.variant == "normal" else b.name
        lines += [f"## {heading}", "", b.markdown, ""]
    warnings = [f"{b.variant.title()}: {w}" for b in blocks for w in b.warnings]
    if warnings:
        lines += ["## Conversion warnings", ""] + [f"- {w}" for w in warnings] + [""]
    refs = {url: label for b in blocks for url, label in b.references.items()}
    if refs:
        lines += ["## Additional source links", "",
                  "Links for plain-text field labels, traits, and MAP pairs above:", ""]
        lines += [f"- [{label}]({url})" for url, label in refs.items()]
        lines.append("")
    lines += ["## Attribution", "",
              "Game content and Pathfinder are owned by Paizo Inc. Archives of Nethys is credited as the source of this conversion. "
              "This converter is unofficial and is not endorsed by Paizo or Archives of Nethys. "
              "Source-book citations are retained in each block. "
              "See [Archives of Nethys licensing and copyright notices](https://2e.aonprd.com/Licenses.aspx). "
              "This personal-use export does not grant redistribution rights or replace applicable source licenses.", "",
              "<!-- Provenance: SHA-256 of each input HTML file. Local-input timestamps are conversion times, not download times.",
              json.dumps({b.variant: {"url": b.url, "sha256": b.sha256} for b in blocks}, indent=2), "-->", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="AoN NPCs.aspx or Monsters.aspx URL; quote it in your shell")
    parser.add_argument("-o", "--output", type=Path, help="Output .md path (default: creature name.md)")
    parser.add_argument("--html-dir", type=Path, help="Read normal.html, weak.html, elite.html locally; no network")
    parser.add_argument("--save-html-dir", type=Path, help="Save downloaded inputs for inspection/offline reuse")
    parser.add_argument("--timeout", type=float, default=30, help="Timeout per HTTP attempt in seconds (default: 30)")
    parser.add_argument("--force", action="store_true", help="Replace an existing Markdown output")
    args = parser.parse_args(argv)
    try:
        if args.timeout <= 0:
            raise ConversionError("--timeout must be positive.")
        if args.html_dir and args.save_html_dir:
            raise ConversionError("Use either --html-dir or --save-html-dir, not both.")
        urls = variant_urls(args.url)
        blocks = []
        for variant, url in urls.items():
            if args.html_dir:
                data = (args.html_dir / f"{variant}.html").read_bytes()
            else:
                print(f"Fetching {variant}: {url}", file=sys.stderr)
                if blocks:
                    time.sleep(1)  # Three sequential requests, no bulk crawling.
                data = fetch(url, args.timeout)
            block = parse_page(data, url, variant)
            blocks.append(block)
            if args.save_html_dir:
                args.save_html_dir.mkdir(parents=True, exist_ok=True)
                (args.save_html_dir / f"{variant}.html").write_bytes(data)
        output = args.output or Path(re.sub(r'[^\w .-]', '_', blocks[0].name) + ".md")
        if output.suffix.lower() != ".md":
            raise ConversionError("Output filename must end in .md.")
        result = document(blocks, "Input: saved HTML" if args.html_dir else "Input: live HTML")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w" if args.force else "x", encoding="utf-8", newline="\n") as f:
            f.write(result)
        for b in blocks:
            for warning in b.warnings:
                print(f"Warning ({b.variant}): {warning}", file=sys.stderr)
        print(f"Created {output.resolve()} (3 statblocks).")
        return 0
    except (ConversionError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
