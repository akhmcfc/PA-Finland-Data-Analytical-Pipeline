"""
Finnish to English translations for Project Access Pipeline
"""

FINNISH_TO_ENGLISH = {
    # COUNTRIES
    "Ranska": "France",
    "Saksa": "Germany",
    "Japani": "Japan",
    "Etelä-Korea": "South Korea",
    "Pohjois-Korea": "North Korea",
    "Kiina": "China",
    "Intia": "India",
    "Thaimaa": "Thailand",
    "Vietnam": "Vietnam",
    "Singaporen": "Singapore",
    "Hongkong": "Hong Kong",
    "Britannia": "UK",
    "Yhdysvallat": "USA",
    "Kanada": "Canada",
    "Ruotsi": "Sweden",
    "Norja": "Norway",
    "Tanska": "Denmark",
    "Alankomaat": "Netherlands",
    "Belgia": "Belgium",
    "Sveitsi": "Switzerland",
    "Itävalta": "Austria",
    "Itälia": "Italy",
    "Espanja": "Spain",
    "Portugali": "Portugal",
    "Kreikka": "Greece",
    "Puola": "Poland",
    "Unkari": "Hungary",
    "Tšekki": "Czech Republic",
    "Australia": "Australia",
    "Uusi-Seelanti": "New Zealand",
    "Brasilia": "Brazil",
    "Meksiko": "Mexico",
    "Argentiina": "Argentina",
    "Emiraadit": "UAE",
    "Singapore": "Singapore",
    "Paikka": "Place",
    
    # REGIONS/DESTINATIONS
    "Manner-Eurooppa": "Continental Europe",
    "Oseania": "Oceania",
    "Iso-Britannia": "UK",
    "Pohjois-Amerikka": "North America",
    "Etelä-Amerikka": "South America",
    "Aasia": "Asia",
    "Afrikka": "Africa",
    "Pohjoinen Eurooppa": "Northern Europe",
    "Eurooppa": "Europe",
    
    # FINNISH CITIES
    "Helsinki": "Helsinki",
    "Espoo": "Espoo",
    "Tampere": "Tampere",
    "Turku": "Turku",
    "Oulu": "Oulu",
    "Jyväskylä": "Jyväskylä",
    "Kuopio": "Kuopio",
    "Lahti": "Lahti",
    "Pori": "Pori",
    "Kouvola": "Kouvola",
    
    # FIELDS OF STUDY
    "Lakitiedettä": "Law",
    "Liiketalous": "Business & Economics",
    "Taloustiede": "Economics",
    "Tietojenkäsittelytiede": "Computer Science",
    "Ohjelmistotekniikka": "Software Engineering",
    "Tietotekniikka": "IT",
    "Lääketiede": "Medicine",
    "Hoitotiede": "Nursing",
    "Psykologia": "Psychology",
    "Fysiikka": "Physics",
    "Kemia": "Chemistry",
    "Biologia": "Biology",
    "Matematiikka": "Mathematics",
    "Tekniikka": "Engineering",
    "Arkkitehtuuri": "Architecture",
    "Taide": "Arts",
    "Musiikin": "Music",
    "Historia": "History",
    "Filosofia": "Philosophy",
    "Sosiologia": "Sociology",
    "Antropologia": "Anthropology",
    "Kielitieteet": "Linguistics",
    "Kirjallisuus": "Literature",
    "Maantiede": "Geography",
    "Ympäristötiede": "Environmental Science",
    "Kemian": "Chemistry",
    "Fysiikan": "Physics",
    "Biologian": "Biology",
    
    # COMMON PHRASES - UNCERTAINTY
    "En ole vielä varma": "Not sure yet",
    "En ole varma": "Not sure",
    "En tiedä": "I don't know",
    "En ole päättänyt": "Haven't decided",
    "Ei ole varmaa": "Not sure",
    "Vielä miettimässä": "Still thinking",
    "Todella en tiedä": "Really don't know",
    "Ei varma": "Not sure",
    "Epävarma": "Uncertain",
    "Mahdollisesti": "Maybe",
    "Luultavasti": "Probably",
    "Ehkä": "Maybe",
    "Kai": "Maybe",
    "Varmasti": "Definitely",
    "Todella": "Really",
    "Kovin": "Very",
    "Hyvin": "Very",
    "Liian": "Too",
    
    # COMMON PHRASES - LOCATION
    "haluan vain ulkomailla": "Want to go abroad",
    "haluan ulkomailla": "Want to go abroad",
    "vain ulkomailla": "Just abroad",
    "Muualla maailmassa": "Somewhere in the world",
    "Muualla": "Elsewhere",
    "Euroopassa": "In Europe",
    "Aasian": "In Asia",
    "Amerikassa": "In America",
    "Australiassa": "In Australia",
    "Jokin näistä": "One of these",
    "Kaikissa": "All of them",
    "Missä tahansa": "Anywhere",
    "Paljon paikkoja": "Many places",
    "Avointa": "Open",
    "Ulkomailla": "Abroad",
    "Kotimaassa": "In Finland",
    "Maailmalla": "Around the world",
    
    # CONNECTORS
    "tai": "or",
    "ja": "and",
    "sekä": "and",
    "kuin": "as",
    "kun": "when",
    "jos": "if",
    "mutta": "but",
    "koska": "because",
    
    # COMMON WORDS
    "suuri": "big",
    "pieni": "small",
    "hyvä": "good",
    "huono": "bad",
    "kiva": "nice",
    "hieno": "great",
    "huomattava": "significant",
    
    # SPECIAL CHARACTERS / ENCODING ISSUES
    "u00e4": "",
    "ä": "a",
    "ö": "o",
    "å": "a",
}

def is_structured_entry(text):
    """Check if text is a structured entry (country/region) vs free-text"""
    if not text:
        return False
    
    text_str = str(text).strip()
    
    # Free-text indicators
    if any(char in text_str for char in ["!", "?", "*", "/"]):
        return False
    
    if len(text_str) > 50:
        return False
    
    if any(word in text_str.lower() for word in ["i'm", "want", "don't", "haluan", "en ole", "tiedä", "varma"]):
        return False
    
    return True

def translate_to_english(text):
    """Translate Finnish text to English"""
    if not text:
        return text
    
    text_str = str(text).strip()
    
    # Check for exact matches first
    if text_str in FINNISH_TO_ENGLISH:
        return FINNISH_TO_ENGLISH[text_str]
    
    # Check for partial matches (common substrings)
    for finnish, english in FINNISH_TO_ENGLISH.items():
        if len(finnish) > 3 and finnish in text_str:
            return text_str.replace(finnish, english)
    
    return text_str

def translate_destination(dest):
    """Translate destination with smart detection"""
    if not dest:
        return dest
    
    dest_str = str(dest).strip()
    
    # If it's structured (country/region), translate it
    if is_structured_entry(dest_str):
        return translate_to_english(dest_str)
    
    # If it's free-text, keep it as-is (it's a user's personal response)
    return dest_str

def translate_list(items):
    """Translate a list of items"""
    if isinstance(items, list):
        return [translate_to_english(item) for item in items]
    elif isinstance(items, str):
        try:
            import json
            parsed = json.loads(items)
            if isinstance(parsed, list):
                return [translate_to_english(item) for item in parsed]
        except:
            pass
    return translate_to_english(items)
