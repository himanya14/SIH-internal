# =========================================================
# INSIGHTS GENERATOR
# =========================================================
#
# Converts the results of the intelligence modules into
# structured investigative insights.
#
# This module summarizes analytical findings.
# It does NOT make a legal determination of guilt.
# =========================================================


def generate_insights(case_data):
    """
    Generate structured intelligence insights.

    Expected input:

        {
            "entities": {...},
            "relationships": [...],
            "nodes": [...],
            "edges": [...],
            "kingpin": {...},
            "guilt_scores": [...],
            "syndicates": [...],
            "alerts": [...]
        }

    Returns:

        {
            "primary_suspect": {...},
            "network_summary": {...},
            "evidence": [...],
            "key_findings": [...],
            "risk_summary": {...},
            "chargesheet_evidence": [...]
        }
    """

    if case_data is None:
        case_data = {}

    entities = case_data.get("entities", {})
    relationships = case_data.get("relationships", [])
    syndicates = case_data.get("syndicates", [])
    alerts = case_data.get("alerts", [])
    guilt_scores = case_data.get("guilt_scores", [])
    kingpin = case_data.get("kingpin", {})

    # -----------------------------------------------------
    # PRIMARY SUSPECT
    # -----------------------------------------------------

    primary_suspect = build_primary_suspect(
        kingpin,
        guilt_scores
    )

    # -----------------------------------------------------
    # NETWORK SUMMARY
    # -----------------------------------------------------

    network_summary = build_network_summary(
        entities,
        relationships,
        syndicates,
        alerts
    )

    # -----------------------------------------------------
    # EVIDENCE
    # -----------------------------------------------------

    evidence = extract_evidence(
        relationships,
        alerts
    )

    # -----------------------------------------------------
    # KEY FINDINGS
    # -----------------------------------------------------

    key_findings = generate_key_findings(
        primary_suspect,
        network_summary,
        alerts,
        syndicates
    )

    # -----------------------------------------------------
    # RISK SUMMARY
    # -----------------------------------------------------

    risk_summary = build_risk_summary(
        guilt_scores
    )

    # -----------------------------------------------------
    # CHARGESHEET EVIDENCE
    # -----------------------------------------------------

    chargesheet_evidence = build_chargesheet_evidence(
        primary_suspect,
        relationships,
        alerts,
        syndicates
    )

    return {
        "primary_suspect": primary_suspect,
        "network_summary": network_summary,
        "evidence": evidence,
        "key_findings": key_findings,
        "risk_summary": risk_summary,
        "chargesheet_evidence": chargesheet_evidence
    }


# =========================================================
# PRIMARY SUSPECT
# =========================================================

def build_primary_suspect(kingpin, guilt_scores):
    """
    Determine the primary suspect.

    First preference:
        Kingpin detector result.

    Fallback:
        Highest guilt score.
    """

    if kingpin:

        suspect = kingpin.get("suspect")

        if suspect:

            return {
                "name": suspect,
                "role": kingpin.get(
                    "role",
                    "High Influence"
                ),
                "guilt_score": kingpin.get(
                    "guilt_score",
                    0
                ),
                "risk_level": kingpin.get(
                    "risk_level",
                    "Unknown"
                )
            }

    # -----------------------------------------------------
    # FALLBACK TO HIGHEST GUILT SCORE
    # -----------------------------------------------------

    if guilt_scores:

        sorted_scores = sorted(
            guilt_scores,
            key=lambda item: item.get(
                "guilt_score",
                0
            ),
            reverse=True
        )

        top = sorted_scores[0]

        return {
            "name": top.get(
                "suspect",
                "Unknown"
            ),
            "role": "Primary Suspect",
            "guilt_score": top.get(
                "guilt_score",
                0
            ),
            "risk_level": top.get(
                "risk_level",
                "Unknown"
            )
        }

    return {
        "name": "Unknown",
        "role": "Unknown",
        "guilt_score": 0,
        "risk_level": "Unknown"
    }


# =========================================================
# NETWORK SUMMARY
# =========================================================

def build_network_summary(
    entities,
    relationships,
    syndicates,
    alerts
):
    """
    Create a summary of the investigated network.
    """

    persons = entities.get(
        "persons",
        []
    )

    phones = entities.get(
        "phones",
        []
    )

    vehicles = entities.get(
        "vehicles",
        []
    )

    locations = entities.get(
        "locations",
        []
    )

    organisations = entities.get(
        "organisations",
        []
    )

    bank_accounts = entities.get(
        "bank_accounts",
        []
    )

    dates_times = entities.get(
        "dates_times",
        []
    )

    return {
        "persons": len(persons),
        "phones": len(phones),
        "vehicles": len(vehicles),
        "locations": len(locations),
        "organisations": len(organisations),
        "bank_accounts": len(bank_accounts),
        "dates_times": len(dates_times),
        "relationships": len(relationships),
        "syndicates": get_syndicate_count(
            syndicates
        ),
        "alerts": len(alerts)
    }


