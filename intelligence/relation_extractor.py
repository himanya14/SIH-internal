import re

import spacy


# =========================================================
# LOAD NLP MODEL
# =========================================================

nlp = spacy.load("en_core_web_sm")


# =========================================================
# RELATIONSHIP VOCABULARY
# =========================================================

RELATION_VERBS = {
    "call": "CALLED",
    "phone": "CALLED",
    "contact": "CONTACTED",
    "meet": "MET",
    "visit": "VISITED",
    "own": "OWNS",
    "drive": "USED_VEHICLE",
    "transfer": "TRANSFERRED_MONEY_TO",
    "send": "TRANSFERRED_MONEY_TO",
    "pay": "TRANSFERRED_MONEY_TO",
}


# =========================================================
# MAIN FUNCTION
# =========================================================

def extract_relationships(
    text,
    entities,
    source_type="FIR"
):

    doc = nlp(text)

    relationships = []

    known_entities = build_known_entities(
        entities
    )

    for sentence in doc.sents:

        sentence_relationships = extract_from_sentence(
            sentence,
            known_entities,
            source_type
        )

        relationships.extend(
            sentence_relationships
        )

    return remove_duplicates(
        relationships
    )


# =========================================================
# ENTITY PREPARATION
# =========================================================

def build_known_entities(entities):

    known_entities = []

    entity_type_mapping = {
        "persons": "PERSON",
        "phones": "PHONE",
        "vehicles": "VEHICLE",
        "locations": "LOCATION",
        "organisations": "ORGANISATION",
        "bank_accounts": "BANK_ACCOUNT",
        "dates_times": "DATE_TIME"
    }

    for category, entity_type in (
        entity_type_mapping.items()
    ):

        for value in entities.get(
            category,
            []
        ):

            known_entities.append({
                "text": value,
                "type": entity_type
            })

    return known_entities


# =========================================================
# SENTENCE EXTRACTION
# =========================================================

def extract_from_sentence(
    sentence,
    known_entities,
    source_type
):

    relationships = []

    sentence_entities = find_sentence_entities(
        sentence,
        known_entities
    )

    if not sentence_entities:
        return relationships

    # -----------------------------------------------------
    # SAME-LOCATION CORRELATION
    # -----------------------------------------------------

    relationships.extend(
        extract_same_location_relationships(
            sentence,
            sentence_entities,
            source_type
        )
    )

    # -----------------------------------------------------
    # PHONE / VEHICLE USAGE
    # -----------------------------------------------------

    relationships.extend(
        extract_usage_relationships(
            sentence,
            sentence_entities,
            source_type
        )
    )

    # -----------------------------------------------------
    # VERB-BASED RELATIONSHIPS
    # -----------------------------------------------------

    for token in sentence:

        lemma = token.lemma_.lower()

        if lemma not in RELATION_VERBS:
            continue

        relationship = RELATION_VERBS[
            lemma
        ]

        source = find_source_entity(
            token,
            sentence_entities
        )

        if (
            relationship
            == "TRANSFERRED_MONEY_TO"
        ):

            target = find_financial_target_entity(
                token,
                sentence_entities
            )

        else:

            target = find_target_entity(
                token,
                sentence_entities
            )

            # -------------------------------------------------
            # PERSON-TO-PERSON FALLBACK
            # -------------------------------------------------
            #
            # Example:
            # Ravi Mehra called Neha Kapoor.
            #
            # spaCy may attach only "Kapoor" as the object,
            # while our entity is the full "Neha Kapoor".
            # If normal dependency matching fails, choose the
            # nearest person appearing after the verb.
            # -------------------------------------------------

            if target is None:

                target = find_person_target_after_verb(
                    token,
                    sentence_entities,
                    source
                )

        if source and target:

            if relationship != "USED_VEHICLE":

                relationships.append(
                    create_relationship(
                        source,
                        target,
                        relationship,
                        sentence.text,
                        source_type,
                        0.95
                    )
                )

        else:

            passive_result = (
                extract_passive_relationship(
                    token,
                    sentence_entities
                )
            )

            if passive_result:

                (
                    passive_source,
                    passive_target
                ) = passive_result

                relationships.append(
                    create_relationship(
                        passive_source,
                        passive_target,
                        relationship,
                        sentence.text,
                        source_type,
                        0.93
                    )
                )

        relationships.extend(
            extract_phone_relationships(
                token,
                sentence_entities,
                sentence.text,
                source_type
            )
        )

        relationships.extend(
            extract_vehicle_relationships(
                token,
                sentence_entities,
                sentence.text,
                source_type
            )
        )

    # -----------------------------------------------------
    # PERSON -> LOCATION RELATIONSHIP
    # -----------------------------------------------------

    location_relationships = (
        extract_location_relationships(
            sentence_entities,
            sentence.text,
            source_type
        )
    )

    specific_location_exists = any(
        relation["relationship"] == "VISITED"
        for relation in relationships
    )

    if not specific_location_exists:

        relationships.extend(
            location_relationships
        )

    return relationships


