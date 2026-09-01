import re
from collections import Counter, defaultdict
from datetime import datetime

'''
50+ calls → CRITICAL
10–49 calls → HIGH
3–9 late-night calls → HIGH
₹10 lakh+ → CRITICAL
₹5 lakh+ → HIGH
₹1 lakh+ → MEDIUM
'''

# ALERT DETECTOR

def detect_alerts(
    data,
    syndicates=None,
    thresholds=None
):
    """
    Detect suspicious patterns from intelligence data.

    Parameters
    ----------
    data:
        Can contain:
            - relationships
            - entities
            - transactions
            - calls
            - records

    syndicates:
        Optional community-detection output.

    thresholds:
        Optional custom thresholds.

    Returns
    -------
    list of alert dictionaries
    """

    if data is None:
        data = {}

    if thresholds is None:
        thresholds = {}

    alerts = []

    relationships = data.get(
        "relationships",
        []
    )

    transactions = data.get(
        "transactions",
        []
    )

    calls = data.get(
        "calls",
        []
    )

    # -----------------------------------------------------
    # If separate calls/transactions are not supplied,
    # try to derive them from relationships.
    # -----------------------------------------------------

    if not calls:

        calls = [
            relationship
            for relationship in relationships
            if relationship.get("relationship") in {
                "CALLED",
                "CONTACTED"
            }
        ]

    if not transactions:

        transactions = [
            relationship
            for relationship in relationships
            if relationship.get("relationship")
            == "TRANSFERRED_MONEY_TO"
        ]

    # -----------------------------------------------------
    # 1. Communication spike
    # -----------------------------------------------------

    alerts.extend(
        detect_communication_spikes(
            calls,
            threshold=thresholds.get(
                "communication_spike",
                10
            )
        )
    )

    # -----------------------------------------------------
    # 2. Late-night communication
    # -----------------------------------------------------

    alerts.extend(
        detect_late_night_communication(
            calls,
            threshold=thresholds.get(
                "late_night_calls",
                3
            )
        )
    )

    # -----------------------------------------------------
    # 3. Suspicious financial transactions
    # -----------------------------------------------------

    alerts.extend(
        detect_large_transactions(
            transactions,
            threshold=thresholds.get(
                "large_transaction",
                100000
            )
        )
    )

    # -----------------------------------------------------
    # 4. Circular money transfers
    # -----------------------------------------------------

    alerts.extend(
        detect_circular_transactions(
            transactions
        )
    )

    # -----------------------------------------------------
    # 5. Shared entities
    # -----------------------------------------------------

    alerts.extend(
        detect_shared_resources(
            relationships,
            threshold=thresholds.get(
                "shared_resource",
                2
            )
        )
    )

    # -----------------------------------------------------
    # 6. Cross-syndicate connections
    # -----------------------------------------------------

    if syndicates:

        alerts.extend(
            detect_cross_syndicate_connections(
                relationships,
                syndicates
            )
        )

    # -----------------------------------------------------
    # Remove duplicates
    # -----------------------------------------------------

    alerts = deduplicate_alerts(
        alerts
    )

    # -----------------------------------------------------
    # Sort by severity
    # -----------------------------------------------------

    severity_order = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    alerts.sort(
        key=lambda alert: (
            severity_order.get(
                alert.get("severity"),
                99
            ),
            alert.get("type", "")
        )
    )

    # -----------------------------------------------------
    # Add alert IDs
    # -----------------------------------------------------

    for index, alert in enumerate(
        alerts,
        start=1
    ):

        alert["id"] = (
            f"ALERT_{index:03d}"
        )

    return alerts


# =========================================================
# COMMUNICATION SPIKES
# =========================================================

def detect_communication_spikes(
    calls,
    threshold=10
):
    """
    Detect unusually high numbers of calls
    between the same pair of people.

    Example:

        47 calls between Ravi and Amit
        within 24 hours.

    """

    pair_counts = Counter()

    pair_records = defaultdict(list)

    for call in calls:

        source = call.get("source")
        target = call.get("target")

        if not source or not target:
            continue

        pair = tuple(
            sorted(
                [source, target]
            )
        )

        pair_counts[pair] += 1

        pair_records[pair].append(
            call
        )

    alerts = []

    for pair, count in pair_counts.items():

        if count < threshold:
            continue

        source, target = pair

        alerts.append({
            "severity": (
                "CRITICAL"
                if count >= threshold * 5
                else "HIGH"
            ),
            "type": "COMMUNICATION_SPIKE",
            "message": (
                f"{count} calls detected between "
                f"{source} and {target}."
            ),
            "entities": [
                source,
                target
            ],
            "count": count,
            "confidence": min(
                0.99,
                0.70 + (
                    count / (
                        threshold * 10
                    )
                )
            ),
            "evidence": pair_records[pair]
        })

    return alerts


