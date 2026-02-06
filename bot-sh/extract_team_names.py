#!/usr/bin/env python3
"""Extract correct team tab names (UPPERCASE) and match URLs for batch processing."""

from playwright.sync_api import sync_playwright
import re
import json


def extract_match_info(date_filter: str = "today"):
    """Extract all matches with team names and URLs for a specific date."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("📍 Navigating to StatsHub...")
            page.goto("https://www.statshub.com/")
            page.wait_for_load_state("networkidle")

            label = date_filter.capitalize()
            print(f"📍 Clicking '{label}' filter...")
            page.get_by_text(label, exact=True).click()
            page.wait_for_load_state("networkidle")

            print("📍 Extracting all matches and team names...")

            # Get all match links with hrefs
            match_links = page.locator('a[href*="/fixture/"]').all()
            print(f"Found {len(match_links)} match links")

            matches = []
            seen_urls = set()

            for link in match_links:
                try:
                    href = link.get_attribute("href")
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        # Extract match name from href (e.g., "deportivo-alaves-vs-real-sociedad")
                        match_id_pattern = r"/fixture/([^/]+)/(\d+)"
                        m = re.search(match_id_pattern, href)
                        if m:
                            slug = m.group(
                                1
                            )  # e.g., "deportivo-alaves-vs-real-sociedad"
                            match_id = m.group(2)

                            # Extract team names from slug
                            parts = slug.split("-vs-")
                            if len(parts) == 2:
                                home_slug = parts[0]
                                away_slug = parts[1]

                                # Clean up slugs to get display names
                                # e.g., "deportivo-alaves" -> "Deportivo Alaves"
                                home_name = " ".join(
                                    word.capitalize() for word in home_slug.split("-")
                                )
                                away_name = " ".join(
                                    word.capitalize() for word in away_slug.split("-")
                                )

                                matches.append(
                                    {
                                        "home_team_slug": home_name,
                                        "away_team_slug": away_name,
                                        "match_url": href,
                                        "match_id": match_id,
                                    }
                                )
                                print(f"  ✓ {home_name} vs {away_name}: {href}")
                except Exception as e:
                    print(f"  ✗ Error processing link: {e}")

            # Remove duplicates
            unique_matches = []
            seen = set()
            for m in matches:
                key = (m["home_team_slug"], m["away_team_slug"])
                if key not in seen:
                    unique_matches.append(m)
                    seen.add(key)

            print(f"\n📊 Found {len(unique_matches)} unique matches")

            # Now, click on each match and extract the actual team tab names (UPPERCASE)
            matches_with_tabs = []
            for i, match in enumerate(unique_matches):
                print(
                    f"\n[{i+1}/{len(unique_matches)}] Extracting team tab names for {match['home_team_slug']} vs {match['away_team_slug']}..."
                )
                try:
                    page.goto("https://www.statshub.com" + match["match_url"])
                    page.wait_for_load_state("networkidle")

                    # Click Opponent Stats button
                    try:
                        page.get_by_role("button", name="Opponent Stats NEW!").click()
                        page.wait_for_load_state("networkidle")
                    except Exception as e:
                        print(f"  ⚠️ Could not click Opponent Stats: {e}")
                        # continue anyway to attempt reading tabs

                    # Get all elements with role=tab and read their visible (uppercase) text
                    tabs = page.locator('[role="tab"]').all()
                    tab_names = []
                    for tab in tabs:
                        try:
                            text = tab.inner_text().strip()
                            if text:
                                tab_names.append(text)
                        except Exception:
                            pass

                    # Find home and away team tab names by matching slug words against tab text
                    home_tab = None
                    away_tab = None

                    def slug_to_words(slug):
                        return [w for w in slug.replace("-", " ").split() if w]

                    home_words = slug_to_words(match["home_team_slug"].lower())
                    away_words = slug_to_words(match["away_team_slug"].lower())

                    for t in tab_names:
                        t_up = t.upper()
                        if any(w.upper() in t_up for w in home_words):
                            home_tab = t
                        if any(w.upper() in t_up for w in away_words):
                            away_tab = t

                    if not home_tab or not away_tab:
                        # Fallback to positional mapping if we couldn't match by words
                        if len(tab_names) >= 2:
                            home_tab = tab_names[0]
                            away_tab = tab_names[1]
                            print(
                                f"  Using position-based tabs: {home_tab} vs {away_tab}"
                            )

                    if home_tab and away_tab:
                        match["home_team_tab"] = home_tab
                        match["away_team_tab"] = away_tab
                        matches_with_tabs.append(match)
                        print(f"  ✓ Team tabs: '{home_tab}' vs '{away_tab}'")
                    else:
                        print(f"  ✗ Could not determine team tabs. Found: {tab_names}")

                except Exception as e:
                    print(f"  ✗ Error extracting team tabs: {e}")

            # Save results
            output = {
                "matches": matches_with_tabs,
                "total_found": len(unique_matches),
                "total_extracted_tabs": len(matches_with_tabs),
            }

            with open("team_tabs.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            print(f"\n✅ Saved team tab information to team_tabs.json")
            print(f"   Total unique matches: {len(unique_matches)}")
            print(f"   Matches with team tabs extracted: {len(matches_with_tabs)}")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract team tab labels.")
    parser.add_argument(
        "--date",
        type=str,
        choices=["today", "tomorrow"],
        default="today",
        help="Match date (default: today)",
    )
    args = parser.parse_args()
    extract_match_info(date_filter=args.date)
