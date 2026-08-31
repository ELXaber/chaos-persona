#V08302026
# =============================================================================
# CAIOS PROJECT ANDREW: Vision Verifier
# Domain-agnostic consistency check cross-references claims against measurements.
# Copyright (c) 2025 Jonathan Schack. License: GPL-3.0 -See LICENSE for details- Contact: X @el_xaber or cai-os.com
# =============================================================================

import re
import math
import base64
from typing import Dict, List, Any, Optional

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[VISION_VERIFIER] opencv-python not installed — geometric "
          "verification disabled. Install: pip install opencv-python numpy")

# =========================================================================
# 1. Generic geometric feature extraction - no knowledge of "illusions"
# =========================================================================

def _merge_duplicate_edges(lines: List[Dict], angle_tol_deg: float = 5.0,
                            perp_dist_tol: float = 22.0) -> List[Dict]:
    """
    Canny/Hough commonly detects both edges of a single thick line stroke
    as two separate near-identical segments (top edge + bottom edge).
    Groups segments that are near-parallel, close together perpendicular
    to their shared direction, AND overlap along that direction — this
    last check is essential: two short fin segments from opposite corners
    of the image can share both angle and "distance to the same infinite
    line" without being anywhere near each other physically.
    """
    def _norm_angle(a):
        return a % 180

    def _project_range(pts, dx, dy, ox, oy, norm):
        """Project points onto the line direction, return (min, max) scalar range."""
        vals = [((px - ox) * dx + (py - oy) * dy) / norm for px, py in pts]
        return min(vals), max(vals)

    used = [False] * len(lines)
    merged = []

    for i, l1 in enumerate(lines):
        if used[i]:
            continue
        group = [l1]
        used[i] = True
        a1 = _norm_angle(l1['angle'])
        (x1, y1), (x2, y2) = l1['endpoints']
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy) or 1
        range1 = _project_range([(x1, y1), (x2, y2)], dx, dy, x1, y1, norm)

        for j in range(i + 1, len(lines)):
            if used[j]:
                continue
            l2 = lines[j]
            a2 = _norm_angle(l2['angle'])
            angle_diff = min(abs(a1 - a2), 180 - abs(a1 - a2))
            if angle_diff > angle_tol_deg:
                continue

            mx = (l2['endpoints'][0][0] + l2['endpoints'][1][0]) / 2
            my = (l2['endpoints'][0][1] + l2['endpoints'][1][1]) / 2
            perp_dist = abs((mx - x1) * dy - (my - y1) * dx) / norm
            if perp_dist > perp_dist_tol:
                continue

            # Require the segments to actually overlap along the
            # line's own direction, not just lie near the same infinite line
            range2 = _project_range(list(l2['endpoints']), dx, dy, x1, y1, norm)
            overlap = min(range1[1], range2[1]) - max(range1[0], range2[0])
            if overlap < -10:  # allow a small gap, but not disjoint segments
                continue

            group.append(l2)
            used[j] = True

        pts = [p for g in group for p in g['endpoints']]
        max_d, best_pair = 0, (pts[0], pts[0])
        for p in range(len(pts)):
            for q in range(p + 1, len(pts)):
                d = math.hypot(pts[p][0] - pts[q][0], pts[p][1] - pts[q][1])
                if d > max_d:
                    max_d, best_pair = d, (pts[p], pts[q])

        merged.append({
            'endpoints': best_pair,
            'length': round(max_d, 1),
            'angle': group[0]['angle']
        })

    return merged

def extract_geometry(image_b64: str) -> Dict[str, Any]:
    """
    Pulls raw structural primitives from the image. Knows nothing about
    named patterns, just measures what's there.
    """

    img_bytes = base64.b64decode(image_b64)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {'line_count': 0, 'lines': []}

    edges = cv2.Canny(img, 50, 150)
    raw_lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50,
                                 minLineLength=20, maxLineGap=5)

    lines_raw = []
    if raw_lines is not None:
        # reshape(-1, 4) normalizes (N,1,4) or (N,4) to the same flat form,
        # regardless of which shape this OpenCV build returns
        for x1, y1, x2, y2 in raw_lines.reshape(-1, 4):
            length = math.hypot(int(x2) - int(x1), int(y2) - int(y1))
            angle = math.degrees(math.atan2(int(y2) - int(y1), int(x2) - int(x1)))
            if raw_lines is not None:
                lines_raw.append({
                    'endpoints': ((int(x1), int(y1)), (int(x2), int(y2))),
                    'length': round(length, 1),
                    'angle': round(angle, 1)
                })

    lines = _merge_duplicate_edges(lines_raw)
    print(f"[VISION_VERIFIER] Pre-merge: {[(l['length'], l['angle'], l['endpoints']) for l in lines_raw]}")
    print(f"[VISION_VERIFIER] Post-merge: {[(l['length'], l['angle'], l['endpoints']) for l in lines]}")

    return {'line_count': len(lines), 'lines': lines
        # room to extend generically: shape count, color regions, etc.
            }

