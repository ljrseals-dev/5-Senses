"""Canonical MSD MusicNN 50-label order from the public MusicNN port."""

MSD_TAGS: tuple[str, ...] = (
    "rock", "pop", "alternative", "indie", "electronic", "female vocalists",
    "dance", "00s", "alternative rock", "jazz", "beautiful", "metal",
    "chillout", "male vocalists", "classic rock", "soul", "indie rock",
    "Mellow", "electronica", "80s", "folk", "90s", "chill", "instrumental",
    "punk", "oldies", "blues", "hard rock", "ambient", "acoustic",
    "experimental", "female vocalist", "guitar", "Hip-Hop", "70s", "party",
    "country", "easy listening", "sexy", "catchy", "funk", "electro",
    "heavy metal", "Progressive rock", "60s", "rnb", "indie pop", "sad",
    "House", "happy",
)

if len(MSD_TAGS) != 50 or len(set(MSD_TAGS)) != 50:
    raise RuntimeError("MSD tag vocabulary must contain 50 unique ordered labels")
