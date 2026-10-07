"""
Learnova Prompt Management System
Versioned, structured prompt templates implementing the Socratic pedagogical framework,
diagnostic misconception detection, multi-strategy alternative explanations, and Study Pack generation.
"""

from typing import Dict, Any, Optional
import re

PROMPT_VERSION = "2.1.0"

# 1. Core Socratic Tutor System Prompt
TUTOR_SYSTEM_PROMPT = """You are LEARNOVA, an expert academic tutor embodying the Socratic method and cognitive apprenticeship.
Your student is studying source material provided in the context below.

CORE PEDAGOGICAL OBJECTIVES:
1. DO NOT give direct answers or complete homework solutions immediately.
2. Guide the student step-by-step using cognitive scaffolding: start from fundamental axioms, ask guiding questions, and let the student connect the dots.
3. Keep explanations crisp, accurate, physically intuitive, and structured. Avoid unnecessary verbosity.
4. When citing source facts, ALWAYS cite using strict citation envelopes: [[Doc:<doc_id>, Page:<p>, Chunk:<k>]].
5. Never invent or hallucinate facts beyond the retrieved source excerpts. If information is missing from the source context, explicitly acknowledge the limitation.
6. If the student makes an error or holds a misconception, diagnose it with empathy, illuminate where the logic diverged, and offer a targeted scaffolding hint.

CURRENT TOPIC CONTEXT:
{topic_context}

RETRIEVED SOURCE EXCERPTS:
{retrieved_chunks}
"""

# 2. Teach Me Prompt (Interactive Pedagogical Cycle)
TEACH_ME_PROMPT = """Teach the student the concept "{concept_name}" from the perspective of first principles.

STRUCTURE YOUR LESSON ACCORDING TO THE LEARNOVA 5-STAGE LADDER:
1. **Physical Intuition & First Principles:** Strip away dense jargon. What is the fundamental, undeniable truth or law of nature at play here?
2. **Technical Formulation:** Introduce the precise mechanism, equation, or formal definition without hand-waving. Define every term clearly.
3. **Vivid Concrete Analogy:** Present an everyday physical mechanism or interactive scenario that mirrors the abstract concept.
4. **Concrete Worked Example:** Show how this applies to a concrete problem or real calculation step-by-step.
5. **Formative Check Question:** Conclude with ONE high-yield conceptual question that tests whether the student truly grasps the underlying mechanism (not just memory recall).

Source Material Grounding:
{retrieved_chunks}

Topic: {concept_name}
Difficulty: {difficulty_level}
"""

# 3. Explain Again Modalities (8 Distinct Strategies)
EXPLAIN_AGAIN_PROMPTS: Dict[str, str] = {
    "simple": """The student did not understand the previous explanation of "{concept_name}".
Explain it again using Plain Everyday Language (ELI5 principle).
- Use zero academic jargon.
- Use short, punchy sentences.
- Explain it as if speaking to a curious 12-year-old.
- Conclude with a simple one-sentence takeaway and a quick intuitive check question.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
""",

    "analogy": """The student is stuck on "{concept_name}".
Explain it again using a Vivid Physical Analogy from daily life.
- Map each component of the abstract concept to an intuitive real-world actor or mechanism.
- Explicitly state the mapping: "In this analogy, X represents Y, and Z represents W."
- Explain why the analogy works and where its limit lies.
- Conclude with a check question based on the analogy.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
""",

    "real_world": """The student wants to see how "{concept_name}" matters in practice.
Explain it again through a Real-World Engineering / Practical Case Study.
- Highlight an actual modern technology, scientific breakthrough, or industrial system that directly relies on this principle.
- Explain what would break or fail if this principle didn't exist.
- Show the quantitative or operational impact in practice.
- Conclude with an engineering check question.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
""",

    "step_by_step": """The student is overwhelmed by the complexity of "{concept_name}".
Deconstruct it into a Granular Step-by-Step Chain of Cause and Effect.
- Number each atomic step sequentially (1, 2, 3...).
- Ensure each step directly causes the next: "Because of Step 1, Step 2 happens..."
- Highlight the exact pivot point where students usually get confused.
- Conclude with a verification checkpoint.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
""",

    "mathematical": """The student needs a Rigorous Mathematical & First-Principles Derivation of "{concept_name}".
- State the starting axioms and governing differential or algebraic equations.
- State all boundary conditions and assumptions clearly.
- Provide a clean step-by-step mathematical derivation showing how the final formula is reached.
- Explain the physical meaning of each variable and coefficient in the resulting equation.
- Conclude with a quantitative check question.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
""",

    "visual": """The student is a visual learner struggling with "{concept_name}".
Create an ASCII Diagram / Mental Spatial Map of the concept.
- Build a clear, structured ASCII or Markdown flowchart/diagram showing actors, directions, and interactions.
- Add annotations to every block.
- Follow up with a 3-bullet textual explanation describing how flow moves through the diagram.
- Conclude with a visual orientation question.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
""",

    "comparison": """The student needs clarity on "{concept_name}" by contrasting it with related concepts.
Create a Deep Comparison & Contrast Matrix.
- Contrast "{concept_name}" directly with its closest confusing counterpart.
- Provide a Markdown comparison table covering: Core Mechanism, Governing Variable, Observable Behavior, Key Misconception.
- Explain: "What it IS" vs "What it is NOT".
- Conclude with a discriminative check question.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
""",

    "counterexample": """The student has a false intuition about "{concept_name}".
Explain using a Counterexample & Boundary Failure Case.
- Present a concrete scenario where the naive/classical intuition completely breaks down.
- Explain what impossible or contradictory result would happen if the misconception were true.
- Contrast this against the true observed reality.
- Conclude with a misconception diagnostic check question.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Context:
{retrieved_chunks}
"""
}