# =========================================================
# EVIDENCE EXTRACTION
# =========================================================

def extract_evidence(
    relationships,
    alerts
):
    """
    Collect evidence from relationships and alerts.

    Duplicate evidence is removed.
    """

    evidence = []

    seen = set()

    # -----------------------------------------------------
    # RELATIONSHIP EVIDENCE
    # -----------------------------------------------------

    for relationship in relationships:

        text = relationship.get(
            "evidence",
            ""
        )

        if not text:
            continue

        key = (
            "relationship",
            text
        )

        if key in seen:
            continue

        seen.add(key)

        evidence.append({
            "type": "RELATIONSHIP",
            "relationship": relationship.get(
                "relationship",
                "UNKNOWN"
            ),
            "source": relationship.get(
                "source",
                ""
            ),
            "target": relationship.get(
                "target",
                ""
            ),
            "confidence": relationship.get(
                "confidence",
                1.0
            ),
            "text": text
        })

    # -----------------------------------------------------
    # ALERT EVIDENCE
    # -----------------------------------------------------

    for alert in alerts:

        message = alert.get(
            "message",
            ""
        )

        if not message:
            continue

        key = (
            "alert",
            alert.get(
                "type",
                "UNKNOWN"
            ),
            message
        )

        if key in seen:
            continue

        seen.add(key)

        evidence.append({
            "type": "ALERT",
            "alert_type": alert.get(
                "type",
                "UNKNOWN"
            ),
            "severity": alert.get(
                "severity",
                "UNKNOWN"
            ),
            "confidence": alert.get(
                "confidence",
                0
            ),
            "text": message
        })

    return evidence


# =========================================================
# KEY FINDINGS
# =========================================================

def generate_key_findings(
    primary_suspect,
    network_summary,
    alerts,
    syndicates
):
    """
    Generate concise findings suitable for a dashboard.
    """

    findings = []

    suspect = primary_suspect.get(
        "name"
    )

    # -----------------------------------------------------
    # PRIMARY SUSPECT
    # -----------------------------------------------------

    if suspect and suspect != "Unknown":

        finding = (
            suspect
            + " has the highest network influence "
            + "among the analysed suspects."
        )

        findings.append(finding)

    # -----------------------------------------------------
    # SYNDICATES
    # -----------------------------------------------------

    syndicate_count = network_summary.get(
        "syndicates",
        0
    )

    if syndicate_count > 0:

        finding = (
            str(syndicate_count)
            + " potential criminal network group(s) "
            + "were identified."
        )

        findings.append(finding)

    # -----------------------------------------------------
    # CRITICAL ALERTS
    # -----------------------------------------------------

    critical_count = count_alerts_by_severity(
        alerts,
        "CRITICAL"
    )

    if critical_count > 0:

        finding = (
            str(critical_count)
            + " critical suspicious activity "
            + "alert(s) were detected."
        )

        findings.append(finding)

    # -----------------------------------------------------
    # HIGH ALERTS
    # -----------------------------------------------------

    high_count = count_alerts_by_severity(
        alerts,
        "HIGH"
    )

    if high_count > 0:

        finding = (
            str(high_count)
            + " high-severity suspicious activity "
            + "alert(s) were detected."
        )

        findings.append(finding)

    # -----------------------------------------------------
    # NETWORK SIZE
    # -----------------------------------------------------

    persons = network_summary.get(
        "persons",
        0
    )

    relationships = network_summary.get(
        "relationships",
        0
    )

    if persons > 0 and relationships > 0:

        finding = (
            "The analysed network contains "
            + str(persons)
            + " identified person(s) and "
            + str(relationships)
            + " recorded relationship(s)."
        )

        findings.append(finding)

    return findings


# =========================================================
# RISK SUMMARY
# =========================================================

def build_risk_summary(guilt_scores):
    """
    Summarize suspects according to risk level.
    """

    summary = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "Unknown": 0
    }

    highest_risk = None
    highest_score = -1

    for suspect in guilt_scores:

        risk = suspect.get(
            "risk_level",
            "Unknown"
        )

        if risk not in summary:
            risk = "Unknown"

        summary[risk] += 1

        score = suspect.get(
            "guilt_score",
            0
        )

        if score > highest_score:

            highest_score = score

            highest_risk = {
                "suspect": suspect.get(
                    "suspect",
                    "Unknown"
                ),
                "guilt_score": score,
                "risk_level": risk
            }

    return {
        "counts": summary,
        "highest_risk": highest_risk
    }


