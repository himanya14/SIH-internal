import networkx as nx


# =========================================================
# BUILD GRAPH
# =========================================================

def build_graph(entities, relationships):
    """
    Build a NetworkX graph from extracted entities
    and relationships.

    Returns:
        NetworkX MultiDiGraph
    """

    graph = nx.MultiDiGraph()

    # -----------------------------------------------------
    # Add entity nodes
    # -----------------------------------------------------

    entity_type_mapping = {
        "persons": "person",
        "phones": "phone",
        "vehicles": "vehicle",
        "locations": "location",
        "organisations": "organisation",
        "bank_accounts": "bank_account",
        "dates_times": "date_time"
    }

    for category, node_type in entity_type_mapping.items():

        for entity in entities.get(category, []):

            node_id = create_node_id(
                node_type,
                entity
            )

            graph.add_node(
                node_id,
                name=entity,
                type=node_type
            )

    # -----------------------------------------------------
    # Add relationship edges
    # -----------------------------------------------------

    for relationship in relationships:

        source = relationship["source"]
        target = relationship["target"]

        source_id = find_node_id(
            graph,
            source
        )

        target_id = find_node_id(
            graph,
            target
        )

        # If an entity wasn't present in the entity list,
        # create it dynamically.
        if source_id is None:

            source_id = create_node_id(
                "unknown",
                source
            )

            graph.add_node(
                source_id,
                name=source,
                type="unknown"
            )

        if target_id is None:

            target_id = create_node_id(
                "unknown",
                target
            )

            graph.add_node(
                target_id,
                name=target,
                type="unknown"
            )

        # -------------------------------------------------
        # Add edge
        # -------------------------------------------------

        graph.add_edge(
            source_id,
            target_id,
            relationship=relationship["relationship"],
            confidence=relationship.get(
                "confidence",
                1.0
            ),
            evidence=relationship.get(
                "evidence",
                ""
            ),
            source_type=relationship.get(
                "source_type",
                "UNKNOWN"
            ),
            weight=1
        )

    return graph


# =========================================================
# CREATE NODE ID
# =========================================================

def create_node_id(
    node_type,
    entity
):
    """
    Creates a stable ID for a graph node.

    Example:
        person + Ravi Kumar
        -> PERSON_RAVI_KUMAR
    """

    normalized = entity.strip().upper()

    normalized = normalized.replace(
        " ",
        "_"
    )

    return f"{node_type.upper()}_{normalized}"


# =========================================================
# FIND NODE
# =========================================================

def find_node_id(
    graph,
    entity_name
):
    """
    Find an existing node using its entity name.
    """

    normalized = entity_name.strip().lower()

    for node_id, data in graph.nodes(
        data=True
    ):

        if data.get(
            "name",
            ""
        ).strip().lower() == normalized:

            return node_id

    return None


# =========================================================
# EXPORT GRAPH
# =========================================================

def graph_to_json(graph):
    """
    Convert NetworkX graph into the JSON structure
    expected by the frontend.
    """

    nodes = []

    edges = []

    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------

    for node_id, data in graph.nodes(
        data=True
    ):

        nodes.append({
            "id": node_id,
            "name": data.get(
                "name",
                ""
            ),
            "type": data.get(
                "type",
                "unknown"
            )
        })

    # -----------------------------------------------------
    # Edges
    # -----------------------------------------------------

    for source, target, data in graph.edges(
        data=True
    ):

        edges.append({
            "source": source,
            "target": target,
            "relationship": data.get(
                "relationship",
                "UNKNOWN"
            ),
            "weight": data.get(
                "weight",
                1
            ),
            "confidence": data.get(
                "confidence",
                1.0
            ),
            "evidence": data.get(
                "evidence",
                ""
            ),
            "source_type": data.get(
                "source_type",
                "UNKNOWN"
            )
        })

    return {
        "nodes": nodes,
        "edges": edges
    }


# =========================================================
# COMPLETE GRAPH PIPELINE
# =========================================================

def build_graph_data(
    entities,
    relationships
):
    """
    Convenience function.

    Takes extracted entities and relationships
    and directly returns frontend-ready graph data.
    """

    graph = build_graph(
        entities,
        relationships
    )

    return graph_to_json(graph)