# =========================================================
# LATE-NIGHT COMMUNICATION
# =========================================================

def detect_late_night_communication(
    calls,
    threshold=3
):
    """
    Detect repeated communication during
    late-night hours.

    Late night = 00:00 - 05:00.
    """

    pair_counts = Counter()

    pair_records = defaultdict(list)

    for call in calls:

        timestamp = (
            call.get("timestamp")
            or call.get("datetime")
            or call.get("date_time")
        )

        if not timestamp:
            continue

        hour = extract_hour(
            timestamp
        )

        if hour is None:
            continue

        if 0 <= hour < 5:

            source = call.get("source")
            target = call.get("target")

            if not source or not target:
                continue

            pair = tuple(
                sorted(
                    [source, target]
                )
            )

            pair_counts[pair] += 1

            pair_records[pair].append(
                call
            )

    alerts = []

    for pair, count in pair_counts.items():

        if count < threshold:
            continue

        source, target = pair

        alerts.append({
            "severity": "HIGH",
            "type": "LATE_NIGHT_COMMUNICATION",
            "message": (
                f"{count} late-night communications "
                f"detected between {source} and {target}."
            ),
            "entities": [
                source,
                target
            ],
            "count": count,
            "confidence": min(
                0.95,
                0.65 + count * 0.05
            ),
            "evidence": pair_records[pair]
        })

    return alerts


# =========================================================
# LARGE TRANSACTIONS
# =========================================================

def detect_large_transactions(
    transactions,
    threshold=100000
):
    """
    Detect unusually large financial transactions.
    """

    alerts = []

    for transaction in transactions:

        amount = extract_amount(
            transaction
        )

        if amount is None:
            continue

        if amount < threshold:
            continue

        source = transaction.get(
            "source",
            "Unknown"
        )

        target = transaction.get(
            "target",
            "Unknown"
        )

        if amount >= threshold * 10:

            severity = "CRITICAL"

        elif amount >= threshold * 5:

            severity = "HIGH"

        else:

            severity = "MEDIUM"

        alerts.append({
            "severity": severity,
            "type": "LARGE_TRANSACTION",
            "message": (
                f"Large transaction of "
                f"₹{amount:,.0f} detected from "
                f"{source} to {target}."
            ),
            "entities": [
                source,
                target
            ],
            "amount": amount,
            "confidence": min(
                0.99,
                0.70 + (
                    amount / (
                        threshold * 20
                    )
                )
            ),
            "evidence": [
                transaction
            ]
        })

    return alerts


# =========================================================
# CIRCULAR TRANSACTIONS
# =========================================================

def detect_circular_transactions(
    transactions
):
    """
    Detect simple circular money-transfer patterns.

    Example:

        Ravi -> Amit
        Amit -> Raj
        Raj -> Ravi
    """

    transfer_graph = defaultdict(set)

    transfer_records = defaultdict(list)

    for transaction in transactions:

        source = transaction.get(
            "source"
        )

        target = transaction.get(
            "target"
        )

        if not source or not target:
            continue

        transfer_graph[
            source
        ].add(target)

        transfer_records[
            (source, target)
        ].append(transaction)

    alerts = []

    # -----------------------------------------------------
    # Search for 3-person cycles
    # -----------------------------------------------------

    for first in transfer_graph:

        for second in transfer_graph[first]:

            if second == first:
                continue

            if second not in transfer_graph:
                continue

            for third in transfer_graph[second]:

                if third in {
                    first,
                    second
                }:
                    continue

                if (
                    first
                    in transfer_graph.get(
                        third,
                        set()
                    )
                ):

                    alerts.append({
                        "severity": "HIGH",
                        "type": "CIRCULAR_TRANSACTION",
                        "message": (
                            "Circular financial flow detected: "
                            f"{first} → {second} → "
                            f"{third} → {first}."
                        ),
                        "entities": [
                            first,
                            second,
                            third
                        ],
                        "confidence": 0.90,
                        "evidence": (
                            transfer_records.get(
                                (first, second),
                                []
                            )
                            +
                            transfer_records.get(
                                (second, third),
                                []
                            )
                            +
                            transfer_records.get(
                                (third, first),
                                []
                            )
                        )
                    })

    return alerts


# =========================================================
# SHARED RESOURCES
# =========================================================