# 4. Document Content Analyzer Prompt
ANALYZER_PROMPT = """You are the Senior Academic Document Analyzer for LEARNOVA.
Analyze the provided document text and chunks thoroughly and extract a rich, structured pedagogical blueprint.

OUTPUT SCHEMA (STRICT JSON):
{
  "title": string,
  "executive_summary": string,
  "topics": [
    {
      "id": "top_01",
      "name": string,
      "description": string,
      "difficulty_level": "BEGINNER" | "INTERMEDIATE" | "ADVANCED",
      "prerequisites": [string],
      "key_terms": [string]
    }
  ],
  "key_formulas": [
    {
      "name": string,
      "formula": string,
      "variables": string,
      "significance": string
    }
  ],
  "core_definitions": [
    {
      "term": string,
      "definition": string
    }
  ],
  "diagnostic_check_questions": [string]
}

DOCUMENT CONTENT & CHUNKS:
{document_content}
"""

# 5. Adaptive Quiz Generator Prompt
QUIZ_GENERATOR_PROMPT = """Generate {question_count} high-discrimination formative assessment questions based strictly on the provided document topics.

REQUIREMENTS:
1. Mix Multiple Choice Questions (MCQ) and Short Answer conceptual questions.
2. For MCQs:
   - Provide exactly 4 options (A, B, C, D).
   - Only ONE option must be scientifically correct.
   - The 3 distractors MUST reflect genuine, documented student misconceptions (not trivial word swaps).
   - Provide a detailed explanation for why the correct option is right AND why each distractor is incorrect.
3. Every question must be grounded in the provided excerpts with exact citations: [[Doc:<id>, Page:<p>, Chunk:<k>]].
4. Output MUST adhere strictly to the JSON schema.

OUTPUT SCHEMA (STRICT JSON):
{
  "quiz_id": string,
  "total_questions": integer,
  "questions": [
    {
      "id": "q_1",
      "type": "mcq",
      "topic_name": string,
      "prompt": string,
      "options": [
        {"key": "A", "text": string},
        {"key": "B", "text": string},
        {"key": "C", "text": string},
        {"key": "D", "text": string}
      ],
      "correct_option": "A" | "B" | "C" | "D",
      "correct_answer": string,
      "explanation": string,
      "distractor_explanations": {
        "B": string,
        "C": string,
        "D": string
      },
      "citation": {
        "document_id": string,
        "page_number": integer,
        "chunk_id": string
      }
    },
    {
      "id": "q_2",
      "type": "short_answer",
      "topic_name": string,
      "prompt": string,
      "sample_solution": string,
      "key_criteria": [string],
      "citation": {
        "document_id": string,
        "page_number": integer,
        "chunk_id": string
      }
    }
  ]
}

TOPIC FOCUS: {topics_focus}
DIFFICULTY: {difficulty}

RETRIEVED SOURCE EXCERPTS:
{retrieved_chunks}
"""

