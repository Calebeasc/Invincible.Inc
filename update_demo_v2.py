import sys

with open('demo-to-be-real.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Core Philosophy 3
phil_2_text = 'The UI should act strictly as a live feed of Omni\'s autonomous discoveries.'
phil_3_text = phil_2_text + '\n\n**CORE PHILOSOPHY 3: ABSOLUTE OPERATIONAL REALITY:** Once a tool or phase is marked as "COMPLETED" or "RELEASED", it MUST be 100% functional and operational. The use of demo data, synthetic placeholders, or "simulated success" stubs is strictly forbidden. Omni is a tactical tool, not a dashboard demo. Every finding must be derived from real-world sensors or live web intelligence.'

if phil_2_text in content and '**CORE PHILOSOPHY 3' not in content:
    content = content.replace(phil_2_text, phil_3_text)

# Photos Section in Dossier
dossier_target = '7. The Sovereign Vault: All-Source Intelligence Dossiers'
photo_layout_text = r'''#### [ ] **A. The "Sovereign Intelligence Dossier" (Human-Readable / .md)**
*   **Design Philosophy:** A high-impact, tactical Markdown report designed for rapid operator briefing. It uses a minimalist "Invincible.Inc" aesthetic with clear headings and categorized data blocks.
*   **Layout Sections:**
    0.  **[PROFILE PHOTO]:** If a high-confidence headshot is found, it MUST be placed at the absolute top of the file as an embedded image.
    1.  **[SUMMARY]:** A 3-sentence high-level overview of the target's current status and risk level.
    2.  **[IDENTITY ANCHORS]:** Core data (Full Name, Verified Emails, Phone Numbers, Physical Addresses).
    3.  **[PATTERN OF LIFE (POL)]:** A list of frequent locations (Home, Work, Social) with "Active Times" (e.g., "Mon-Fri 0900-1700 at [Work Address]").
    4.  **[DIGITAL FOOTPRINT]:** A table of discovered social accounts, website mentions, and leaked credentials.
    5.  **[VISUAL EVIDENCE / PHOTOS]:** A dedicated section containing all photos discovered and face-matched to the target. Images should be displayed as a gallery with timestamps and source URLs.
    6.  **[ASSOCIATE GRAPH]:** A list of known associates, family members, and frequently co-located devices.
    7.  **[VULNERABILITY REPORT]:** Open ports, exposed tech stacks, and suggested infiltration vectors.'''

# Finding the existing A. sections and replacing them with the updated version
import re
pattern = re.compile(r'#### \[ \] \*\*A\. The "Sovereign Intelligence Dossier".*?Suggested infiltration vectors\.', re.DOTALL)
content = pattern.sub(photo_layout_text, content)

# Custom PimEyes / Facial Recognition logic
facial_recon_text = r'''### [ ] 3. Visual Surveillance & Biometric Identification (VINT)
*   **What would be used:** OpenALPR (License Plates), OpenCV + DeepFace / `face_recognition`, Pixel-based Geolocation (like GeoSpy API or local equivalent).
*   **The "Omni-PimEyes" Custom Engine:** 
    - **Development:** Build a custom Python module `vint_search.py` that utilizes `DeepFace` to create a biometric hash of the target's face. 
    - **Infiltration:** Automatically scour pre-indexed facial databases and reverse-image search engines.
    - **Redundancy (Maximal Gathering):** For 100% coverage, Omni MUST integrate and automate searches across:
        1. **PimEyes** (via stealth scraping/API).
        2. **FaceCheck.id** (ID search).
        3. **Yandex Images** (High-accuracy facial matching).
        4. **Google Lens/Images** (Broad context).
        5. **Social-Searcher** (Profile matching).
    - **Action:** Omni downloads results from ALL of these simultaneously, runs a local `face_recognition` compare to confirm the match, and only pushes high-confidence hits to the Dossier.
*   **Useful Features:** "Scan Video Feed for Target" - taking the CCTV feed URLs we already have in `UttPage.xaml.cs` and piping those frames through `deep_look.py` constantly. If a face matches, the UI flashes red and locks the map onto that camera.'''

pattern_facial = re.compile(r'### \[ \] 3\. Visual Surveillance & Biometric Identification \(VINT\).*?locks the map onto that camera\.', re.DOTALL)
content = pattern_facial.sub(facial_recon_text, content)

with open('demo-to-be-real.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Success")