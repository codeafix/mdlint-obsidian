"""Tests for Obsidian compatibility rules."""

import pytest
from mdlint_obsidian import validate


def errors_for(rule, content, **kwargs):
    return [e for e in validate(content, **kwargs) if e.rule == rule]


# ---------------------------------------------------------------------------
# std-internal-link
# ---------------------------------------------------------------------------
class TestStdInternalLink:
    def test_md_link_to_note(self):
        errs = errors_for("std-internal-link", "See [My Note](my-note.md).")
        assert len(errs) == 1
        assert errs[0].line == 1

    def test_md_link_with_path(self):
        errs = errors_for("std-internal-link", "See [Note](folder/note.md).")
        assert len(errs) == 1

    def test_md_link_path_no_extension(self):
        errs = errors_for("std-internal-link", "See [Note](folder/note).")
        assert len(errs) == 1

    def test_external_http_not_flagged(self):
        assert errors_for("std-internal-link", "See [Example](https://example.com).") == []

    def test_external_http_plain_not_flagged(self):
        assert errors_for("std-internal-link", "[Link](http://example.com/path/to/page)") == []

    def test_anchor_link_not_flagged(self):
        assert errors_for("std-internal-link", "Jump to [Section](#heading).") == []

    def test_mailto_not_flagged(self):
        assert errors_for("std-internal-link", "[Email](mailto:x@y.com)") == []

    def test_image_not_flagged(self):
        # Images handled by std-internal-image, not this rule
        assert errors_for("std-internal-link", "![alt](image.png)") == []

    def test_not_flagged_inside_code_block(self):
        content = "```\n[Note](note.md)\n```"
        assert errors_for("std-internal-link", content) == []

    def test_line_number(self):
        errs = errors_for("std-internal-link", "First line\n[Note](note.md)")
        assert errs[0].line == 2


# ---------------------------------------------------------------------------
# std-internal-image
# ---------------------------------------------------------------------------
class TestStdInternalImage:
    def test_local_image(self):
        errs = errors_for("std-internal-image", "![alt](image.png)")
        assert len(errs) == 1
        assert errs[0].line == 1

    def test_local_image_with_path(self):
        errs = errors_for("std-internal-image", "![alt](assets/image.png)")
        assert len(errs) == 1

    def test_external_image_not_flagged(self):
        assert errors_for("std-internal-image", "![alt](https://example.com/img.png)") == []

    def test_data_url_not_flagged(self):
        assert errors_for("std-internal-image", "![alt](data:image/png;base64,abc)") == []

    def test_not_flagged_inside_code_block(self):
        content = "```\n![alt](image.png)\n```"
        assert errors_for("std-internal-image", content) == []

    def test_message_suggests_embed_syntax(self):
        errs = errors_for("std-internal-image", "![alt](assets/photo.jpg)")
        assert "![[photo.jpg]]" in errs[0].message

    def test_line_number(self):
        errs = errors_for("std-internal-image", "Line 1\n![alt](img.png)")
        assert errs[0].line == 2


# ---------------------------------------------------------------------------
# std-reference-link
# ---------------------------------------------------------------------------
class TestStdReferenceLink:
    def test_reference_link_usage(self):
        errs = errors_for("std-reference-link", "See [my note][note-ref].")
        assert len(errs) == 1
        assert errs[0].line == 1

    def test_reference_link_definition(self):
        errs = errors_for("std-reference-link", "[note-ref]: https://example.com")
        assert len(errs) == 1

    def test_footnote_def_not_flagged(self):
        # [^id]: is a footnote definition, not a reference link
        assert errors_for("std-reference-link", "[^1]: This is a footnote.") == []

    def test_footnote_ref_not_flagged(self):
        content = "Text[^1].\n\n[^1]: Footnote."
        assert errors_for("std-reference-link", content) == []

    def test_not_flagged_inside_code_block(self):
        content = "```\n[text][ref]\n[ref]: url\n```"
        assert errors_for("std-reference-link", content) == []

    def test_inline_link_not_flagged(self):
        # [text](url) is an inline link, not a reference link
        assert errors_for("std-reference-link", "[text](https://example.com)") == []

    def test_line_number_definition(self):
        errs = errors_for("std-reference-link", "Some text\n[ref]: https://url.com")
        assert errs[0].line == 2


