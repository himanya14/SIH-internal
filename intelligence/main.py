# =========================================================
# PERSON 3 - MASTER INTELLIGENCE PIPELINE
# =========================================================
#
# Python version: 3.10+
#
# Complete pipeline:
#
# Raw text
#     ↓
# Entity Extraction
#     ↓
# Relationship Extraction
#     ↓
# Graph Construction
#     ↓
# Kingpin Detection
#     ↓
# Guilt / Risk Scoring
#     ↓
# Community / Syndicate Detection
#     ↓
# Alert Detection
#     ↓
# Intelligence Insights
#
# =========================================================


from entity_extractor import extract_entities
from relation_extractor import extract_relationships

from graph_builder import (
    build_graph,
    graph_to_json
)

from kingpin_detector import (
    detect_kingpin
)

from guilt_score import (
    calculate_guilt_score
)

from community_detector import (
    detect_communities
)

from alert_detector import (
    detect_alerts
)

from insights_generator import (
    generate_insights
)


# =========================================================
# ANALYZE CASE
# =========================================================

def analyze_case(
    text,
    source_type="FIR"
):
    """
    Run the complete Person 3 intelligence pipeline.

    Parameters
    ----------
    text : str
        Raw FIR/report/CDR/transaction text.

    source_type : str
        Source of the information.
        Default is FIR.

    Returns
    -------
    dict
        Complete intelligence result.
    """

    # =====================================================
    # STEP 1 - ENTITY EXTRACTION
    # =====================================================

    entities = extract_entities(
        text
    )

    # =====================================================
    # STEP 2 - RELATIONSHIP EXTRACTION
    # =====================================================

    # IMPORTANT:
    # extract_relationships() requires both
    # text AND entities.

    relationships = extract_relationships(
        text,
        entities
    )

    # Make sure source type exists.

    for relationship in relationships:

        if not relationship.get(
            "source_type"
        ):

            relationship[
                "source_type"
            ] = source_type

    # =====================================================
    # STEP 3 - GRAPH CONSTRUCTION
    # =====================================================

    graph = build_graph(
        entities,
        relationships
    )

    graph_data = graph_to_json(
        graph
    )

    # =====================================================
    # STEP 4 - KINGPIN DETECTION
    # =====================================================

    kingpin_result = detect_kingpin(
        graph
    )

    # =====================================================
    # STEP 5 - GUILT / RISK SCORING
    # =====================================================

    guilt_scores = []

    # Get only PERSON nodes.

    person_nodes = [

        node

        for node, data in graph.nodes(
            data=True
        )

        if data.get(
            "type"
        ) == "person"
    ]

    # Calculate score for every suspect.

    for person_node in person_nodes:

        suspect_name = graph.nodes[
            person_node
        ].get(
            "name",
            person_node
        )

        score = calculate_guilt_score(
            suspect_name,
            graph,
            kingpin_result
        )

        guilt_scores.append(
            score
        )

    # =====================================================
    # STEP 6 - COMMUNITY / SYNDICATE DETECTION
    # =====================================================

    community_result = detect_communities(
        graph
    )

    syndicates = community_result.get(
        "syndicates",
        []
    )

    assignments = community_result.get(
        "assignments",
        {}
    )

    # =====================================================
    # STEP 7 - ALERT DETECTION
    # =====================================================

    alert_input = {

        "entities": entities,

        "relationships": relationships,

        "graph": graph,

        "graph_data": graph_data,

        "syndicates": syndicates,

        "assignments": assignments
    }

    # IMPORTANT:
    #
    # alert_detector.py expects the COMPLETE
    # community result dictionary here.
    #
    # Do NOT pass:
    #
    #     syndicates=syndicates
    #
    # because syndicates is only a list.
    #
    # Pass:
    #
    #     community_result
    #
    # which contains both syndicates and assignments.

    alerts = detect_alerts(
        alert_input,
        syndicates=community_result
    )

    # =====================================================
    # STEP 8 - INTELLIGENCE INSIGHTS
    # =====================================================

    insight_input = {

        "entities": entities,

        "relationships": relationships,

        "nodes": graph_data.get(
            "nodes",
            []
        ),

        "edges": graph_data.get(
            "edges",
            []
        ),

        "kingpin": kingpin_result,

        "guilt_scores": guilt_scores,

        "syndicates": syndicates,

        "assignments": assignments,

        "alerts": alerts
    }

    insights = generate_insights(
        insight_input
    )

    # =====================================================
    # STEP 9 - FINAL OUTPUT
    # =====================================================

    result = {

        "entities": entities,

        "relationships": relationships,

        "nodes": graph_data.get(
            "nodes",
            []
        ),

        "edges": graph_data.get(
            "edges",
            []
        ),

        "kingpin": kingpin_result,

        "guilt_scores": guilt_scores,

        "syndicates": syndicates,

        "assignments": assignments,

        "alerts": alerts,

        "insights": insights
    }

    return result


# =========================================================
# TEST PIPELINE
# =========================================================

if __name__ == "__main__":

    sample_text = """

    Ravi Kumar contacted Amit Sharma.

    Ravi Kumar called Amit Sharma using 9876543210.

    Amit Sharma was using vehicle PB10AB1234.

    Ravi Kumar transferred ₹50000 to Amit Sharma.

    Ravi Kumar was seen near Sector 21.

    Amit Sharma met Raj Malhotra.

    Raj Malhotra visited Sector 21.

    """

    print()
    print("=" * 70)
    print("PERSON 3 - COMPLETE INTELLIGENCE PIPELINE")
    print("=" * 70)

    # =====================================================
    # RUN PIPELINE
    # =====================================================

    result = analyze_case(
        sample_text,
        source_type="FIR"
    )

    # =====================================================
    # ENTITIES
    # =====================================================

    print()
    print("ENTITIES:")

    print(
        result["entities"]
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    print()
    print("RELATIONSHIPS:")

    for relationship in result[
        "relationships"
    ]:

        print(
            relationship
        )

    # =====================================================
    # GRAPH
    # =====================================================

    print()
    print("GRAPH:")

    print(
        "Nodes:",
        len(
            result["nodes"]
        )
    )

    print(
        "Edges:",
        len(
            result["edges"]
        )
    )

    # =====================================================
    # KINGPIN
    # =====================================================

    print()
    print("KINGPIN:")

    print(
        result["kingpin"]
    )

    # =====================================================
    # GUILT SCORES
    # =====================================================

    print()
    print("GUILT / RISK SCORES:")

    for score in result[
        "guilt_scores"
    ]:

        print(
            score
        )

    # =====================================================
    # SYNDICATES
    # =====================================================

    print()
    print("SYNDICATES:")

    for syndicate in result[
        "syndicates"
    ]:

        print(
            syndicate
        )

    # =====================================================
    # ASSIGNMENTS
    # =====================================================

    print()
    print("SYNDICATE ASSIGNMENTS:")

    for person, syndicate in result[
        "assignments"
    ].items():

        print(
            person,
            "->",
            syndicate
        )

    # =====================================================
    # ALERTS
    # =====================================================

    print()
    print("ALERTS:")

    for alert in result[
        "alerts"
    ]:

        print(
            alert
        )

    # =====================================================
    # INSIGHTS
    # =====================================================

    print()
    print("GENERATED INTELLIGENCE:")

    print(
        result["insights"]
    )

    # =====================================================
    # COMPLETE
    # =====================================================

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)