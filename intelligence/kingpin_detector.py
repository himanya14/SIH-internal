import networkx as nx


# =========================================================
# KINGPIN DETECTOR
# =========================================================

def detect_kingpin(graph):
    """
    Identify the most influential person in the network.

    Uses:
        - Degree Centrality
        - Betweenness Centrality
        - PageRank

    Only PERSON nodes are considered as suspects.

    Returns:
        {
            "suspect": ...,
            "role": "Kingpin",
            "guilt_score": ...,
            "risk_level": ...,
            "metrics": {...},
            "suspects": [...]
        }
    """

    # -----------------------------------------------------
    # Find person nodes
    # -----------------------------------------------------

    persons = [
        node
        for node, data in graph.nodes(data=True)
        if data.get("type") == "person"
    ]

    if not persons:

        return {
            "suspect": None,
            "role": None,
            "guilt_score": 0,
            "risk_level": "LOW",
            "metrics": {},
            "suspects": []
        }

    # -----------------------------------------------------
    # Calculate graph metrics
    # -----------------------------------------------------

    degree_centrality = nx.degree_centrality(graph)

    betweenness_centrality = nx.betweenness_centrality(
        graph
    )

    try:

        pagerank = nx.pagerank(graph)

    except nx.PowerIterationFailedConvergence:

        pagerank = {
            node: 0
            for node in graph.nodes()
        }

    # -----------------------------------------------------
    # Normalize metrics
    # -----------------------------------------------------

    degree_scores = normalize_scores(
        degree_centrality,
        persons
    )

    betweenness_scores = normalize_scores(
        betweenness_centrality,
        persons
    )

    pagerank_scores = normalize_scores(
        pagerank,
        persons
    )

    # -----------------------------------------------------
    # Calculate combined score for every person
    # -----------------------------------------------------

    combined_scores = {}

    for person in persons:

        degree = degree_scores.get(
            person,
            0
        )

        betweenness = betweenness_scores.get(
            person,
            0
        )

        page_rank = pagerank_scores.get(
            person,
            0
        )

        score = (
            0.30 * degree
            + 0.40 * betweenness
            + 0.30 * page_rank
        )

        combined_scores[person] = round(
            score,
            2
        )

    # -----------------------------------------------------
    # Sort suspects by score
    # -----------------------------------------------------

    ranked_persons = sorted(
        persons,
        key=lambda person: combined_scores[person],
        reverse=True
    )

    # -----------------------------------------------------
    # Build suspect ranking
    # -----------------------------------------------------

    suspect_results = []

    for rank, person in enumerate(
        ranked_persons,
        start=1
    ):

        name = graph.nodes[person].get(
            "name",
            person
        )

        score = combined_scores[person]

        suspect_results.append({
            "rank": rank,
            "name": name,

            "degree_centrality": round(
                degree_centrality.get(
                    person,
                    0
                ),
                4
            ),

            "betweenness_centrality": round(
                betweenness_centrality.get(
                    person,
                    0
                ),
                4
            ),

            "pagerank": round(
                pagerank.get(
                    person,
                    0
                ),
                4
            ),

            "degree_score": degree_scores.get(
                person,
                0
            ),

            "betweenness_score": betweenness_scores.get(
                person,
                0
            ),

            "pagerank_score": pagerank_scores.get(
                person,
                0
            ),

            "combined_score": score,

            "risk_level": get_risk_level(
                score
            )
        })

    # -----------------------------------------------------
    # Top suspect
    # -----------------------------------------------------

    kingpin_node = ranked_persons[0]

    kingpin_name = graph.nodes[
        kingpin_node
    ].get(
        "name",
        kingpin_node
    )

    kingpin_score = combined_scores[
        kingpin_node
    ]

    # -----------------------------------------------------
    # Return final result
    # -----------------------------------------------------

    return {
        "suspect": kingpin_name,
        "role": "Kingpin",
        "guilt_score": kingpin_score,
        "risk_level": get_risk_level(
            kingpin_score
        ),

        "metrics": {
            "degree_centrality": round(
                degree_centrality.get(
                    kingpin_node,
                    0
                ),
                4
            ),

            "betweenness_centrality": round(
                betweenness_centrality.get(
                    kingpin_node,
                    0
                ),
                4
            ),

            "pagerank": round(
                pagerank.get(
                    kingpin_node,
                    0
                ),
                4
            )
        },

        "suspects": suspect_results
    }


# =========================================================
# NORMALIZE SCORES
# =========================================================

def normalize_scores(
    scores,
    persons
):
    """
    Convert a graph metric into a 0-100 scale.

    The highest value among PERSON nodes becomes 100.
    """

    if not persons:
        return {}

    values = [
        scores.get(
            person,
            0
        )
        for person in persons
    ]

    maximum = max(values)

    if maximum == 0:

        return {
            person: 0
            for person in persons
        }

    return {
        person: round(
            (
                scores.get(
                    person,
                    0
                )
                / maximum
            ) * 100,
            2
        )
        for person in persons
    }


# =========================================================
# RISK LEVEL
# =========================================================

def get_risk_level(score):

    if score >= 80:
        return "Critical"

    elif score >= 60:
        return "High"

    elif score >= 40:
        return "Medium"

    else:
        return "Low"