# =========================================================
# FIND ENTITIES IN SENTENCE
# =========================================================

def find_sentence_entities(
    sentence,
    known_entities
):

    results = []

    sentence_lower = sentence.text.lower()

    for entity in known_entities:

        entity_text = entity["text"]
        entity_lower = entity_text.lower()

        search_start = 0

        while True:

            start = sentence_lower.find(
                entity_lower,
                search_start
            )

            if start == -1:
                break

            end = start + len(
                entity_text
            )

            results.append({
                "text": entity_text,
                "type": entity["type"],
                "start": start,
                "end": end
            })

            search_start = end

    results.sort(
        key=lambda item: item["start"]
    )

    return results


# =========================================================
# SAME-LOCATION RELATIONSHIPS
# =========================================================

def extract_same_location_relationships(
    sentence,
    sentence_entities,
    source_type
):

    relationships = []

    persons = [
        entity
        for entity in sentence_entities
        if entity["type"] == "PERSON"
    ]

    if len(persons) < 2:
        return relationships

    sentence_lower = sentence.text.lower()

    same_location_indicators = [
        "same geographic area",
        "same geographical area",
        "same location",
        "same area",
        "same place",
        "same vicinity",
        "same geographic zone",
        "same geographical zone",
        "co-located",
        "colocated"
    ]

    has_same_location_indicator = any(
        indicator in sentence_lower
        for indicator in same_location_indicators
    )

    if not has_same_location_indicator:
        return relationships

    observation_indicators = [
        "observed",
        "seen",
        "recorded",
        "located",
        "detected",
        "present",
        "found",
        "reported",
        "captured"
    ]

    has_observation_context = any(
        indicator in sentence_lower
        for indicator in observation_indicators
    )

    if not has_observation_context:
        return relationships

    for index in range(
        len(persons)
    ):

        for second_index in range(
            index + 1,
            len(persons)
        ):

            source = persons[index]
            target = persons[second_index]

            relationships.append(
                create_relationship(
                    source,
                    target,
                    "SEEN_AT_SAME_LOCATION",
                    sentence.text,
                    source_type,
                    0.87
                )
            )

    return relationships


# =========================================================
# FIND SOURCE
# =========================================================

def find_source_entity(
    verb,
    sentence_entities
):

    subject = None

    for child in verb.children:

        if child.dep_ in [
            "nsubj",
            "csubj"
        ]:

            subject = child
            break

    if subject is not None:

        entity = token_to_entity(
            subject,
            sentence_entities
        )

        if entity:
            return entity

    # -----------------------------------------------------
    # SOURCE POSITIONAL FALLBACK
    # -----------------------------------------------------
    #
    # If dependency parsing does not map the subject to
    # the full entity, use the nearest person before verb.
    # -----------------------------------------------------

    sentence_start = verb.sent.start_char

    relative_verb_start = (
        verb.idx - sentence_start
    )

    candidates = [
        entity
        for entity in sentence_entities
        if (
            entity["type"] == "PERSON"
            and entity["end"] <= relative_verb_start
        )
    ]

    if candidates:

        candidates.sort(
            key=lambda entity: entity["end"],
            reverse=True
        )

        return candidates[0]

    return None


# =========================================================
# FIND NORMAL TARGET
# =========================================================

def find_target_entity(
    verb,
    sentence_entities
):

    for child in verb.children:

        if child.dep_ in [
            "dobj",
            "obj"
        ]:

            entity = token_to_entity(
                child,
                sentence_entities
            )

            if entity:
                return entity

    for child in verb.children:

        if child.dep_ == "prep":

            for grandchild in child.children:

                if grandchild.dep_ == "pobj":

                    entity = token_to_entity(
                        grandchild,
                        sentence_entities
                    )

                    if entity:
                        return entity

    return None


# =========================================================
# PERSON TARGET POSITIONAL FALLBACK
# =========================================================