# ---------------------------------------------------------------------------
# heading-no-space
# ---------------------------------------------------------------------------
class TestHeadingNoSpace:
    def test_h1_no_space(self):
        errs = errors_for("heading-no-space", "#My Heading")
        assert len(errs) == 1
        assert errs[0].line == 1

    def test_h2_no_space(self):
        errs = errors_for("heading-no-space", "##My Heading")
        assert len(errs) == 1

    def test_h3_no_space(self):
        errs = errors_for("heading-no-space", "###Section Title")
        assert len(errs) == 1

    def test_valid_h1(self):
        assert errors_for("heading-no-space", "# My Heading") == []

    def test_valid_h2(self):
        assert errors_for("heading-no-space", "## Section") == []

    def test_single_hash_single_word_not_flagged(self):
        # Single # + single word = likely an Obsidian tag, not a broken heading
        assert errors_for("heading-no-space", "#tag") == []
        assert errors_for("heading-no-space", "#obsidian") == []

    def test_double_hash_single_word_is_flagged(self):
        # ## is never a valid tag — definitely a broken heading
        errs = errors_for("heading-no-space", "##tag")
        assert len(errs) == 1

    def test_not_flagged_inside_code_block(self):
        content = "```\n#Heading\n```"
        assert errors_for("heading-no-space", content) == []

    def test_line_number(self):
        errs = errors_for("heading-no-space", "Normal line\n##Missing Space")
        assert errs[0].line == 2

    def test_message_shows_fix(self):
        errs = errors_for("heading-no-space", "##My Title")
        assert "## My Title" in errs[0].message


# ---------------------------------------------------------------------------
# indented-code-block
# ---------------------------------------------------------------------------
class TestIndentedCodeBlock:
    def test_indented_after_blank(self):
        content = "Some text\n\n    indented code"
        errs = errors_for("indented-code-block", content)
        assert len(errs) == 1
        assert errs[0].line == 3

    def test_indented_at_start_of_file(self):
        errs = errors_for("indented-code-block", "    indented first line")
        assert len(errs) == 1

    def test_indented_after_nonblank_not_flagged(self):
        # Indented line following non-blank = likely list continuation, not code block
        content = "Some text\n    continuation"
        assert errors_for("indented-code-block", content) == []

    def test_list_indentation_not_flagged(self):
        # 4-space indent that's a nested list item
        content = "- Item\n\n    - Nested item"
        assert errors_for("indented-code-block", content) == []

    def test_not_flagged_inside_fenced_code_block(self):
        content = "```\n    indented inside fence\n```"
        assert errors_for("indented-code-block", content) == []

    def test_three_spaces_not_flagged(self):
        content = "Some text\n\n   three spaces only"
        assert errors_for("indented-code-block", content) == []


# ---------------------------------------------------------------------------
# raw-html
# ---------------------------------------------------------------------------
class TestRawHtml:
    def test_div_tag(self):
        errs = errors_for("raw-html", "<div>Some content</div>")
        assert len(errs) == 1
        assert errs[0].line == 1

    def test_span_tag(self):
        errs = errors_for("raw-html", "Text with <span>inline</span> html.")
        assert len(errs) == 1

    def test_br_self_closing(self):
        errs = errors_for("raw-html", "Line break<br/>here.")
        assert len(errs) == 1

    def test_img_tag(self):
        errs = errors_for("raw-html", '<img src="photo.jpg" />')
        assert len(errs) == 1

    def test_unknown_tag_not_flagged(self):
        # Not in the known HTML tag set
        assert errors_for("raw-html", "<mycustomtag>content</mycustomtag>") == []

    def test_math_less_than_not_flagged(self):
        # $x < 5$ — < followed by space, not a tag
        assert errors_for("raw-html", "The value $x < 5$.") == []

    def test_not_flagged_inside_code_block(self):
        content = "```\n<div>html</div>\n```"
        assert errors_for("raw-html", content) == []

    def test_line_number(self):
        errs = errors_for("raw-html", "Normal text\n<p>Paragraph</p>")
        assert errs[0].line == 2

    def test_only_one_error_per_line(self):
        # Multiple tags on one line — only one error reported
        errs = errors_for("raw-html", "<b>bold</b> and <i>italic</i>")
        assert len(errs) == 1


# ---------------------------------------------------------------------------
# std-horizontal-rule
# ---------------------------------------------------------------------------
class TestStdHorizontalRule:
    def test_triple_asterisk(self):
        errs = errors_for("std-horizontal-rule", "***")
        assert len(errs) == 1
        assert errs[0].line == 1

    def test_spaced_asterisks(self):
        errs = errors_for("std-horizontal-rule", "* * *")
        assert len(errs) == 1

    def test_triple_underscore(self):
        errs = errors_for("std-horizontal-rule", "___")
        assert len(errs) == 1

    def test_spaced_underscores(self):
        errs = errors_for("std-horizontal-rule", "_ _ _")
        assert len(errs) == 1

    def test_hyphen_hr_not_flagged(self):
        assert errors_for("std-horizontal-rule", "---") == []

    def test_spaced_hyphen_hr_not_flagged(self):
        assert errors_for("std-horizontal-rule", "- - -") == []

    def test_bold_not_flagged(self):
        # ***bold*** is emphasis, not an HR
        assert errors_for("std-horizontal-rule", "***bold text***") == []

    def test_not_flagged_inside_code_block(self):
        content = "```\n***\n```"
        assert errors_for("std-horizontal-rule", content) == []

    def test_line_number(self):
        errs = errors_for("std-horizontal-rule", "Some text\n***")
        assert errs[0].line == 2

    def test_message_suggests_hyphen(self):
        errs = errors_for("std-horizontal-rule", "***")
        assert "---" in errs[0].message
