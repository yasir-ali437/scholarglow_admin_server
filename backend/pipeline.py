"""
pipeline.py — Importable wrapper around script_T5.py pipeline.
All heavy logic stays in the original scripts; this module
orchestrates them and yields SSE-style progress messages.
"""

import sys
import os
import re
import ast
import base64
import openai
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# ── Resolve paths so imports work regardless of CWD ─────────────────────────
AUTOMATION_DIR = r"E:\Scholarship Website\poster\automation"
if AUTOMATION_DIR not in sys.path:
    sys.path.insert(0, AUTOMATION_DIR)

from poster_T7 import create_poster
from post_T2 import create_post
from wordpress import post_to_wordpress

# ── Credentials (pulled from env, with script fallbacks) ────────────────────
OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY",
    "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",
)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ── System prompts (copied verbatim from script_T5.py) ──────────────────────
BLOG_SYSTEM = """You are an expert scholarship content writer for a website.

Your task is to convert raw opportunity information into a publication-ready scholarship article in valid HTML format.

You must follow every instruction exactly.

================================
OUTPUT RULES
================================

1. Return the output in this exact order:
   Title: ...
   Categories = [...]
   
   [Then the full HTML article]

2. The title must:
   - be concise
   - be engaging
   - always be under 60 characters
   - match the opportunity accurately

3. The categories line must:
   - appear immediately after the title
   - use this exact format: Categories = [id, id]
   - include only the most relevant category id or ids
   - choose from this dictionary only:

   {
     5: "Bachelors or Masters Scholarships",
     7: "Conferences",
     24: "Documents",
     12: "Fellowships",
     8: "Internships",
     28: "Online Courses",
     9: "PHD Scholarships",
     17: "Scholarships in Australia",
     19: "Scholarships in Canada",
     23: "Scholarships in China",
     21: "Scholarships in Europe",
     18: "Scholarships in Japan",
     22: "Scholarships in UK",
     11: "Social Media Accounts",
     10: "Summer Schools",
     15: "Trainings",
     29: "Volunteer Activities"
   }

4. Return the article in clean HTML only.
5. Do not use markdown.
6. Do not use emojis.
7. Do not shorten the provided information.
8. Rewrite everything in original wording to avoid plagiarism.
9. Keep the tone informative, encouraging, student-friendly, and publication-ready.
10. Optimize naturally for keywords such as:
    - Fully Funded
    - International Students
    - Apply Online
    - Deadline

================================
ARTICLE STRUCTURE
================================

You must follow this structure exactly:

1. Opening paragraph
2. About the [Program Name]
   - Host Country
   - Duration
   - Dates
   - Benefits
   - Deadline
Also Check 1 : {link here}
3. Financial Benefits
   - bullet points
Also Check 2 : {link here}
4. Program Theme
   - if no theme is available, use "Program Details" instead
5. Eligibility Criteria
   - Nationality
   - Age (if applicable)
   - Background
   - Requirements
Also Check 3 : {link here}
6. How to Apply for the [Program Name]?
   - short paragraph
   - mention the official website

================================
FORMATTING RULES
================================

1. Start with a short engaging introduction of 2 to 4 sentences.
2. Mention the host country, dates, theme, and host organization in the opening paragraph whenever available.
3. Use clear, simple, student-friendly language.
4. Keep formatting clean and readable.
5. In the About section, show the deadline in red color.
6. For "Also Check 1", "Also Check 2", and "Also Check 3":
   - I will provide three links in the raw input
   - use them in the proper Also Check locations
   - create proper anchor text based on the linked opportunity title
   - do not color the links
7. Always include the exact buttons HTML at the end.
8. Only update the href links in the buttons.
9. Do not change the design, wording, color, spacing, or structure of the buttons HTML.

================================
BUTTONS HTML
================================

Append this exact HTML at the end, only replacing the href values with the correct links from the input:

<!-- Buttons Section -->
<div style="margin-top: 35px; display: flex; justify-content: center; align-items: center; gap: 12px; flex-wrap: nowrap;"><a style="background-color: #f4b400; color: #000000; text-decoration: none; padding: 1px 22px; border-radius: 30px; font-weight: 600; font-size: 14px; white-space: nowrap; display: inline-block;" href="" target="_blank" rel="noopener">OFFICIAL WEBSITE</a><br /><a style="background-color: #f4b400; color: #000000; text-decoration: none; padding: 1px 22px; border-radius: 30px; font-weight: 600; font-size: 14px; white-space: nowrap; display: inline-block;" href="" target="_blank" rel="noopener">APPLY NOW</a></div>

</div>

================================
VALIDATION CHECKLIST
================================

Before returning the answer, verify all of the following:
- Title is under 60 characters
- Categories line is present and valid
- Output order is correct
- Opening paragraph is 2 to 4 sentences
- Both Also Check links are included in the correct sections
- Also Check links are blue and use anchor text
- Deadline is red
- Buttons HTML is included exactly
- Only href values in the buttons were changed
- No markdown is used
- No emojis are used

Now wait for the raw opportunity information.
"""