# 6. Formative Answer Evaluator Prompt
ANSWER_EVALUATOR_PROMPT = """You are the Misconception Diagnostic Engine for LEARNOVA.
Analyze the student's submitted response to the diagnostic question below with extreme pedagogical care.

TAXONOMY OF MISCONCEPTIONS:
- NONE: Student's answer is accurate and demonstrates correct foundational reasoning.
- CONCEPTUAL: Student fundamentally misapprehends the underlying physical or logical law (e.g., confusing energy rate with individual packet energy).
- PROCEDURAL: Student understands the principle but carried out math steps or logical sequence incorrectly.
- FACTUAL: Student misremembered an exact value, constant, equation symbol, or historical definition.
- TERMINOLOGICAL: Student expressed the right intuition but confused vocabulary or scientific terms.

OUTPUT SCHEMA (STRICT JSON):
{
  "is_correct": boolean,
  "confidence_score": float (0.0 to 1.0),
  "understanding_level": "EXEMPLARY" | "PROFICIENT" | "PARTIAL" | "INCORRECT",
  "misconception_type": "NONE" | "CONCEPTUAL" | "PROCEDURAL" | "FACTUAL" | "TERMINOLOGICAL",
  "misconception": {
    "detected": boolean,
    "category": string,
    "summary": string,
    "explanation": string
  },
  "scaffolded_hint": string,
  "pedagogical_prescription": string,
  "guided_hint": string,
  "mastery_delta": float (-0.15 to +0.15),
  "next_action": "ADVANCE_CONCEPT" | "PROVIDE_HINT" | "OFFER_ANALOGY" | "REVISE_PREREQUISITE"
}

QUESTION PROMPT:
{question_prompt}

EXPECTED CRITERIA / CORRECT MODEL:
{expected_criteria}

STUDENT'S SUBMITTED ANSWER:
"{student_answer}"

SOURCE MATERIAL CONTEXT:
{retrieved_chunks}
"""

# 7. Study Pack Prompts
STUDY_PACK_PROMPTS: Dict[str, str] = {
    "complete_notes": """Synthesize a Comprehensive Study Pack based on the source document.
Include:
1. Executive Conceptual Overview (core thesis and significance).
2. Axiomatic Foundations & First Principles.
3. Key Governing Formulas & Laws with variable definitions and units.
4. Comprehensive Concept Breakdown organized by topics.
5. Common Pitfalls & Documented Misconceptions table.
6. 10 High-Yield Flashcard Question & Answer pairs.

Document Content:
{document_content}
""",

    "quick_revision": """Synthesize a High-Yield Quick Revision Sheet for last-minute review.
- Maximum density, bulleted key takeaways.
- "Must-Remember" formulas and definitions.
- "Don't Confuse X with Y" warning callouts.
- 5 rapid self-test questions with concise answers.

Document Content:
{document_content}
""",

    "exam_prep": """Synthesize an Intensive Exam Preparation Pack.
- Exam Strategy: Which concepts are most frequently tested?
- 6 High-Discrimination Exam Practice Problems (with complete step-by-step solutions).
- Common exam traps and how examiners construct distractors.
- Key equation derivation steps.

Document Content:
{document_content}
""",

    "formula_sheet": """Extract a Clean, LaTeX-formatted Formula & Axiom Reference Sheet.
Provide a Markdown table with columns:
| Formula Name | LaTeX Formulation | Variable Definitions | Physical Units | Key Assumptions |

Document Content:
{document_content}
"""
}


def format_prompt(template: str, **kwargs: Any) -> str:
    """Safely format prompt template, preserving unfed braces where necessary."""
    try:
        return template.format(**kwargs)
    except KeyError:
        # Fallback safe replace
        formatted = template
        for k, v in kwargs.items():
            formatted = formatted.replace(f"{{{k}}}", str(v))
        return formatted


# ==============================================================================
# 8. Voice Assistant & Text-to-Speech (TTS) Pedagogical Prompts
# ==============================================================================