def detect_shared_resources(
    relationships,
    threshold=2
):
    """
    Detect multiple people connected to the same:

        phone
        vehicle
        location
        bank account
    """

    resource_types = {
        "USED_PHONE": "phone",
        "USED_VEHICLE": "vehicle",
        "OWNS": "vehicle",
        "ASSOCIATED_WITH_LOCATION": "location",
        "VISITED": "location",
        "USED_ACCOUNT": "bank_account"
    }

    resource_people = defaultdict(set)

    resource_records = defaultdict(list)

    for relationship in relationships:

        relationship_type = relationship.get(
            "relationship"
        )

        resource_type = resource_types.get(
            relationship_type
        )

        if not resource_type:
            continue

        source = relationship.get(
            "source"
        )

        target = relationship.get(
            "target"
        )

        if not source or not target:
            continue

        key = (
            resource_type,
            target
        )

        resource_people[key].add(
            source
        )

        resource_records[key].append(
            relationship
        )

    alerts = []

    for (
        resource_type,
        resource
    ), people in resource_people.items():

        if len(people) < threshold:
            continue

        people = sorted(
            people
        )

        alerts.append({
            "severity": "HIGH",
            "type": "SHARED_RESOURCE",
            "message": (
                f"{len(people)} people are connected "
                f"to the same {resource_type}: "
                f"{resource}."
            ),
            "entities": (
                people
                + [resource]
            ),
            "resource_type": resource_type,
            "resource": resource,
            "people": people,
            "confidence": min(
                0.95,
                0.70 + (
                    len(people) * 0.05
                )
            ),
            "evidence": resource_records[
                (
                    resource_type,
                    resource
                )
            ]
        })

    return alerts


# =========================================================
# CROSS-SYNDICATE CONNECTION
# =========================================================

def detect_cross_syndicate_connections(
    relationships,
    syndicates
):
    """
    Detect people who connect two different
    detected syndicates.

    This can identify potential bridge individuals.
    """

    assignments = syndicates.get(
        "assignments",
        {}
    )

    alerts = []

    seen = set()

    for relationship in relationships:

        source = relationship.get(
            "source"
        )

        target = relationship.get(
            "target"
        )

        if not source or not target:
            continue

        source_group = assignments.get(
            source
        )

        target_group = assignments.get(
            target
        )

        if not source_group or not target_group:
            continue

        if source_group == target_group:
            continue

        pair = tuple(
            sorted(
                [source, target]
            )
        )

        if pair in seen:
            continue

        seen.add(pair)

        alerts.append({
            "severity": "HIGH",
            "type": "CROSS_SYNDICATE_CONNECTION",
            "message": (
                f"Connection detected between "
                f"{source} ({source_group}) and "
                f"{target} ({target_group})."
            ),
            "entities": [
                source,
                target
            ],
            "syndicates": [
                source_group,
                target_group
            ],
            "relationship": relationship.get(
                "relationship",
                "CONNECTED"
            ),
            "confidence": relationship.get(
                "confidence",
                0.80
            ),
            "evidence": [
                relationship
            ]
        })

    return alerts


# =========================================================
# HELPERS
# =========================================================

def extract_hour(timestamp):
    """
    Extract hour from common timestamp formats.
    """

    if isinstance(
        timestamp,
        datetime
    ):

        return timestamp.hour

    if not isinstance(
        timestamp,
        str
    ):

        return None

    # ISO timestamp

    try:

        parsed = datetime.fromisoformat(
            timestamp.replace(
                "Z",
                "+00:00"
            )
        )

        return parsed.hour

    except ValueError:

        pass

    # Try HH:MM

    match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        timestamp
    )

    if match:

        return int(
            match.group(1)
        )

    return None


def extract_amount(record):
    """
    Extract transaction amount from
    structured or textual data.
    """

    amount = record.get(
        "amount"
    )

    if isinstance(
        amount,
        (int, float)
    ):

        return float(amount)

    text = record.get(
        "evidence",
        ""
    )

    if not text:
        text = record.get(
            "message",
            ""
        )

    if not text:
        return None

    # Remove commas

    text = text.replace(
        ",",
        ""
    )

    # ₹50000
    match = re.search(
        r"₹\s*(\d+(?:\.\d+)?)",
        text
    )

    if match:

        return float(
            match.group(1)
        )

    # Rs 50000 / INR 50000

    match = re.search(
        r"(?:Rs\.?|INR)\s*(\d+(?:\.\d+)?)",
        text,
        re.IGNORECASE
    )

    if match:

        return float(
            match.group(1)
        )

    return None


# =========================================================
# DEDUPLICATION
# =========================================================

def deduplicate_alerts(
    alerts
):
    """
    Remove duplicate alerts while preserving
    meaningful distinct alerts.
    """

    unique = []
    seen = set()

    for alert in alerts:

        key = (
            alert.get("type"),
            tuple(
                sorted(
                    alert.get(
                        "entities",
                        []
                    )
                )
            )
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            alert
        )

    return unique