POSTER_FORMAT_SYSTEM = """Return the data in the following format for me to create a poster. Update all the values based on the scholarship information that user will provide.
Instructions: title should always be in two lines upto 70 characters, and bullets values should be upto 25 characters max, also update the selected country based on scholarship opportunity. Always return the data in the following format without any change, do not add or remove any field, just update the values.
title=" text here \n text here",
bullets=[
    ("Host Country", "# Update Country Name Here"),
    ("Dates", "24 Aug – 4 Sep, 2026"),
    ("Open To", "All Nationalities"),
    ("Application Fee", "None"),
],
deadline_label="Application Deadline: 22 March 2026, 11:59 p.m. CET",
selected_country="eu"
"""

POST_FORMAT_SYSTEM = """Return the result ONLY in the exact format below.

Strict rules:
- Output only Python code.
- Do not use markdown.
- Do not use code fences.
- Do not add any explanation or extra text.
- Keep the exact variable names.
- Keep the exact order.
- Keep INTRO_1(300 characters) and INTRO_2(400 characters) similar in length to the sample.
- Keep each PROGRAM_DETAILS value concise and similar in length to the sample.
- Output must remain valid Python.

Use this exact template:

SELECTED_COUNTRY = "se"

TITLE = "Summer School 2026 in Sweden (Fully Funded)"

INTRO_1 = (
    "The applications are now open for the Armament and Disarmament "
    "Summer School 2026. This is a premier, fully funded program that runs "
    "for five days, from August 24–28, 2026. Open to all nationals."
)

INTRO_2 = (
    "It is open to students, researchers, policymakers, practitioners, "
    "and young professionals, with approximately 25 candidates selected "
    "to attend each year."
)

PROGRAM_DETAILS = [
    ("Host Country:", "Sweden"),
    ("Location:", "Uppsala University"),
    ("Program Dates:", "25–29 August 2025"),
    ("Deadline:", "16th March 2026"),
]

FINANCIAL_BENEFITS = [
    "Round Airfare Tickets, Accommodation, Tuition, Visa Cost, "
    "Travel Insurance, Local Transport in Sweden and Food."
]

ELIGIBILITY = [
    "Candidates from around the world are eligible to apply.",
    "Students, researchers, policymakers, practitioners.",
    "Completed a bachelor's degree before the program began.",
    "Currently enrolled in or recently graduated from a university.",
]

HOW_TO_APPLY = (
    "All applicants must adhere to the application procedures outlined "
    "on the official website. The link to the website is provided below."
)

Now fill this exact template using the raw information I provide."""

CAPTION_SYSTEM = """You are a professional social media content writer for a scholarship platform.
Generate a highly engaging, SEO-friendly social media caption.
Include: title line with emojis, 1-2 line description, 3-4 benefit bullet points, dates, deadline, website link, 4-6 hashtags.
Format:
[flag]🚀 [Program Name]
[description]
✔ Benefit 1
✔ Benefit 2
✔ Benefit 3
📅 [Dates]
⏳ Deadline: [Deadline]
More details:
[scholarglow link]
#Hashtag1 #Hashtag2 #Hashtag3"""