def find_person_target_after_verb(
    verb,
    sentence_entities,
    source=None
):

    sentence_start = verb.sent.start_char

    relative_verb_end = (
        verb.idx
        - sentence_start
        + len(verb.text)
    )

    candidates = [
        entity
        for entity in sentence_entities
        if (
            entity["type"] == "PERSON"
            and entity["start"] >= relative_verb_end
        )
    ]

    if source:

        candidates = [
            entity
            for entity in candidates
            if entity["text"] != source["text"]
        ]

    if not candidates:
        return None

    candidates.sort(
        key=lambda entity: entity["start"]
    )

    return candidates[0]


# =========================================================
# FIND FINANCIAL TRANSFER TARGET
# =========================================================

def find_financial_target_entity(
    verb,
    sentence_entities
):

    sentence = verb.sent

    sentence_text = sentence.text

    to_match = re.search(
        r"\bto\b",
        sentence_text,
        flags=re.IGNORECASE
    )

    if to_match:

        to_position = to_match.end()

        candidates = [
            entity
            for entity in sentence_entities
            if (
                entity["start"] >= to_position
                and not is_currency_entity(
                    entity
                )
            )
        ]

        if candidates:

            person_candidates = [
                entity
                for entity in candidates
                if entity["type"] == "PERSON"
            ]

            if person_candidates:
                return person_candidates[0]

            return candidates[0]

    for child in verb.children:

        if (
            child.dep_ == "prep"
            and child.text.lower() == "to"
        ):

            for grandchild in child.children:

                if grandchild.dep_ == "pobj":

                    entity = token_to_entity(
                        grandchild,
                        sentence_entities
                    )

                    if (
                        entity
                        and not is_currency_entity(
                            entity
                        )
                    ):
                        return entity

    for child in verb.children:

        if child.dep_ in [
            "dobj",
            "obj",
            "dative"
        ]:

            entity = token_to_entity(
                child,
                sentence_entities
            )

            if (
                entity
                and not is_currency_entity(
                    entity
                )
            ):
                return entity

    sentence_start = sentence.start_char

    relative_verb_end = (
        verb.idx
        - sentence_start
        + len(verb.text)
    )

    candidates = [
        entity
        for entity in sentence_entities
        if (
            entity["start"] >= relative_verb_end
            and not is_currency_entity(
                entity
            )
        )
    ]

    if candidates:

        person_candidates = [
            entity
            for entity in candidates
            if entity["type"] == "PERSON"
        ]

        if person_candidates:
            return person_candidates[0]

        return candidates[0]

    return None


# =========================================================
# CURRENCY ENTITY CHECK
# =========================================================

def is_currency_entity(entity):

    if entity is None:
        return False

    value = (
        entity["text"]
        .strip()
        .lower()
    )

    currency_values = {
        "inr",
        "rs",
        "rs.",
        "rupee",
        "rupees",
        "₹",
        "usd",
        "dollar",
        "dollars",
        "$",
        "eur",
        "euro",
        "euros",
        "€",
        "gbp",
        "pound",
        "pounds",
        "£"
    }

    return value in currency_values


# =========================================================
# PASSIVE VOICE
# =========================================================

def extract_passive_relationship(
    verb,
    sentence_entities
):

    passive_subject = None
    agent = None

    for child in verb.children:

        if child.dep_ in [
            "nsubjpass",
            "nsubj:pass"
        ]:

            passive_subject = token_to_entity(
                child,
                sentence_entities
            )

    for child in verb.children:

        if (
            child.dep_ in [
                "agent",
                "prep"
            ]
            and child.text.lower() == "by"
        ):

            for grandchild in child.children:

                if grandchild.dep_ == "pobj":

                    agent = token_to_entity(
                        grandchild,
                        sentence_entities
                    )

    if passive_subject and agent:

        return (
            agent,
            passive_subject
        )

    return None


# =========================================================
# TOKEN -> ENTITY
# =========================================================

def token_to_entity(
    token,
    sentence_entities
):

    if token is None:
        return None

    token_start = token.idx

    sentence_start = token.sent.start_char

    relative_token_start = (
        token_start - sentence_start
    )

    relative_token_end = (
        relative_token_start
        + len(token.text)
    )

    # -----------------------------------------------------
    # TOKEN STARTS INSIDE ENTITY
    # -----------------------------------------------------

    for entity in sentence_entities:

        if (
            entity["start"]
            <= relative_token_start
            < entity["end"]
        ):

            return entity

    # -----------------------------------------------------
    # TOKEN ENDS INSIDE ENTITY
    # -----------------------------------------------------

    for entity in sentence_entities:

        if (
            entity["start"]
            < relative_token_end
            <= entity["end"]
        ):

            return entity

    # -----------------------------------------------------
    # TOKEN IS FULLY INSIDE ENTITY
    # -----------------------------------------------------

    for entity in sentence_entities:

        if (
            entity["start"]
            <= relative_token_start
            and relative_token_end
            <= entity["end"]
        ):

            return entity

    return None


