import random

DRAGON_NAMES = [
    "Zadra", "Ignis", "Malachit", "Popiół", "Iskra", "Szrama", "Lumen", "Mrok",
    "Aster", "Kobalt", "Rubin", "Mgła", "Bursztyn", "Sol", "Nox", "Pestka",
    "Węgielek", "Heksa", "Furia", "Łuska", "Pył", "Cierń", "Szafir", "Kruk",
    "Żagiew", "Bazalt", "Tarnina", "Smuga", "Grot", "Rysa", "Miedźka", "Lazur",
    "Karmin", "Szelest", "Popiel", "Szkliwo", "Wrzos", "Kreda", "Obsydian", "Żmij",
    "Mora", "Sadzik", "Glinka", "Jantar", "Piołun", "Orlik", "Szept", "Zefir",
    "Bielik", "Kora", "Dymek", "Runa", "Wicher", "Głaz", "Irys", "Wrzask"
]

COLORS = [
    "popielaty", "czarny", "złoty", "rdzawy", "zielonkawy", "granatowy", "biały", "miedziany", "purpurowy",
    "szafirowy", "perłowy", "oliwkowy", "karminowy", "lawendowy", "stalowy", "bursztynowy", "kościany", "dymny"
]
PATTERNS = [
    "bez wzoru", "w pręgi", "w cętki", "z marmurkowaniem", "z jasnym grzbietem", "z ciemnym brzuchem",
    "z lśniącymi plamami", "łaciaty", "z maską na pysku", "z ciemnymi końcówkami skrzydeł",
    "z pręgą ogonową", "z gwiezdnymi plamkami", "z popękanymi łuskami"
]
EYES = ["bursztynowe", "zielone", "srebrne", "czarne", "złote", "błękitne", "czerwone", "fioletowe", "miodowe", "dymne"]
HORNS = [
    "bez rogów", "krótkie rogi", "zakrzywione rogi", "asymetryczne rogi", "drobne kolce",
    "koronne rogi", "baranie rogi", "pojedynczy róg", "pęknięte rogi"
]
SIZES = ["mały", "średni", "duży", "smukły", "krępy"]
TEMPERAMENTS = ["dumny", "złośliwy", "lękliwy", "ciekawski", "leniwy", "wyrachowany", "przywiązany", "dziki"]

def random_name():
    return random.choice(DRAGON_NAMES)

def describe_dragon(pet):
    ph = pet["phenotype"]
    return f'{ph["size"]}, {ph["color"]} smok {ph["pattern"]}, o {ph["eyes"]} oczach i cesze: {pet["temperament"]}.'

def temperament_line(pet):
    t = pet["temperament"]
    name = pet["name"]
    lines = {
        "dumny": [
            f"{name} pozwala ci podejść, ale tylko dlatego, że najwyraźniej sam to zaplanował.",
            f"{name} patrzy na ciebie z wysokości, nawet kiedy siedzi na podłodze.",
            f"{name} poprawia skrzydło takim ruchem, jakby cała hodowla była jego portretem.",
            f"{name} przez chwilę stoi w świetle. Nie przypadkiem. Smoki nie robią takich rzeczy przypadkiem.",
        ],
        "złośliwy": [
            f"{name} przesuwa miskę dokładnie tam, gdzie możesz się o nią potknąć.",
            f"{name} udaje, że nie rozumie, czego od niego chcesz. Rozumie doskonale.",
        ],
        "lękliwy": [
            f"{name} obserwuje cię z bezpiecznej odległości, ale nie ucieka. To już coś.",
            f"{name} chowa pysk pod skrzydło, kiedy robisz gwałtowniejszy ruch.",
        ],
        "ciekawski": [
            f"{name} wkłada nos we wszystko, czego nie powinien dotykać.",
            f"{name} znalazł dziś coś błyszczącego i uważa, że to od teraz część jego osobowości.",
        ],
        "leniwy": [
            f"{name} przeciąga się tak długo, jakby robił z tego formę sztuki.",
            f"{name} uznał, że podłoga jest dziś wystarczająco dobrym tronem.",
        ],
        "wyrachowany": [
            f"{name} patrzy na jedzenie, potem na ciebie, jakby negocjował warunki kontraktu.",
            f"{name} nie zrobił nic złego. Co jest samo w sobie podejrzane.",
            f"{name} przesuwa się dokładnie tam, gdzie będziesz musiał go ominąć.",
            f"{name} obserwuje monety z zainteresowaniem stworzenia, które rozumie pojęcie długu.",
        ],
        "przywiązany": [
            f"{name} siedzi bliżej niż zwykle i udaje, że to przypadek.",
            f"{name} pozwala ci poprawić posłanie. Potem poprawia je po swojemu.",
        ],
        "dziki": [
            f"{name} przez chwilę wygląda, jakby słyszał coś z bardzo daleka.",
            f"{name} drapie pazurem ziemię, jakby przypominał sobie zapach otwartej przestrzeni.",
            f"{name} zostawia przy wejściu ślad błota, którego nikt nie potrafi przypisać do żadnej znanej drogi.",
            f"{name} śpi z jednym okiem uchylonym. Nie ze strachu. Z przyzwyczajenia.",
        ],
    }
    return random.choice(lines.get(t, [f"{name} zachowuje się dziś niejednoznacznie."]))

