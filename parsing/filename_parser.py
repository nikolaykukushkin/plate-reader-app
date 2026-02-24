"""
Parse experiment metadata from filename.

Supported formats:
  YYYYMMDD_experiment_name_OP.ext           (single experiment)
  YYYYMMDDL_experiment_name_OP.ext          (single, with letter suffix e.g. 20260205A)
  YYYYMMDDL_exp1_OP_YYYYMMDDL_exp2_OP.ext  (multiple experiments)
"""
import os
import re
from typing import Dict, List

# Regex: 8 digits + optional uppercase letter
_DATE_RE = re.compile(r'^(\d{8})([A-Z])?$')


def parse_filename(filepath: str) -> Dict[str, str]:
    """
    Extract experiment metadata from filename (legacy single-experiment).

    Returns dict with keys: 'date', 'name', 'operator'.
    """
    results = parse_multi_experiment_filename(filepath)
    if results:
        r = results[0]
        return {
            'date': r.get('date', ''),
            'name': r.get('name', ''),
            'operator': r.get('operator', ''),
        }
    return {'date': '', 'name': '', 'operator': ''}


def parse_multi_experiment_filename(filepath: str) -> List[Dict[str, str]]:
    """
    Parse a filename that may encode one or more experiments.

    Returns a list of dicts, each with:
      - date:     e.g. '2026-02-05'
      - date_raw: e.g. '20260205A'
      - name:     e.g. 'reverse transplant'
      - operator: e.g. 'NK'
    """
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]
    tokens = name_without_ext.split('_')

    # Find indices of all tokens that look like dates
    date_indices: List[int] = []
    for i, tok in enumerate(tokens):
        if _DATE_RE.match(tok):
            date_indices.append(i)

    if not date_indices:
        return []

    experiments: List[Dict[str, str]] = []

    for seg_num, di in enumerate(date_indices):
        # The segment for this experiment runs from this date token
        # to just before the next date token (or end of tokens).
        if seg_num + 1 < len(date_indices):
            seg_end = date_indices[seg_num + 1]
        else:
            seg_end = len(tokens)

        seg_tokens = tokens[di:seg_end]

        # Parse date
        date_tok = seg_tokens[0]
        m = _DATE_RE.match(date_tok)
        digits = m.group(1)
        suffix = m.group(2) or ''
        date_formatted = f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"
        if suffix:
            date_formatted += suffix

        date_raw = date_tok

        # Determine operator: last token in segment if it's 2-3 uppercase letters
        operator = ''
        name_tokens = seg_tokens[1:]
        if name_tokens:
            last = name_tokens[-1]
            if 1 <= len(last) <= 3 and last.isalpha() and last == last.upper():
                operator = last
                name_tokens = name_tokens[:-1]

        # Everything remaining is the experiment name
        exp_name = ' '.join(name_tokens).strip()
        if exp_name:
            exp_name = exp_name[0].upper() + exp_name[1:]

        experiments.append({
            'date': date_formatted,
            'date_raw': date_raw,
            'name': exp_name,
            'operator': operator,
        })

    return experiments