# =========================================================
# USAGE RELATIONSHIPS
# =========================================================

def extract_usage_relationships(
    sentence,
    sentence_entities,
    source_type
):

    relationships = []

    text = sentence.text.lower()

    usage_words = [
        "use",
        "used",
        "using",
        "utilized",
        "utilising",
        "utilizing"
    ]

    if not any(
        word in text
        for word in usage_words
    ):
        return relationships

    persons = [
        entity
        for entity in sentence_entities
        if entity["type"] == "PERSON"
    ]

    if not persons:
        return relationships

    source = persons[0]

    phones = [
        entity
        for entity in sentence_entities
        if entity["type"] == "PHONE"
    ]

    if phones:

        relationships.append(
            create_relationship(
                source,
                phones[0],
                "USED_PHONE",
                sentence.text,
                source_type,
                0.92
            )
        )

    vehicles = [
        entity
        for entity in sentence_entities
        if entity["type"] == "VEHICLE"
    ]

    if vehicles:

        relationships.append(
            create_relationship(
                source,
                vehicles[0],
                "USED_VEHICLE",
                sentence.text,
                source_type,
                0.92
            )
        )

    return relationships


# =========================================================
# PHONE RELATIONSHIPS
# =========================================================

def extract_phone_relationships(
    verb,
    sentence_entities,
    evidence,
    source_type
):

    relationships = []

    phones = [
        entity
        for entity in sentence_entities
        if entity["type"] == "PHONE"
    ]

    if not phones:
        return relationships

    person = find_source_entity(
        verb,
        sentence_entities
    )

    if person is None:
        return relationships

    verb_lemma = verb.lemma_.lower()

    if verb_lemma in [
        "call",
        "phone",
        "contact"
    ]:

        relationships.append(
            create_relationship(
                person,
                phones[0],
                "USED_PHONE",
                evidence,
                source_type,
                0.92
            )
        )

    return relationships


# =========================================================
# VEHICLE RELATIONSHIPS
# =========================================================

def extract_vehicle_relationships(
    verb,
    sentence_entities,
    evidence,
    source_type
):

    relationships = []

    vehicles = [
        entity
        for entity in sentence_entities
        if entity["type"] == "VEHICLE"
    ]

    if not vehicles:
        return relationships

    person = find_source_entity(
        verb,
        sentence_entities
    )

    if person is None:
        return relationships

    verb_lemma = verb.lemma_.lower()

    if verb_lemma == "drive":

        relationships.append(
            create_relationship(
                person,
                vehicles[0],
                "USED_VEHICLE",
                evidence,
                source_type,
                0.92
            )
        )

    return relationships


# =========================================================
# LOCATION RELATIONSHIPS
# =========================================================

def extract_location_relationships(
    sentence_entities,
    evidence,
    source_type
):

    relationships = []

    persons = [
        entity
        for entity in sentence_entities
        if entity["type"] == "PERSON"
    ]

    locations = [
        entity
        for entity in sentence_entities
        if entity["type"] == "LOCATION"
    ]

    if (
        not persons
        or not locations
    ):
        return relationships

    evidence_lower = evidence.lower()

    location_indicators = [
        "near",
        "at",
        "in",
        "located",
        "seen",
        "from"
    ]

    if any(
        indicator in evidence_lower
        for indicator in location_indicators
    ):

        relationships.append(
            create_relationship(
                persons[0],
                locations[0],
                "ASSOCIATED_WITH_LOCATION",
                evidence,
                source_type,
                0.88
            )
        )

    return relationships


# =========================================================
# CREATE RELATIONSHIP
# =========================================================

def create_relationship(
    source,
    target,
    relationship,
    evidence,
    source_type,
    confidence
):

    return {
        "source": source["text"],
        "target": target["text"],
        "relationship": relationship,
        "confidence": confidence,
        "evidence": evidence.strip(),
        "source_type": source_type
    }


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(
    relationships
):

    unique = []

    seen = set()

    for relationship in relationships:

        key = (
            relationship["source"],
            relationship["target"],
            relationship["relationship"]
        )

        if key not in seen:

            seen.add(key)

            unique.append(
                relationship
            )

    return unique