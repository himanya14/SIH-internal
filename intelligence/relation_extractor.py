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

def extract_relationships(text, entities, source_type="FIR"):

    doc = nlp(text)

    relationships = []

    known_entities = build_known_entities(entities)

    for sentence in doc.sents:

        sentence_relationships = extract_from_sentence(
            sentence,
            known_entities,
            source_type
        )

        relationships.extend(sentence_relationships)

    return remove_duplicates(relationships)


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

    for category, entity_type in entity_type_mapping.items():

        for value in entities.get(category, []):

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
    # Handle use / used / using separately
    #
    # "used" is not a generic relationship.
    #
    # Person + phone   -> USED_PHONE
    # Person + vehicle -> USED_VEHICLE
    # -----------------------------------------------------

    relationships.extend(
        extract_usage_relationships(
            sentence,
            sentence_entities,
            source_type
        )
    )

    # -----------------------------------------------------
    # Find normal relationship verbs
    # -----------------------------------------------------

    for token in sentence:

        lemma = token.lemma_.lower()

        if lemma not in RELATION_VERBS:
            continue

        relationship = RELATION_VERBS[lemma]

        # -------------------------------------------------
        # Active voice
        # -------------------------------------------------

        source = find_source_entity(
            token,
            sentence_entities
        )

        target = find_target_entity(
            token,
            sentence_entities
        )

        if source and target:

            # Don't create generic vehicle relationship
            # if the target is a phone/vehicle through a
            # specialized relationship.
            if relationship == "USED_VEHICLE":
                continue

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

        # -------------------------------------------------
        # Passive voice
        # -------------------------------------------------

        else:

            passive_result = extract_passive_relationship(
                token,
                sentence_entities
            )

            if passive_result:

                source, target = passive_result

                relationships.append(
                    create_relationship(
                        source,
                        target,
                        relationship,
                        sentence.text,
                        source_type,
                        0.93
                    )
                )

        # -------------------------------------------------
        # Phone relationships for call/contact
        # -------------------------------------------------

        relationships.extend(
            extract_phone_relationships(
                token,
                sentence_entities,
                sentence.text,
                source_type
            )
        )

        # -------------------------------------------------
        # Vehicle relationships for drive
        # -------------------------------------------------

        relationships.extend(
            extract_vehicle_relationships(
                token,
                sentence_entities,
                sentence.text,
                source_type
            )
        )

    # -----------------------------------------------------
    # Location relationships
    # -----------------------------------------------------

    location_relationships = extract_location_relationships(
        sentence_entities,
        sentence.text,
        source_type
    )

    # Don't create a generic location relationship if
    # a specific VISITED relationship already exists.

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

        if entity_text.lower() in sentence_lower:

            start = sentence_lower.find(
                entity_text.lower()
            )

            end = start + len(entity_text)

            results.append({
                "text": entity_text,
                "type": entity["type"],
                "start": start,
                "end": end
            })

    # Sort according to their position in the sentence
    results.sort(
        key=lambda x: x["start"]
    )

    return results


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

    if subject is None:
        return None

    return token_to_entity(
        subject,
        sentence_entities
    )


# =========================================================
# FIND TARGET
# =========================================================

def find_target_entity(
    verb,
    sentence_entities
):

    # -----------------------------------------------------
    # Direct object
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Prepositional object
    # -----------------------------------------------------

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
# PASSIVE VOICE
# =========================================================

def extract_passive_relationship(
    verb,
    sentence_entities
):

    passive_subject = None
    agent = None

    # -----------------------------------------------------
    # Find passive subject
    #
    # Example:
    #
    # Amit was contacted by Ravi.
    #
    # Amit -> nsubjpass
    # -----------------------------------------------------

    for child in verb.children:

        if child.dep_ == "nsubjpass":

            passive_subject = token_to_entity(
                child,
                sentence_entities
            )

    # -----------------------------------------------------
    # Find "by + entity"
    # -----------------------------------------------------

    for child in verb.children:

        if (
            child.dep_ in ["agent", "prep"]
            and child.text.lower() == "by"
        ):

            for grandchild in child.children:

                if grandchild.dep_ == "pobj":

                    agent = token_to_entity(
                        grandchild,
                        sentence_entities
                    )

    # -----------------------------------------------------
    # Reverse the direction
    #
    # Amit was contacted by Ravi
    #
    # becomes:
    #
    # Ravi -> CONTACTED -> Amit
    # -----------------------------------------------------

    if passive_subject and agent:

        return agent, passive_subject

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
        relative_token_start + len(token.text)
    )

    # -----------------------------------------------------
    # Direct overlap
    # -----------------------------------------------------

    for entity in sentence_entities:

        if (
            entity["start"]
            <= relative_token_start
            < entity["end"]
        ):

            return entity

    # -----------------------------------------------------
    # Multi-word entity
    #
    # Example:
    # Ravi Kumar
    #
    # spaCy may give us token "Ravi"
    # while our entity is "Ravi Kumar"
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

    # -----------------------------------------------------
    # Find person performing the action
    # -----------------------------------------------------

    persons = [
        entity
        for entity in sentence_entities
        if entity["type"] == "PERSON"
    ]

    if not persons:
        return relationships

    source = persons[0]

    # -----------------------------------------------------
    # Person -> Phone
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Person -> Vehicle
    # -----------------------------------------------------

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

    if not persons or not locations:
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

def remove_duplicates(relationships):

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

            unique.append(relationship)

    return unique