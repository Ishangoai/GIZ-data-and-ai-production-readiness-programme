"""Text Toolkit: a Gradio app to transform and analyse text.
 
The module only exposes ``build_app`` so that ``api/main.py`` can mount the
interface on the FastAPI server. Running this file directly still works, which
makes local testing faster than starting the whole API.
"""

import re
import string
from collections import Counter
from dataclasses import dataclass
 
import gradio as gr
 
CASE_NONE = "No change"
CASE_UPPER = "Uppercase"
CASE_LOWER = "Lowercase"
CASE_TITLE = "Title Case"
CASE_OPTIONS = [CASE_NONE, CASE_UPPER, CASE_LOWER, CASE_TITLE]
 
# Named constants make the numbers explainable and easy to tweak in one place.
WORDS_PER_MINUTE = 200  # Typical adult silent reading speed.
SENTENCE_END_PATTERN = r"[.!?]+"
# The optional apostrophe group keeps "don't" as one word. str.title() would
# produce "Don'T", which looks like a bug to users.
TITLE_WORD_PATTERN = r"\w+(?:'\w+)?"

# --------------------------------------------------------------------------
# Text operations. Kept as pure functions (no Gradio objects) so they can be
# unit tested without starting a server.
# --------------------------------------------------------------------------
def convert_case(text: str, case_choice: str) -> str:
    """Return the text converted to the chosen case."""
    if case_choice == CASE_UPPER:
        return text.upper()
    if case_choice == CASE_LOWER:
        return text.lower()
    if case_choice == CASE_TITLE:
        return re.sub(
            TITLE_WORD_PATTERN,
            lambda match: match.group().capitalize(),
            text,
        )
    return text
 
 
def reverse_word_order(text: str) -> str:
    """Reverse the order of the words (extra whitespace is collapsed)."""
    # split() without arguments is deliberate: it ignores repeated spaces and
    # line breaks, so the output never starts with stray whitespace.
    return " ".join(reversed(text.split()))
 
 
def reverse_characters(text: str) -> str:
    """Reverse every character in the text."""
    return text[::-1]
 
 
def transform_text(
    text: str,
    case_choice: str,
    should_reverse_words: bool,
    should_reverse_characters: bool,
) -> str:
    """Apply every selected operation to the text, in a fixed order."""
    # A fixed order keeps the result predictable. Changing case first means
    # the reversals never have to care about letter case.
    result = convert_case(text, case_choice)
    if should_reverse_words:
        result = reverse_word_order(result)
    if should_reverse_characters:
        result = reverse_characters(result)
    return result
 
 
# --------------------------------------------------------------------------
# Text analysis
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class TextStats:
    """Statistics describing a piece of text."""
 
    word_count: int
    character_count: int
    average_word_length: float
    sentence_count: int
    reading_time_seconds: int
    longest_word: str
    most_common_word: str
 
 
def extract_words(text: str) -> list[str]:
    """Split text into words, ignoring surrounding punctuation."""
    # Stripping punctuation stops "Hello," and "Hello" counting as different
    # words and keeps the average word length honest.
    stripped = (word.strip(string.punctuation) for word in text.split())
    return [word for word in stripped if word]
 
 
def count_sentences(text: str) -> int:
    """Count sentences by splitting on '.', '!' and '?'."""
    parts = re.split(SENTENCE_END_PATTERN, text)
    # The text after the last full stop is usually empty, so skip blanks to
    # avoid counting a sentence that does not exist.
    return sum(1 for part in parts if part.strip())
 
 
def analyze_text(text: str) -> TextStats:
    """Compute statistics for the given text."""
    words = extract_words(text)
    word_count = len(words)
 
    # Return early for empty input: it avoids a division by zero below and
    # gives the user clean zeros instead of an error message.
    if word_count == 0:
        return TextStats(0, len(text), 0.0, 0, 0, "-", "-")
 
    average_length = sum(len(word) for word in words) / word_count
    reading_seconds = round(word_count / WORDS_PER_MINUTE * 60)
    # Lowercase before counting so "The" and "the" are the same word.
    counts = Counter(word.lower() for word in words)
 
    return TextStats(
        word_count=word_count,
        character_count=len(text),
        average_word_length=round(average_length, 2),
        sentence_count=count_sentences(text),
        reading_time_seconds=reading_seconds,
        longest_word=max(words, key=len),
        most_common_word=counts.most_common(1)[0][0],
    )
 
 
