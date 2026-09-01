import sys
from pathlib import Path
from typing import Any, Dict


# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INTELLIGENCE_DIR = (
    PROJECT_ROOT
    / "intelligence"
)

if not INTELLIGENCE_DIR.exists():

    raise RuntimeError(
        f"Intelligence folder not found: {INTELLIGENCE_DIR}"
    )


if str(INTELLIGENCE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(INTELLIGENCE_DIR)
    )


# =========================================================
# IMPORT AI PIPELINE
# =========================================================

from main import analyze_case


# =========================================================
# RUN CASE ANALYSIS
# =========================================================

def run_case_analysis(
    text: str,
    source_type: str = "FIR"
) -> Dict[str, Any]:
    """
    Send case text to the intelligence pipeline
    and normalize the response for the backend.

    The returned investigation priority and
    network influence values are analytical
    indicators only.
    """

    if not text or not text.strip():

        raise ValueError(
            "Case text cannot be empty"
        )


    result = analyze_case(
        text=text,
        source_type=source_type
    )


    if not isinstance(
        result,
        dict
    ):

        raise RuntimeError(
            "Intelligence pipeline returned an invalid response"
        )


    # =====================================================
    # NORMALIZED BACKEND RESPONSE
    # =====================================================

    return {

        "entities": result.get(
            "entities",
            {}
        ),

        "relationships": result.get(
            "relationships",
            []
        ),

        "nodes": result.get(
            "nodes",
            []
        ),

        "edges": result.get(
            "edges",
            []
        ),

        "network_influence": result.get(
            "kingpin"
        ),

        "investigation_priorities": result.get(
            "investigation_priorities",
            []
        ),

        "syndicates": result.get(
            "syndicates",
            []
        ),

        "assignments": result.get(
            "assignments",
            {}
        ),

        "alerts": result.get(
            "alerts",
            []
        ),

        "insights": result.get(
            "insights",
            {}
        )
    }