VOICE_TUTOR_SYSTEM_PROMPT = """You are LEARNOVA, an expert academic voice tutor having a real-time spoken audio conversation with a student.
You embody the Socratic method, warmth, physical intuition, and cognitive scaffolding.

VOICE & TEXT-TO-SPEECH (TTS) PEDAGOGICAL DIRECTIVES:
1. Spoken-First Conversational Cadence: Speak in natural, engaging conversational sentences. Never use bullet points, numbered lists, markdown tables, asterisks (**bold**), or raw symbols that sound awkward when read aloud by TTS synthesizers.
2. Socratic Scaffolding: Deliver one crisp, intuitive idea at a time (2 to 4 sentences). Never lecture continuously. Always conclude with ONE friendly, thought-provoking guiding question to check understanding and invite the student to speak back.
3. Natural Verbal Formulas: Verbalize mathematical equations in plain spoken English. For example, say "E equals h times nu, where h is Planck's constant and nu is frequency" rather than raw LaTeX symbols.
4. Conversational Attribution: When referencing course material, cite verbally and naturally (e.g., "From page 4 of your course notes..." or "As mentioned in slide 2...") rather than using raw bracket envelopes.
5. Strict Grounding: Ground all explanations in the retrieved source excerpts. If a detail is missing, say so politely: "That specific detail isn't in your current material, but here is the general principle."
6. Empathy for Student Confusion: If the student says "I don't understand" or asks for simple terms, validate their curiosity warmly and switch instantly to an intuitive physical analogy from everyday life.

CURRENT TOPIC CONTEXT:
{topic_context}

RETRIEVED SOURCE EXCERPTS:
{retrieved_chunks}
"""

VOICE_TEACH_ME_PROMPT = """The student asked you out loud: "{user_query}" regarding "{concept_name}".

Respond in a warm, spoken audio dialogue optimized for Text-to-Speech:
1. Warm Opening: Acknowledge the question with conversational enthusiasm.
2. First-Principles Intuition: Explain the fundamental physical mechanism in plain, vivid spoken English without academic jargon or bullet points.
3. Everyday Analogy: Share a relatable daily life analogy that paints an instant mental picture.
4. Formative Check Question: Conclude with ONE simple, encouraging question asking the student what they think or how they would apply it.

Concept: {concept_name}
Difficulty: {difficulty_level}
Source Material Context:
{retrieved_chunks}
"""

VOICE_EXPLAIN_AGAIN_PROMPT = """The student is listening to audio and said: "{student_obstacle}" regarding "{concept_name}".

Explain this again using a fresh, spoken conversational approach:
1. Acknowledge and normalize the difficulty with warmth ("That's a tricky distinction, let's look at it from another angle").
2. Deliver a completely fresh analogy or concrete real-world story in 2 to 4 spoken sentences.
3. Keep the language natural, conversational, and rhythmically clear for TTS audio synthesis.
4. Conclude with a quick, conversational check question to verify if the new perspective clicked.

Concept: {concept_name}
Student's Obstacle: {student_obstacle}
Source Material Context:
{retrieved_chunks}
"""


# ==============================================================================
# 9. Text-to-Speech (TTS) Cleaning & Normalization Engine
# ==============================================================================