def format_extra_stats(stats: TextStats) -> str:
    """Build the Markdown summary shown under the main statistics."""
    return (
        f"- **Sentences:** {stats.sentence_count}\n"
        f"- **Reading time:** about {stats.reading_time_seconds} seconds\n"
        f"- **Longest word:** {stats.longest_word}\n"
        f"- **Most common word:** {stats.most_common_word}"
    )
 
 
def update_stats(text: str) -> tuple[int, int, float, str]:
    """Return the values for every statistics component."""
    stats = analyze_text(text)
    return (
        stats.word_count,
        stats.character_count,
        stats.average_word_length,
        format_extra_stats(stats),
    )
 
 
# --------------------------------------------------------------------------
# Button handlers
# --------------------------------------------------------------------------
def clear_all() -> tuple[str, str, bool, bool]:
    """Reset the input text and every option to its default."""
    return "", CASE_NONE, False, False
 
 
def reuse_output(result: str) -> tuple[str, str, bool, bool]:
    """Move the result into the input box and reset the options."""
    # The options are reset on purpose. Otherwise the same operations would
    # run again on the new input, and reversing twice undoes itself.
    return result, CASE_NONE, False, False
 
 
# --------------------------------------------------------------------------
# User interface
# --------------------------------------------------------------------------
def build_app() -> gr.Blocks:
    """Create the Gradio interface and wire up its events."""
    # Building inside a function (not at import time) means importing this
    # module in api/main.py has no side effects until the app is needed.
    with gr.Blocks(title="Text Toolkit") as app:
        gr.Markdown("# Text Toolkit\nType or paste text, then pick tools.")
 
        input_box = gr.Textbox(
            label="Your text",
            placeholder="Type or paste any text here...",
            lines=6,
        )
 
        with gr.Tabs():
            with gr.TabItem("Case Converter"):
                # "No change" is included so the output starts as the
                # original text instead of forcing a case on the user.
                case_choice = gr.Radio(
                    choices=CASE_OPTIONS,
                    value=CASE_NONE,
                    label="Choose a case",
                )
 
            with gr.TabItem("Text Reverser"):
                reverse_words_box = gr.Checkbox(label="Reverse Word Order")
                reverse_chars_box = gr.Checkbox(label="Reverse All Characters")
 
            with gr.TabItem("Text Analyzer"):
                with gr.Row():
                    word_count = gr.Number(label="Word Count", precision=0)
                    char_count = gr.Number(
                        label="Character Count", precision=0
                    )
                    average_length = gr.Number(
                        label="Average Word Length", precision=2
                    )
                extra_stats = gr.Markdown()
 
        # Read-only so users cannot edit the result by mistake. The copy
        # button covers the real need, which is taking the text elsewhere.
        output_box = gr.Textbox(
            label="Result",
            lines=6,
            interactive=False,
            buttons=["copy"],
        )
 
        with gr.Row():
            use_output_button = gr.Button("Use result as new input")
            clear_button = gr.Button("Clear", variant="stop")
 
        transform_inputs = [
            input_box,
            case_choice,
            reverse_words_box,
            reverse_chars_box,
        ]
        stats_outputs = [word_count, char_count, average_length, extra_stats]
 
        # triggers=None re-runs the function whenever any input changes, so
        # we do not need a separate .change() call for every component.
        gr.on(
            triggers=None,
            fn=transform_text,
            inputs=transform_inputs,
            outputs=output_box,
        )
        # Statistics only depend on the raw text, so the options are not
        # passed in. This avoids needless recalculation.
        input_box.change(update_stats, input_box, stats_outputs)
 
        # Clearing the controls fires their change events, which refresh
        # the result and statistics for us.
        clear_button.click(clear_all, outputs=transform_inputs)
        use_output_button.click(
            reuse_output, inputs=output_box, outputs=transform_inputs
        )
 
    return app
 
 
if __name__ == "__main__":
    # Only runs for quick local testing. In production, api/main.py mounts
    # the app and the server is started by uvicorn.
    build_app().launch(theme=gr.themes.Soft())
 
