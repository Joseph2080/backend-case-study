from src.cv._extraction.views import CVExtractedData
from src.llm.views.prompt.file import FilePrompt
from src.llm.views.prompt.template import PromptTemplate, UserPrompt


class CVExtractionPrompt(PromptTemplate):
    Output = CVExtractedData

    def __init__(self, cv: FilePrompt):
        self.cv = cv

    def system_prompt(self) -> str:
        return """
You are given a CV.
Your job is to extract all the information from the CV.

# Important general rules:
- Extract the information in the same language as the CV.
- Only extract information that are actually clearly stated in the CV. Don't synthesize or invent information.
- **CRITICAL: Every non-custom section kind must appear at most once.** If multiple, separated, or interleaved blocks have the same kind, merge their items into one section at the position of its first occurrence, preserving item order.
- This is a structural merge only: never reclassify content to avoid a repeated kind, and never omit, summarize, or condense any item or its text while merging.

# Formatting rules:
- Always format names, job titles, company names, education degrees, and skills in proper title case, even if they appear in ALL UPPERCASE in the PDF. For example:
  - "JOHN DOE" → "John Doe"
  - "HEAD OF MARKETING" → "Head of Marketing"
  - "MICROSOFT CORPORATION" → "Microsoft Corporation"
  - "BACHELOR OF SCIENCE" → "Bachelor of Science"
- Apply standard capitalization rules based on language.
- Keep acronyms in uppercase (e.g., "CEO", "IT", "HR").

# Specific rules:
- For start and end date: If no month is provided, just leave it empty.
- Only assign a location to an item when it is explicitly associated with that specific item in the CV. Never infer locations from organizations, events, general knowledge, or neighboring entries.
- Only use HTML formatting for descriptions.
- When extracting bullet points, always represent them in HTML format with <ul> and <li> tags.
- Represent the sections as they appear in the CV. Don't rearrange items within a section.
- Order unique section kinds by their first occurrence in the document (e.g., if Skills first appears before Education, Skills should come first in your output).
- Don't duplicate information. For example, a section like "Contact information" that is already fully represented in the person_details section should not be extracted as custom section again. Same for e.g. professional summary, etc.
- LinkedIn, GitHub, Xing, and other social-profile URLs must be extracted as social links, never as personal_website.
- For skills sections: Split them up into individual skills. If skills are organized into named sub-categories within the section (e.g., "IT-Kenntnisse", "Programming Languages", "Frameworks"), preserve that grouping structure. The section title itself (e.g., "Skills", "Kompetenzen") is not a group name - look for structure within. If skills are listed as a flat list without sub-categories, put them all in a single group with name=null.
- IMPORTANT: Languages (e.g., German, English, French) must NEVER appear in skills sections. They belong in the languages section only. If you see a "Languages" sub-section within skills, extract those as a separate languages section instead.
- When detecting skill groups, look for visual groupings like headers, bold text, or indentation that indicate category names. Common patterns include "Category: skill1, skill2" or skills listed under a bold/underlined header.
- Extract a privacy clause whenever the CV contains a statement authorizing or consenting to the processing of personal data from the CV, usually for recruitment. It may be an unlabeled sentence in the footer and may reference GDPR, RODO, EU 2016/679, D.Lgs. 196/2003, or equivalent privacy law. Represent it as a privacy_clause section and do not duplicate it as a custom section.
- Ignore signatures completely (as we can't represent them, we also should not try to extract them).
""".strip()  # noqa: E501

    # # JSON rules:
    # - You answer in JSON format according to the schema.
    # - Make sure to not use unnecessary escape characters that lead to invalid or incorrect strings.

    def user_prompt(self) -> UserPrompt:
        return self.cv