# =========================================================
# CHARGESHEET EVIDENCE
# =========================================================

def build_chargesheet_evidence(
    primary_suspect,
    relationships,
    alerts,
    syndicates
):
    """
    Generate structured evidence points for Person 2.

    These are analytical findings and NOT legal conclusions.
    """

    suspect = primary_suspect.get(
        "name"
    )

    if not suspect or suspect == "Unknown":
        return []

    evidence = []

    # -----------------------------------------------------
    # RELATIONSHIP EVIDENCE
    # -----------------------------------------------------

    for relationship in relationships:

        source = relationship.get(
            "source",
            ""
        )

        target = relationship.get(
            "target",
            ""
        )

        if suspect != source and suspect != target:
            continue

        relationship_type = relationship.get(
            "relationship",
            "UNKNOWN"
        )

        text = relationship.get(
            "evidence",
            ""
        )

        readable_relationship = format_relationship(
            relationship_type
        )

        description = (
            source
            + " "
            + readable_relationship
            + " "
            + target
            + "."
        )

        evidence.append({
            "category": "NETWORK_RELATIONSHIP",
            "description": description,
            "source": text,
            "confidence": relationship.get(
                "confidence",
                1.0
            )
        })

    # -----------------------------------------------------
    # ALERT EVIDENCE
    # -----------------------------------------------------

    for alert in alerts:

        alert_entities = alert.get(
            "entities",
            []
        )

        if suspect not in alert_entities:
            continue

        evidence.append({
            "category": "SUSPICIOUS_ACTIVITY",
            "description": alert.get(
                "message",
                ""
            ),
            "severity": alert.get(
                "severity",
                "UNKNOWN"
            ),
            "confidence": alert.get(
                "confidence",
                0
            )
        })

    # -----------------------------------------------------
    # SYNDICATE ASSOCIATION
    # -----------------------------------------------------

    # Support both:
    #
    # "members": ["Amit Sharma", "Ravi Kumar"]
    #
    # and:
    #
    # "members": [
    #     "PERSON_AMIT_SHARMA",
    #     ...
    # ]

    for syndicate in get_syndicate_list(
        syndicates
    ):

        members = syndicate.get(
            "members",
            []
        )

        member_names = []

        for member in members:

            if member.startswith(
                "PERSON_"
            ):

                name = member.replace(
                    "PERSON_",
                    ""
                )

                name = name.replace(
                    "_",
                    " "
                )

                member_names.append(
                    name.title()
                )

            else:

                member_names.append(
                    member
                )

        if suspect not in member_names:
            continue

        evidence.append({
            "category": "SYNDICATE_ASSOCIATION",
            "description": (
                suspect
                + " is associated with "
                + str(
                    syndicate.get(
                        "id",
                        "Unknown"
                    )
                )
                + "."
            ),
            "members": member_names
        })

    return evidence


# =========================================================
# SYNDICATE HELPERS
# =========================================================

def get_syndicate_list(syndicates):
    """
    Support both:

        [
            {...},
            {...}
        ]

    and:

        {
            "syndicates": [...]
        }
    """

    if isinstance(
        syndicates,
        dict
    ):

        return syndicates.get(
            "syndicates",
            []
        )

    if isinstance(
        syndicates,
        list
    ):

        return syndicates

    return []


def get_syndicate_count(syndicates):

    return len(
        get_syndicate_list(
            syndicates
        )
    )


# =========================================================
# ALERT HELPERS
# =========================================================

def count_alerts_by_severity(
    alerts,
    severity
):
    """
    Count alerts with a specific severity.
    """

    count = 0

    for alert in alerts:

        if alert.get(
            "severity"
        ) == severity:

            count += 1

    return count


# =========================================================
# RELATIONSHIP FORMATTER
# =========================================================

def format_relationship(
    relationship
):
    """
    Convert relationship constants into
    human-readable text.
    """

    replacements = {

        "CALLED":
            "called",

        "CONTACTED":
            "contacted",

        "MET":
            "met",

        "VISITED":
            "visited",

        "OWNS":
            "owns",

        "USED":
            "used",

        "USED_VEHICLE":
            "used vehicle",

        "USED_PHONE":
            "used phone",

        "TRANSFERRED_MONEY_TO":
            "transferred money to",

        "ASSOCIATED_WITH_LOCATION":
            "was associated with location"
    }

    if relationship in replacements:

        return replacements[
            relationship
        ]

    return relationship.lower().replace(
        "_",
        " "
    )