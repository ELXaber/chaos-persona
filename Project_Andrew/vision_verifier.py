#V08252026
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

    lines = []
    if raw_lines is not None:
        # reshape(-1, 4) normalizes (N,1,4) or (N,4) to the same flat form,
        # regardless of which shape this OpenCV build returns
        for x1, y1, x2, y2 in raw_lines.reshape(-1, 4):
            length = math.hypot(int(x2) - int(x1), int(y2) - int(y1))
            angle = math.degrees(math.atan2(int(y2) - int(y1), int(x2) - int(x1)))
            lines.append({
                'endpoints': ((int(x1), int(y1)), (int(x2), int(y2))),
                'length': round(length, 1),
                'angle': round(angle, 1)
            })

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

def extract_claims(response_text: str) -> Dict[str, List]:
    """
    Pulls out geometric assertions using generic comparison/shape
    vocabulary; same handful of predicates apply whether the model is
    describing a Müller-Lyer figure, an Ebbinghaus circle set, or
    anything else with measurable geometry. No named-pattern matching.
    """
    claims = {}
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

    if 'equal_length' in claims and len(lines) >= 2:
        dominant = sorted(lines, key=lambda l: l['length'], reverse=True)[:2]
        a, b = dominant[0]['length'], dominant[1]['length']
        spread = abs(a - b) / max(a, b, 1)
        if spread > 0.15:
            contradictions.append({
                'claim': 'equal length',
                'measured': f"two longest segments differ by {spread:.0%} ({a} vs {b})",
                'severity': 'medium'
            })

    return {
        'contradiction_density': min(1.0, len(contradictions) * 0.4),
        'contradictions': contradictions,
        'claims_checked': list(claims.keys())
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
