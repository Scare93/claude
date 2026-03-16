#!/usr/bin/env python3
"""
Verification script for scraped Montana Code Annotated (MCA) data.

Checks structural completeness, content integrity, and non-empty content
for all scraped sections.

Usage:
    python verify_mca.py                   # Verify all scraped data
    python verify_mca.py --data-dir path   # Verify data in a specific directory
    python verify_mca.py --verbose         # Show per-section details
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import mca_config as config


def load_json(path):
    """Load a JSON file, return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  ERROR: Cannot read {path}: {exc}")
        return None


def verify_section(filepath, verbose=False):
    """Verify a single section JSON file. Returns (ok, warnings)."""
    warnings = []
    data = load_json(filepath)
    if data is None:
        return False, ["Cannot load JSON"]

    # Check required fields
    for field in ["text_content", "raw_html", "content_hash", "url"]:
        if field not in data:
            return False, [f"Missing field: {field}"]

    # Check non-empty content
    text = data.get("text_content", "")
    if not text:
        return False, ["Empty text_content"]

    if len(text) < 50:
        warnings.append(f"Very short text ({len(text)} chars)")

    # Check raw HTML
    raw_html = data.get("raw_html", "")
    if not raw_html:
        warnings.append("Empty raw_html")

    # Verify content hash
    expected_hash = data.get("content_hash", "")
    if expected_hash.startswith("sha256:"):
        computed = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if f"sha256:{computed}" != expected_hash:
            return False, ["Content hash mismatch"]

    if verbose and warnings:
        print(f"    WARN {filepath.name}: {'; '.join(warnings)}")

    return True, warnings


def verify_index(index_path, parent_dir, verbose=False):
    """
    Verify an _index.json and its children recursively.
    Returns (sections_ok, sections_total, warnings_list, errors_list).
    """
    data = load_json(index_path)
    if data is None:
        return 0, 0, [], [f"Cannot load {index_path}"]

    children = data.get("children", [])
    total_sections = 0
    ok_sections = 0
    all_warnings = []
    all_errors = []

    # Check if children directories/files exist
    for child in children:
        child_url = child.get("url", "")
        child_name = child.get("name", "?")

        # Find child directories or section files in parent_dir
        # Children can be subdirectories (with their own _index.json) or section files
        found = False
        for subdir in sorted(parent_dir.iterdir()):
            if subdir.is_dir():
                sub_index = subdir / "_index.json"
                if sub_index.exists():
                    s_ok, s_total, s_warn, s_err = verify_index(
                        sub_index, subdir, verbose
                    )
                    ok_sections += s_ok
                    total_sections += s_total
                    all_warnings.extend(s_warn)
                    all_errors.extend(s_err)
                    found = True
                    break
            elif subdir.is_file() and subdir.suffix == ".json" and subdir.name != "_index.json":
                # This is a section file
                pass

        # If not found as directory, might be in a flattened layout
        # (sections directly under the part directory)

    # Also verify all section JSON files in this directory
    for json_file in sorted(parent_dir.glob("*.json")):
        if json_file.name == "_index.json":
            continue
        total_sections += 1
        ok, warns = verify_section(json_file, verbose)
        if ok:
            ok_sections += 1
        else:
            all_errors.append(f"FAIL: {json_file}: {'; '.join(warns)}")
        all_warnings.extend(warns)

    # Recurse into subdirectories that have _index.json
    for subdir in sorted(parent_dir.iterdir()):
        if subdir.is_dir():
            sub_index = subdir / "_index.json"
            if sub_index.exists():
                s_ok, s_total, s_warn, s_err = verify_index(
                    sub_index, subdir, verbose
                )
                ok_sections += s_ok
                total_sections += s_total
                all_warnings.extend(s_warn)
                all_errors.extend(s_err)

    return ok_sections, total_sections, all_warnings, all_errors


def verify_title(title_dir, title_name, verbose=False):
    """Verify all data under a title directory."""
    index_path = title_dir / "_index.json"
    if not index_path.exists():
        return {
            "name": title_name,
            "status": "MISSING",
            "sections_ok": 0,
            "sections_total": 0,
            "warnings": 0,
            "errors": 1,
            "error_details": [f"No _index.json in {title_dir}"],
        }

    data = load_json(index_path)
    chapters = len(data.get("children", [])) if data else 0

    # Count sections by walking all JSON files (not _index.json)
    total_sections = 0
    ok_sections = 0
    all_warnings = []
    all_errors = []

    for json_file in sorted(title_dir.rglob("*.json")):
        if json_file.name == "_index.json":
            continue
        total_sections += 1
        ok, warns = verify_section(json_file, verbose)
        if ok:
            ok_sections += 1
        else:
            all_errors.append(f"{json_file.name}: {'; '.join(warns)}")
        all_warnings.extend(warns)

    return {
        "name": title_name,
        "status": "OK" if not all_errors else "ERRORS",
        "chapters": chapters,
        "sections_ok": ok_sections,
        "sections_total": total_sections,
        "warnings": len(all_warnings),
        "errors": len(all_errors),
        "error_details": all_errors,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verify scraped MCA data for completeness and integrity."
    )
    parser.add_argument(
        "--data-dir", type=str, default=config.DATA_DIR,
        help="Directory containing scraped data (default: %s)." % config.DATA_DIR
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show per-section warnings."
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Data directory does not exist: {data_dir}")
        print("Run scrape_mca.py first.")
        sys.exit(1)

    print("=" * 70)
    print("MCA VERIFICATION REPORT")
    print("=" * 70)
    print()

    total_ok = 0
    total_sections = 0
    total_warnings = 0
    total_errors = 0
    all_passed = True

    for title_num in sorted(config.TITLES_TO_SCRAPE.keys()):
        title_name = config.TITLES_TO_SCRAPE[title_num]
        if title_num == 0:
            dir_name = "constitution"
        else:
            dir_name = f"title_{title_num:02d}"

        title_dir = data_dir / dir_name
        if not title_dir.exists():
            print(f"Title {title_num:2d}: {title_name:<45s} [NOT SCRAPED]")
            all_passed = False
            total_errors += 1
            continue

        result = verify_title(title_dir, title_name, verbose=args.verbose)

        status_str = result["status"]
        chapters = result.get("chapters", "?")
        sec_ok = result["sections_ok"]
        sec_total = result["sections_total"]
        warns = result["warnings"]
        errs = result["errors"]

        status_tag = "[OK]" if status_str == "OK" and sec_total > 0 else "[FAIL]"
        if sec_total == 0:
            status_tag = "[EMPTY]"

        if title_num == 0:
            label = "Constitution"
        else:
            label = f"Title {title_num:2d}"

        print(
            f"{label}: {title_name:<45s} "
            f"{chapters:>3} ch, {sec_ok:>5}/{sec_total:<5} sections, "
            f"{warns} warns, {errs} errs  {status_tag}"
        )

        if errs > 0:
            all_passed = False
            if args.verbose:
                for detail in result["error_details"][:10]:
                    print(f"         ERROR: {detail}")

        total_ok += sec_ok
        total_sections += sec_total
        total_warnings += warns
        total_errors += errs

    print()
    print("-" * 70)
    print(f"TOTAL: {total_ok}/{total_sections} sections OK, "
          f"{total_warnings} warnings, {total_errors} errors")
    print()

    if total_sections == 0:
        print("STATUS: NO DATA - Run scrape_mca.py first")
        sys.exit(2)
    elif all_passed:
        print("STATUS: PASS")
        sys.exit(0)
    else:
        print("STATUS: FAIL (see errors above)")
        sys.exit(1)


if __name__ == "__main__":
    main()