# =========================================================================
# 2. Generic claim extraction - fixed comparative vocabulary
# =========================================================================

COMPARATIVE_PREDICATES = {
    'longer_shorter': r'\b(\w+)\s+(?:line|segment)?\s*(?:is|looks|appears)\s+(longer|shorter)\s+than\s+(?:the\s+)?(\w+)',
    'equal_length':   r'\bsame\s+length\b|\bidentical\s+(?:in\s+)?(?:size|length)\b|\bequal\s+length\b|\bequal\s+in\s+length\b',
    'diagonal':       r'\bdiagonal\b|\bconverg\w+\b|\bdiverg\w+\b|\barrowhead\w*\b|\bfins?\b|\bwings?\b',
    'parallel':       r'\bparallel\b',
    'count':          r'\b(\d+|two|three|four|five)\s+(?:lines|segments)\b',
}

LENGTH_CLAIMS = re.compile(
    r'(?:same|identical|equal|equivalent)\s+(?:in\s+)?(?:length|size)|'
    r'(?:longer|shorter|bigger|smaller)\s+than|'
    r'(?:appear|look|seem)s?\s+(?:longer|shorter|the\s+same)',
    re.I
)

COLOR_OR_POSITION = re.compile(
    r'\b(blue|red|top|bottom|upper|lower)\b.*?\b(line|segment)\b|'
    r'\b(line|segment)\b.*?\b(blue|red|top|bottom)\b',
    re.I
)

def extract_claims(response_text: str) -> Dict[str, Any]:
    """
    Pulls out geometric assertions using generic comparison/shape
    vocabulary; same handful of predicates apply whether the model is
    describing a Müller-Lyer figure, an Ebbinghaus circle set, or
    anything else with measurable geometry. No named-pattern matching.
    """
    claims = {}
    if LENGTH_CLAIMS.search(response_text):
        claims['length_relation'] = True
    # keep the existing specific patterns as secondary signals
    for predicate, pattern in COMPARATIVE_PREDICATES.items():
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            claims[predicate] = matches
    return claims

# =========================================================================
# 3. Domain-agnostic consistency check
# =========================================================================

def check_geometric_consistency(claims: Dict, geometry: Dict) -> Dict[str, Any]:
    """
    Cross-references extracted claims against measured geometry.
    Mirrors the existing entity-count-consistency logic in CAIOS.txt:
    compare claimed state to actual state, flag mismatch.
    """
    contradictions = []
    lines = geometry.get('lines', [])

    if 'diagonal' in claims and lines:
        # A genuine diagonal-arrowhead claim implies non-axis-aligned
        # angles clustered near line endpoints. Generic check: are ANY
        # detected lines meaningfully off 0°/90°?
        diagonal_present = any(
            15 < abs(l['angle']) % 90 < 75 for l in lines
        )
        if not diagonal_present:
            contradictions.append({
                'claim': 'diagonal/arrowhead/converging structure',
                'measured': f"{len(lines)} lines detected, none at diagonal angles",
                'severity': 'high'
            })

    if ('equal_length' in claims or 'length_relation' in claims) and len(lines) >= 2:
        dominant = sorted(lines, key=lambda l: l['length'], reverse=True)[:2]
        a, b = dominant[0]['length'], dominant[1]['length']
        ratio = min(a, b) / max(a, b, 1)
        if ratio < 0.70:          # clearly not equal (your image is ~0.33)
            contradictions.append({
                'claim': 'equal or similar length',
                'measured': f'longest segments {a:.0f} vs {b:.0f} (ratio {ratio:.2f})',
                'severity': 'high'
            })

    top_lines = sorted(lines, key=lambda l: -l['length'])[:4]
    geometry_summary = "; ".join(
        f"{l['length']:.0f}px @ {l['angle']:.0f}°" for l in top_lines
    ) if top_lines else "no lines detected"

    return {
        'contradiction_density': min(1.0, len(contradictions) * 0.4),
        'contradictions': contradictions,
        'claims_checked': list(claims.keys()),
        'geometry_summary': geometry_summary
    }

# =========================================================================
# Entry point
# =========================================================================

def verify_visual_claims(response_text: str, image_b64: str) -> Optional[Dict]:
    if not CV2_AVAILABLE:
        return None
    claims = extract_claims(response_text)
    print(f"[VISION_VERIFIER] Claims detected: {list(claims.keys())}")
    if not claims:
        return None
    geometry = extract_geometry(image_b64)
    print(f"[VISION_VERIFIER] Lines detected: {geometry['line_count']}, "
          f"lengths: {[l['length'] for l in geometry['lines']]}")
    return check_geometric_consistency(claims, geometry)
