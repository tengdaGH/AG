---
name: structured_research
description: How to conduct structured research with source tracking, fact-checking, and variance logging
---

# Structured Research Skill

Use this skill when researching a topic to produce authoritative, fact-checked documentation. The output should be traceable, auditable, and usable by other agents.

## Step 1: Define Research Scope

Before searching, write down:
- **Topic**: What specific question(s) are you answering?
- **Primary sources**: What are the authoritative/official sources? (e.g., ETS for TOEFL, IELTS for IELTS)
- **Secondary sources**: What expert/community sources should be cross-referenced?

## Step 2: Gather Sources

1. Search with the **primary source domain first** (use `domain` param in `search_web`)
2. Then search without domain restriction for broader coverage
3. Read the actual source pages when possible (`read_url_content`)
4. Record every source in a **Source Table**:

```markdown
| ID | Source | Type | URL |
|----|--------|------|-----|
| S1 | [Name] | Primary (official) | [URL] |
| S2 | [Name] | Secondary (expert) | [URL] |
```

**Source types:**
- `Primary (official)` — The organization that owns/produces the thing being researched
- `Secondary (expert)` — Well-known expert sites, prep sites, academic papers
- `Tertiary (community)` — Forums, Reddit, YouTube comments — use with caution

## Step 3: Extract Data Points

For each key claim or data point:
1. Record **what** the claim is
2. Record **which source(s)** make the claim (use source IDs)
3. Flag any disagreements between sources

## Step 4: Build Variance Log

When sources disagree, create a **Variance Log** entry:

```markdown
### VAR-XXX: [Short Description]

| Source | Claim |
|--------|-------|
| S1 | [What S1 says] |
| S2 | [What S2 says] |
| S3 | [What S3 says] |

**Resolution**: [Which claim we adopt and why]
```

**Resolution rules:**
1. Primary official source always wins over secondary
2. Technical manuals/spec sheets win over marketing pages
3. More recent publications win over older ones
4. When primary sources conflict internally, document the ambiguity with ⚠️
5. Never silently pick one claim — always show the variance

## Step 5: Write the Document

Structure your output document as:

```markdown
# [Topic]

## Sources
[Source Table]

## Variance Log
[All VAR entries]

## [Content sections with inline source citations]
```

**Citation rules:**
- Cite sources inline as `[S1]` or `[S1, S3]`
- Every table row with a factual claim should have a source
- Mark uncertain/disputed facts with ⚠️
- Mark verified-consistent facts with ✅ in the variance log

## Step 6: Store in Knowledge Bank

Save research output to the appropriate location:
- Topic-specific docs → `.agent/knowledge/[domain]/`
- Update the README index if adding a new directory
- Update `history/work_log.md` with what was researched

## Step 7: Maintain Over Time

When revisiting research:
1. Check if sources have updated (new publications, page changes)
2. Add new variance entries if needed
3. Add a `Last verified: [date]` line to the top of the document

---

## Quick Checklist

- [ ] Source table with IDs and types
- [ ] At least one primary (official) source consulted
- [ ] All data points cited with source IDs
- [ ] Variance log for any disagreements
- [ ] Resolution for each variance entry
- [ ] Document saved to knowledge bank
- [ ] Work log updated