def need_report(pet, need):
    name = pet["name"]
    t = pet["temperament"]

    reports = {
        "care": [
            f"{name} oddycha ciężej niż zwykle. Nie robi sceny, ale jego łuski straciły trochę blasku.",
            f"{name} nie wygląda dramatycznie. Właśnie dlatego łatwo byłoby to zignorować. Lepiej nie.",
        ],
        "play": [
            f"{name} od rana przestawia rzeczy w hodowli. Wygląda to mniej jak chaos, a bardziej jak komentarz.",
            f"{name} demonstracyjnie ignoruje zabawki, po czym sprawdza, czy patrzysz.",
        ],
        "rest": [
            f"{name} próbuje wyglądać majestatycznie, ale zasypia w połowie przeciągania skrzydła.",
            f"{name} położył pysk na łapach i nie reaguje nawet na dźwięk otwieranej szafki.",
        ],
        "calm": [
            f"{name} trzyma ogon ciasno przy ciele i śledzi każdy twój ruch. Nie jest zły. Jest spięty.",
            f"{name} siedzi w kącie i udaje, że wszystko kontroluje. Nie kontroluje.",
        ],
        "hungry": [
            f"{name} siedzi przy misce i patrzy na ciebie z cierpliwością, która brzmi jak groźba.",
            f"{name} nie prosi o jedzenie. On tworzy sytuację, w której sam powinieneś dojść do wniosku.",
        ],
        "well": [
            f"{name} przeciąga się leniwie i pozwala ci podejść bliżej niż zwykle. To prawie komplement.",
            f"{name} wygląda dziś dobrze. Trochę zbyt zadowolony z siebie, ale dobrze.",
        ],
    }

    base = random.choice(reports.get(need, reports["well"]))
    flair = temperament_line(pet)
    return f"{base}\n\n{flair}"

def adventure_result_text(pet, outcome):
    name = pet["name"]
    if outcome == "good":
        return f"{name} wrócił z dzikości z gałązką w pysku i miną kogoś, kto przeżył coś ważnego, ale nie zamierza o tym opowiadać."
    if outcome == "mutation":
        return f"{name} wrócił późno. Przez chwilę jego cień nie zgadzał się z kształtem ciała. To pewnie normalne. Pewnie."
    if outcome == "stress":
        return f"{name} wrócił spięty i obcy. Nie podchodzi od razu. Dzikość coś w nim poruszyła."
    if outcome == "injury":
        return f"{name} wrócił z zadrapaniem i obrażoną miną, jakby to świat zachował się nieprofesjonalnie."
    return f"{name} wrócił z dzikości bez wyjaśnień."

def breeding_text(parent_a, parent_b, success, eggs_count):
    if not success:
        return f"Schadzka między {parent_a['name']} i {parent_b['name']} była pełna napięcia, gestów i wzajemnej oceny. Jajek brak."
    if eggs_count == 1:
        return f"{parent_a['name']} i {parent_b['name']} najwyraźniej doszli do jakiegoś porozumienia. Pojawiło się jedno jajko."
    return f"Po schadzce hodowla jest nienaturalnie cicha. Znaleziono {eggs_count} jajka."