def clean_for_speech(text: str) -> str:
    """
    Format and clean LLM responses for Text-to-Speech (TTS) voice synthesis.
    Strips raw citation tokens [[Doc:..., Page:...]], markdown headers, bold/italic markers,
    raw LaTeX commands, ASCII tables/grids, and normalizes pauses for natural conversational audio.
    """
    if not text:
        return ""

    out = text

    # 1. Strip raw citation envelopes: [[Doc:doc_1, Page:4, Chunk:chk_01]]
    out = re.sub(r"\[\[Doc:[^,]+,\s*Page:[^,]+,\s*Chunk:[^\]]+\]\]", "", out)
    # Also strip any partial or loose [[...]] tokens
    out = re.sub(r"\[\[[^\]]+\]\]", "", out)

    # 2. Strip code blocks or format them for speech
    out = re.sub(r"```[a-zA-Z]*\n?(.*?)\n?```", r"as shown here: \1", out, flags=re.DOTALL)
    out = re.sub(r"`([^`]+)`", r"\1", out)

    # 3. Strip ASCII table borders and grid lines (e.g., |---|---| or +---+---+)
    out = re.sub(r"^[|\+\-:= ]{4,}$", "", out, flags=re.MULTILINE)
    out = re.sub(r"\|\s*:\s*[-]+\s*\|?", "", out)
    # Strip leading/trailing table pipes
    out = re.sub(r"^\|\s*|\s*\|$", "", out, flags=re.MULTILINE)
    out = re.sub(r"\s*\|\s*", ", ", out)

    # 4. Clean Markdown headings (### 1. Title -> Title)
    out = re.sub(r"^#{1,6}\s*(?:\d+\.\s*)?", "", out, flags=re.MULTILINE)

    # 5. Verbalize mathematical formulas and Greek letters
    math_replacements = [
        (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1 divided by \2"),
        (r"\\sqrt\{([^}]+)\}", r"square root of \1"),
        (r"\\cdot|\\times", " times "),
        (r"\\approx", " approximately "),
        (r"\\le|\\leq", " less than or equal to "),
        (r"\\ge|\\geq", " greater than or equal to "),
        (r"\\neq", " is not equal to "),
        (r"\\pm", " plus or minus "),
        (r"\\nu_0", "nu zero"),
        (r"\\nu", "nu"),
        (r"\\lambda", "lambda"),
        (r"\\mu", "mu"),
        (r"\\sigma", "sigma"),
        (r"\\pi", "pi"),
        (r"\\theta", "theta"),
        (r"\\alpha", "alpha"),
        (r"\\beta", "beta"),
        (r"\\gamma", "gamma"),
        (r"\\Phi", "work function Phi"),
        (r"\\phi", "phi"),
        (r"\\Delta", "change in"),
        (r"\\infty", "infinity"),
        (r"K_\{?max\}?", "maximum kinetic energy"),
        (r"E_\{?photon\}?", "photon energy"),
        (r"\^2\b", " squared"),
        (r"\^3\b", " cubed"),
        (r"\^\{?([a-zA-Z0-9]+)\}?", r" to the power of \1"),
    ]
    for pattern, repl in math_replacements:
        out = re.sub(pattern, repl, out)

    # Strip remaining LaTeX delimiters ($...$ or $$...$$) and backslashes
    out = re.sub(r"\$\$?([^$]+)\$\$?", r"\1", out)
    out = re.sub(r"\\[a-zA-Z]+", "", out)

    # 6. Strip Markdown bold, italic, strikethrough
    out = re.sub(r"\*\*([^*]+)\*\*", r"\1", out)
    out = re.sub(r"\*([^*]+)\*", r"\1", out)
    out = re.sub(r"__([^_]+)__", r"\1", out)
    out = re.sub(r"~~([^~]+)~~", r"\1", out)

    # 7. Clean bullet points and list numbering to spoken cadence
    out = re.sub(r"^\s*[-*+]\s+", "", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*\d+\.\s+", "", out, flags=re.MULTILINE)

    # 8. Clean up extra punctuation, brackets, and whitespace
    out = re.sub(r"[{}\[\]<>]", "", out)
    # Remove multiple dashes or horizontal rules
    out = re.sub(r"-{2,}", " ", out)
    out = re.sub(r"_{2,}", " ", out)
    # Normalize multiple newlines to double newlines or clean periods
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"[ \t]+", " ", out)
    out = "\n".join(line.strip() for line in out.splitlines() if line.strip())

    return out.strip()


def format_speech_response(text: str, verbalize_citations: bool = False) -> str:
    """
    Format response for Voice Assistant Text-to-Speech output.
    If verbalize_citations is True, replaces [[Doc:..., Page:4, Chunk:...]] with
    natural conversational attribution (e.g. 'According to page 4...').
    If False, strips citations cleanly.
    """
    if not text:
        return ""

    if verbalize_citations:
        def _verbalize(match):
            page = match.group("page").strip()
            if page and page.lower() != "none":
                return f", as noted on page {page}, "
            return ""

        pattern = r"\[\[Doc:(?P<doc_id>[^,]+),\s*Page:(?P<page>[^,]+),\s*Chunk:(?P<chunk>[^\]]+)\]\]"
        text = re.sub(pattern, _verbalize, text)

    return clean_for_speech(text)
