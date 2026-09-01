import re

import spacy


# Load NLP model
nlp = spacy.load("en_core_web_sm")


# Terms that spaCy may classify as organisations
# but are not useful investigative organisations.
EXCLUDED_ORGANISATIONS = {
    "INR",
    "RS",
    "USD",
    "EUR",
    "GBP",
    "CINTRA"
}


def extract_entities(text):

    doc = nlp(text)

    entities = {
        "persons": [],
        "phones": [],
        "vehicles": [],
        "locations": [],
        "organisations": [],
        "bank_accounts": [],
        "dates_times": []
    }

    # =====================================================
    # 1. SPACY NER
    # =====================================================

    for ent in doc.ents:

        entity_text = ent.text.strip()

        # Never allow phone numbers to become dates
        if ent.label_ in ["DATE", "TIME"]:

            if not re.fullmatch(
                r"(?:\+91[-\s]?)?[6-9]\d{9}",
                entity_text
            ):
                entities["dates_times"].append(
                    entity_text
                )

        elif ent.label_ == "PERSON":

            entities["persons"].append(
                entity_text
            )

        elif ent.label_ in ["GPE", "LOC", "FAC"]:

            entities["locations"].append(
                entity_text
            )

        elif ent.label_ == "ORG":

            # Ignore currency codes and CINTRA itself.
            if (
                entity_text.upper()
                not in EXCLUDED_ORGANISATIONS
            ):
                entities["organisations"].append(
                    entity_text
                )

    # =====================================================
    # 2. PHONE NUMBERS
    # =====================================================

    phone_pattern = (
        r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b"
    )

    phones = re.findall(
        phone_pattern,
        text
    )

    for phone in phones:

        phone = phone.strip()

        if phone not in entities["phones"]:
            entities["phones"].append(
                phone
            )

    # =====================================================
    # 3. VEHICLE NUMBERS
    # =====================================================

    vehicle_pattern = (
        r"\b[A-Z]{2}"
        r"\d{1,2}"
        r"[A-Z]{1,3}"
        r"\d{4}\b"
    )

    vehicles = re.findall(
        vehicle_pattern,
        text.upper()
    )

    for vehicle in vehicles:

        if vehicle not in entities["vehicles"]:
            entities["vehicles"].append(
                vehicle
            )

    # =====================================================
    # 4. LOCATION PATTERNS
    # =====================================================

    # Examples:
    # Sector 21
    # Sector 17
    # Block A
    # Area 51

    location_patterns = [
        r"\bSector\s+\d+[A-Za-z]?\b",
        r"\bBlock\s+[A-Za-z0-9]+\b",
        r"\bArea\s+\d+[A-Za-z]?\b"
    ]

    for pattern in location_patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for location in matches:

            location = location.strip()

            # Normalize capitalization
            location = " ".join(
                word.capitalize()
                for word in location.split()
            )

            if location not in entities["locations"]:
                entities["locations"].append(
                    location
                )

    # =====================================================
    # 5. PERSON NAME RECOVERY
    # =====================================================

    # Generic FIR-style names often appear as:
    #
    # Ravi Kumar
    # Amit Sharma
    # Raj Malhotra
    #
    # spaCy's small model may miss some of these names,
    # so consecutive capitalized words are also checked.

    name_pattern = (
        r"\b[A-Z][a-z]+"
        r"(?:\s+[A-Z][a-z]+)+\b"
    )

    possible_names = re.findall(
        name_pattern,
        text
    )

    excluded_phrases = {
        "Sector",
        "Block",
        "Area",
        "Vehicle",
        "Bank Account",
        "Phone Number"
    }

    for name in possible_names:

        name = name.strip()

        if name in excluded_phrases:
            continue

        if name in entities["vehicles"]:
            continue

        if name not in entities["persons"]:
            entities["persons"].append(
                name
            )

    # =====================================================
    # 6. BANK ACCOUNT NUMBERS
    # =====================================================

    # Do not classify every long number as an account.
    # Require account-related context.

    account_patterns = [
        (
            r"(?:account|a/c|account\s+number)"
            r"\s*(?:no\.?|number)?\s*[:\-]?\s*"
            r"(\d{9,18})"
        )
    ]

    for pattern in account_patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for account in matches:

            if (
                account not in entities["phones"]
                and account
                not in entities["bank_accounts"]
            ):
                entities["bank_accounts"].append(
                    account
                )

    # =====================================================
    # 7. REMOVE PARTIAL PERSON NAMES
    # =====================================================

    # Example:
    #
    # Malhotra
    # Raj Malhotra
    #
    # Keep only Raj Malhotra.

    normalized_persons = []

    for person in entities["persons"]:

        is_partial = False

        for other_person in entities["persons"]:

            if person == other_person:
                continue

            if (
                person.lower()
                in other_person.lower()
                and len(person) < len(other_person)
            ):
                is_partial = True
                break

        if not is_partial:
            normalized_persons.append(
                person
            )

    entities["persons"] = normalized_persons

    # Remove people that are actually locations.

    entities["persons"] = [
        person
        for person in entities["persons"]
        if person not in entities["locations"]
    ]

    # =====================================================
    # 8. FINAL ORGANISATION CLEANUP
    # =====================================================

    # Run the filter again in case another extraction
    # path adds an excluded organisation in the future.

    entities["organisations"] = [
        organisation
        for organisation
        in entities["organisations"]
        if (
            organisation.strip().upper()
            not in EXCLUDED_ORGANISATIONS
        )
    ]

    # =====================================================
    # 9. FINAL CLEANUP
    # =====================================================

    for key in entities:

        cleaned = []

        for item in entities[key]:

            item = item.strip()

            if (
                item
                and item not in cleaned
            ):
                cleaned.append(
                    item
                )

        entities[key] = cleaned

    return entities