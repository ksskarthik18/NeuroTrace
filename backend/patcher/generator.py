"""
NeuroTrace - Patch Generator
Generates minimal code patches using LLM, with retry support.
"""

import difflib

from backend.models import PatchResult, PatchChange, RootCauseResult
from backend.llm.client import get_llm_client
from backend.llm.prompts import PATCH_SYSTEM, PATCH_USER, PATCH_RETRY_USER


def _generate_diff(original: str, patched: str) -> str:
    """Generate a unified diff between original and patched code."""
    original_lines = original.splitlines(keepends=True)
    patched_lines = patched.splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines, patched_lines,
        fromfile="original.py", tofile="patched.py",
    )
    return "".join(diff)


def _extract_changes(original: str, patched: str) -> list[PatchChange]:
    """Extract line-level changes between original and patched code."""
    changes = []
    orig_lines = original.splitlines()
    patch_lines = patched.splitlines()

    matcher = difflib.SequenceMatcher(None, orig_lines, patch_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            for k in range(i1, i2):
                changes.append(PatchChange(
                    line=k + 1,
                    action="replace",
                    old=orig_lines[k] if k < len(orig_lines) else "",
                    new=patch_lines[j1 + (k - i1)] if (j1 + k - i1) < len(patch_lines) else "",
                ))
        elif tag == "delete":
            for k in range(i1, i2):
                changes.append(PatchChange(
                    line=k + 1,
                    action="delete",
                    old=orig_lines[k],
                ))
        elif tag == "insert":
            changes.append(PatchChange(
                line=i1 + 1,
                action="insert",
                new="\n".join(patch_lines[j1:j2]),
            ))

    return changes


async def generate_patch(
    source_code: str,
    root_cause: RootCauseResult,
    attempt: int = 1,
    previous_patch: str | None = None,
    failure_reason: str | None = None,
) -> PatchResult:
    """
    Use LLM to generate a minimal fix patch.
    On retry, includes previous failure context for self-correction.
    """
    if attempt == 1 or previous_patch is None:
        prompt = PATCH_USER.format(
            source_code=source_code,
            bug_type=root_cause.bug_type,
            root_cause=root_cause.root_cause,
            faulty_line=root_cause.faulty_line or "unknown",
        )
    else:
        prompt = PATCH_RETRY_USER.format(
            source_code=source_code,
            bug_type=root_cause.bug_type,
            root_cause=root_cause.root_cause,
            previous_patch=previous_patch,
            failure_reason=failure_reason or "Unknown failure",
        )

    messages = [
        {"role": "system", "content": PATCH_SYSTEM},
        {"role": "user", "content": prompt},
    ]

    try:
        client = get_llm_client()
        data = await client.achat_json(messages)
        patched_code = data.get("patched_code", "")

        if not patched_code.strip():
            return PatchResult(
                patched_code=source_code,
                explanation="LLM returned empty patch",
            )

        diff = _generate_diff(source_code, patched_code)
        changes = _extract_changes(source_code, patched_code)

        return PatchResult(
            patched_code=patched_code,
            diff=diff,
            explanation=data.get("explanation", ""),
            changes=changes,
        )

    except Exception as e:
        return PatchResult(
            patched_code=source_code,
            explanation=f"Patch generation failed: {type(e).__name__}: {str(e)}",
        )
