---
name: brainstorming
description: "À utiliser avant toute création — nouvelle feature, composant, fonctionnalité, changement de comportement — pour explorer l'intention, les contraintes et les approches AVANT d'écrire quoi que ce soit. Phase de dialogue uniquement : la mise en forme du plan revient ensuite à plan-notion."
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine
the idea. Once you understand what you're building, present the design and get approval.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any
implementation action until you have presented a design and the user has approved it. This
applies to EVERY project regardless of perceived simplicity.

**Plan-mode exception (Benjamin):** if Claude Code’s native plan mode is active, do not create
a Notion page. The native plan has its own validation cycle, and two competing plans would make
it ambiguous which one is authoritative. In every other mode, the output of this dialogue is a
Notion page — see “Boundary With plan-notion”.
</HARD-GATE>

## Boundary With plan-notion

- **This skill (chat)** — understand the need, surface constraints, propose approaches and
  converge on an approved design.
- **Once the design is approved, hand it over to `plan-notion`**, which writes it up. This skill
  produces no artifact of its own, so stopping here loses the work: a design that exists only in
  the conversation disappears at the next context compaction, and Benjamin has no page to comment
  on or check boxes in.
- **Single exception — native plan mode.** When it is active, it owns the plan; do not invoke
  `plan-notion`.

Never write a design doc to `docs/` and never commit one merely to preserve a plan — the Notion
page is where a design lives.

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change
— all of them. "Simple" projects are where unexamined assumptions cause the most wasted work.
The design can be short (a few sentences for truly simple projects), but you MUST present it and
get approval.

## Checklist

1. **Explore project context** — files, docs, recent commits. On an indexed repo, use the
   `codebase-memory` MCP (`get_architecture`, `search_code`, `query_graph`) rather than reading
   whole files.
2. **Ask clarifying questions** — one at a time, only where they change a substantive choice.
3. **Propose approaches** — with trade-offs and a recommendation.
4. **Present and obtain approval for the design.**
5. **Hand the approved design over to `plan-notion`**, which turns it into a page. Unless native
   plan mode is active — that plan is then authoritative and this skill stops here.

## The Process

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Before asking detailed questions, assess scope: if the request describes multiple independent
  subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag
  this immediately. Don't spend questions refining details of a project that needs to be
  decomposed first.
- If the project is too large for a single spec, help decompose into sub-projects: what are the
  independent pieces, how do they relate, what order should they be built? Then brainstorm the
  first sub-project through the normal design flow. Each sub-project gets its own plan page.
- For appropriately-scoped projects, ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message — if a topic needs more exploration, break it into several
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- **Verify what is verifiable before proposing a choice** — a constraint measured in the docs or
  in the tool beats a plausible-sounding option
- YAGNI ruthlessly — remove unnecessary features from every approach and design

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words
  if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through
  well-defined interfaces, and can be understood and tested independently
- For each unit, you should be able to answer: what does it do, how do you use it, and what does
  it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the
  internals without breaking consumers? If not, the boundaries need work.
- Smaller, well-bounded units are also easier for you to work with — you reason better about code
  you can hold in context at once, and your edits are more reliable when files are focused. When
  a file grows large, that's often a signal that it's doing too much.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work (e.g., a file that's grown too large,
  unclear boundaries, tangled responsibilities), include targeted improvements as part of the
  design — the way a good developer improves code they're working in.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

## After the Design

Once the design is approved, **invoke `plan-notion`** — it turns the design into a page, with the
open questions as callouts and the `Exécution` chapter. Invoke it explicitly: a skill never loads
another one by itself, so without that call the handoff simply does not happen and the design
stays trapped in the conversation.

In native plan mode, stop here instead — that plan is authoritative.

Before handing over, self-check what you're about to pass on:

1. **Placeholder scan** — any "TBD", "TODO", vague requirement? Resolve or turn it into an
   explicit open question with a reco.
2. **Internal consistency** — do any parts contradict each other? Does the architecture match
   the feature description?
3. **Scope check** — focused enough for a single plan, or does it need decomposition?
4. **Ambiguity check** — could any requirement be read two ways? Pick one and make it explicit.

---

*Adapté de [obra/superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent / Prime
Radiant). Récupéré le 2026-08-03. Modifications : sortie redirigée de `writing-plans` vers
`plan-notion`, plus d'écriture de spec dans `docs/` ni de commit, « visual companion » retiré
(pas de navigateur local sur le VPS, et `plan-notion` a déjà sa voie maquette via Vercel),
renvoi codebase-memory ajouté.*

*2026-08-17 — le corps interdisait en trois endroits d'appeler `plan-notion` (défaut au mode
plan natif) alors que la description promettait le passage de main. Inversé : `plan-notion` est
désormais la sortie par défaut, le mode plan natif devient la seule exception.*