HTML_SYSTEM = """Make sure to return the complete input text in html format, also making sure that all text, including paragraphs, headings, etc., everything is in black, and text font is also consistent. Do not add title at the beginning. Moreover, text size should also be consistent other than headings. Do not include any extra html tags like ```html etc"""


# ── Helper functions ─────────────────────────────────────────────────────────

def get_links():
    """Fetch 3 recent post links from scholarglow.com."""
    try:
        response = requests.get("https://scholarglow.com/", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        links_filtered = [l for l in links if len(l) > 60]
        links_filtered = links_filtered[7:]
        return links_filtered[0], links_filtered[1], links_filtered[2]
    except Exception as e:
        return (
            "https://scholarglow.com/",
            "https://scholarglow.com/",
            "https://scholarglow.com/",
        )


def _chat(system: str, user: str, model: str = "gpt-4o-mini", max_tokens: int = 3000) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ── Main pipeline (generator, yields progress dicts) ────────────────────────

def run_pipeline(raw_text: str, apply_link: str, official_link: str):
    """
    Generator that runs the full pipeline and yields progress events.
    Each event is a dict: { "step": str, "status": "running"|"done"|"error", "data": any }
    Final event has "status": "complete" and "data": { wp_url, poster_b64, post_b64, caption }
    """

    results = {}

    # Step 1: Fetch "Also Check" links
    yield {"step": "Fetching recent post links from scholarglow.com…", "status": "running"}
    try:
        links = get_links()
        yield {"step": "✅ Recent links fetched", "status": "done"}
    except Exception as e:
        yield {"step": f"⚠️ Could not fetch links (using fallback): {e}", "status": "done"}
        links = ("https://scholarglow.com/", "https://scholarglow.com/", "https://scholarglow.com/")

    # Build user prompt for blog generation
    user_prompt = f"""{raw_text}

Apply Link: {apply_link}
Official Website: {official_link}

Also Check 1: {links[0]}
Also Check 2: {links[1]}
Also Check 3: {links[2]}
"""

    # Step 2: Generate blog article
    yield {"step": "Generating blog article with GPT-4.1…", "status": "running"}
    try:
        blog_text = _chat(BLOG_SYSTEM, user_prompt, model="gpt-4.1", max_tokens=3000)
        title_match = re.search(r"Title:\s*(.*?)\n", blog_text)
        category_match = re.search(r"Categories\s*=\s*(\[\d+(?:,\s*\d+)*\])", blog_text)
        main_title = title_match.group(1).strip() if title_match else "Scholarship Opportunity"
        categories = ast.literal_eval(category_match.group(1)) if category_match else [5]

        modified = blog_text
        if title_match:
            modified = modified.replace(title_match.group(0), "")
        if category_match:
            modified = modified.replace(category_match.group(0), "")
        cleaned_text = modified.strip()

        results["main_title"] = main_title
        results["categories"] = categories
        results["cleaned_text"] = cleaned_text
        yield {"step": f"✅ Blog generated — Title: {main_title}", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ Blog generation failed: {e}", "status": "error"}
        return

    # Step 3: Extract poster fields
    yield {"step": "Extracting poster fields with GPT…", "status": "running"}
    try:
        poster_format_text = _chat(POSTER_FORMAT_SYSTEM, cleaned_text, model="gpt-4o", max_tokens=800)
        title_m = re.search(r'title\s*=\s*"([^"]*)"', poster_format_text)
        bullets_m = re.search(r"bullets\s*=\s*(\[[\s\S]*?\])\s*,\s*deadline_label", poster_format_text)
        deadline_m = re.search(r'deadline_label\s*=\s*"([^"]*)"', poster_format_text)
        country_m = re.search(r'selected_country\s*=\s*"([^"]*)"', poster_format_text)

        poster_title = title_m.group(1) if title_m else main_title
        poster_bullets = ast.literal_eval(bullets_m.group(1)) if bullets_m else [
            ("Host Country", "International"), ("Dates", "TBD"), ("Open To", "All Nationalities"), ("Application Fee", "None")
        ]
        poster_deadline = deadline_m.group(1) if deadline_m else "Check website for details"
        poster_country = country_m.group(1) if country_m else "eu"

        yield {"step": "✅ Poster fields extracted", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ Poster field extraction failed: {e}", "status": "error"}
        return

    # Step 4: Generate landscape poster (poster_T7)
    yield {"step": "Generating landscape poster (1200×630)…", "status": "running"}
    try:
        os.chdir(AUTOMATION_DIR)
        poster_path = create_poster(poster_title, poster_bullets, poster_deadline, poster_country)
        results["poster_path"] = poster_path
        results["poster_b64"] = image_to_base64(poster_path)
        yield {"step": "✅ Landscape poster generated", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ Landscape poster failed: {e}", "status": "error"}
        return

    # Step 5: Convert blog to HTML
    yield {"step": "Converting blog to clean WordPress HTML…", "status": "running"}
    try:
        html_blog = _chat(HTML_SYSTEM, cleaned_text, model="gpt-4o", max_tokens=3000)
        html_cleaned = re.sub(r"<head>.*?</head>", "", html_blog, flags=re.DOTALL).strip()
        results["html_blog"] = html_cleaned
        yield {"step": "✅ HTML conversion done", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ HTML conversion failed: {e}", "status": "error"}
        return

    # Step 6: Post to WordPress
    yield {"step": "Uploading poster & publishing to WordPress…", "status": "running"}
    try:
        post_link = post_to_wordpress(main_title, categories, html_cleaned, poster_path)
        results["post_link"] = post_link or "https://scholarglow.com"
        yield {"step": f"✅ Published: {results['post_link']}", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ WordPress posting failed: {e}", "status": "error"}
        return

    # Step 7: Extract Instagram post fields
    yield {"step": "Extracting Instagram post fields with GPT…", "status": "running"}
    try:
        post_format_text = _chat(POST_FORMAT_SYSTEM, cleaned_text, model="gpt-4o-mini", max_tokens=1000)
        namespace = {}
        exec(post_format_text, {}, namespace)
        yield {"step": "✅ Instagram post fields extracted", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ Instagram field extraction failed: {e}", "status": "error"}
        return

    # Step 8: Generate Instagram portrait poster (post_T2)
    yield {"step": "Generating Instagram portrait poster (1080×1350)…", "status": "running"}
    try:
        post_path = create_post(
            namespace.get("SELECTED_COUNTRY", "eu"),
            namespace.get("TITLE", main_title),
            namespace.get("INTRO_1", ""),
            namespace.get("INTRO_2", ""),
            namespace.get("PROGRAM_DETAILS", []),
            namespace.get("FINANCIAL_BENEFITS", []),
            namespace.get("ELIGIBILITY", []),
            namespace.get("HOW_TO_APPLY", ""),
        )
        results["post_path"] = post_path
        results["post_b64"] = image_to_base64(post_path)
        yield {"step": "✅ Instagram poster generated", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ Instagram poster failed: {e}", "status": "error"}
        return

    # Step 9: Generate social media caption
    yield {"step": "Generating social media caption…", "status": "running"}
    try:
        caption_prompt = f"{results['post_link']}\n{main_title}\n{cleaned_text}"
        caption = _chat(CAPTION_SYSTEM, caption_prompt, model="gpt-4o-mini", max_tokens=600)
        results["caption"] = caption
        yield {"step": "✅ Caption generated", "status": "done"}
    except Exception as e:
        yield {"step": f"❌ Caption generation failed: {e}", "status": "error"}
        return

    # Final: emit all results
    yield {
        "step": "🎉 Pipeline complete!",
        "status": "complete",
        "data": {
            "wp_url": results.get("post_link", ""),
            "poster_b64": results.get("poster_b64", ""),
            "post_b64": results.get("post_b64", ""),
            "caption": results.get("caption", ""),
            "title": results.get("main_title", ""),
        },
    }
