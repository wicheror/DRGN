# DRGN MVP v2 — lokalny prototyp

Wersja 2 poprawia głównie interfejs testowy.

## Jak uruchomić

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Co zmieniono względem v1

- przycisk następnej tury jest stale widoczny w lewym panelu
- raport tury / feed hodowli jest stale widoczny w prawym panelu
- ekran hodowli pokazuje wszystkie aktywne smoki naraz
- akcje opieki są dostępne bezpośrednio na kartach smoków
- genealogia jest pokazana jako proste drzewo tekstowe
- schadzki i jajka są nadal w osobnych sekcjach
- debug został przeniesiony do panelu bocznego

To dalej jest lokalny prototyp do testów core loopa, nie gotowa gra.


## v2.1

Naprawiono błąd Streamlit: `Columns can only be placed inside other columns up to one level of nesting`.


## v3.2 — portrety jako PNG

Ta wersja całkowicie usuwa surowe HTML/SVG z interfejsu i renderuje portrety smoków jako zwykłe obrazki PNG generowane przez Pythona/Pillow.

To powinno rozwiązać błąd frontendu Streamlit:
`TypeError: First argument must be a String, HTMLElement, HTMLCollection, or NodeList`.


## v4 — ekonomia hodowlana

Ta wersja zmienia rdzeń prototypu:

- cyfrowe statystyki są schowane w szczegółach
- na kartach smoków widać prosty stan, nastrój, gotowość do schadzki i wartość sprzedaży
- mikroakcje typu nakarm/zabawa/odpoczynek zastąpiono jedną „decyzją dnia”
- można sprzedać smoka do innej hodowli i zarobić monety
- można wypuścić smoka w dzikość bez zarobku
- ekonomia jest czytelniejsza: dorosłe stabilne smoki dają przychód, młode i jajka kosztują utrzymanie
- panel boczny pokazuje dzienny bilans monet
- przy schadzkach pokazuje się koszt, ile zostanie monet i ryzyko finansowe
- jeśli linia wygaśnie, można zacząć nową od dzikiego jaja


## v5 — wiedza, przygotowanie i ryzyko

Ta wersja dodaje głębszą warstwę hodowlaną:

- płatne przygotowanie do schadzki:
  - zadbaj przed schadzką — 10 monet
  - rytuał hodowlany — 25 monet
  - luksusowe warunki — 45 monet
- poziom rozpoznania smoka:
  - obserwacja
  - wycena rynkowa
  - ocena hodowlana
  - test genetyczny
- ukryte cechy genetyczne, które nie są od razu widoczne
- test genetyczny może ujawnić ukryte cechy
- prognoza połączenia przed schadzką:
  - szansa jajka
  - szansa wielu jaj
  - prognozowana wartość potomstwa
  - potencjał rzadkich cech
  - ryzyko ukrytych wad
  - kompatybilność temperamentu
- przygotowanie resetuje się po schadzce
- sprzedaż używa stabilniejszej wartości bazowej smoka, zamiast zmieniać się co turę

Główna idea: monety kupują nie tylko schadzkę, ale też wiedzę, przygotowanie i mniejszą niepewność.


## v6 — statusy, raporty i czytelna wiedza

Najważniejsze zmiany:

### Wycena i sprzedaż
- Wycena rynkowa pokazuje konkretną cenę sprzedaży w tej turze.
- Przycisk sprzedaży nie pokazuje ceny, dopóki nie wykonasz wyceny.
- Sprzedaż bez wyceny ujawnia cenę dopiero po fakcie.
- Po wycenie przycisk pokazuje „Sprzedaj za X monet”.

### Ocena hodowlana i test genetyczny
- Ocena hodowlana generuje trwały raport.
- Raport jest widoczny w szczegółach smoka i pojawia się w feedzie.
- Wykonane analizy są oznaczane jako wykonane.
- Test genetyczny wyjaśnia, czy cechy są pozytywne, negatywne czy mieszane oraz jak wpływają na wartość, płodność, mutacyjność i ryzyko.

### Statusy smoków
Decyzja dnia została zastąpiona trwałym statusem:
- W hodowli
- Przygotowany do schadzki
- Smok pracujący
- W dzikości
- Odpoczynek
- Reproduktor / Matka linii

Status działa, dopóki go nie zmienisz.

### Praca smoków
- Smok pracujący zarabia monety co turę.
- Smok pracujący nadal może być użyty do reprodukcji.
- Różne smoki mają różne predyspozycje do pracy.
- Przewidywany zarobek i ryzyko pracy zależą od koloru, rozmiaru, temperamentu, rogów, wzoru i innych cech.

### Głowa linii
- Reproduktor / Matka linii daje bonus ekonomiczny hodowli i wpływa na wagę genealogiczną.


## v7 — lifecycle, recovery and compact UI

### Kondycja
- Status „Odpoczynek” jest darmowy i regeneruje wolniej, ale mocniej niż wcześniej.
- Dodano płatną akcję „Pełna kuracja”, która natychmiast podnosi stan smoka blisko maksimum.
- Dodano akcję „Buduj więź”, która rozwija relację z konkretnym smokiem.
- Więź obniża koszt związania smoka z hodowlą i zmniejsza ryzyko odejścia.

### Cykl życia
- Na karcie smoka widać licznik tur do kolejnego etapu życia.
- Przed starością i możliwym odejściem pojawia się ostrzeżenie.
- Stary smok z wysoką więzią ma mniejsze ryzyko odejścia.

### Widok hodowli
- Widok jest bardziej kompaktowy.
- Smoki są pogrupowane według wieku: starość, dorosłe, młode.
- Jaja są widoczne bezpośrednio w hodowli, na dole, z licznikiem do wyklucia.
- Usunięto osobny widok jaj.

### Feed
- Feed został zwężony i pokazuje mniej wpisów, żeby zostawić więcej miejsca na smoki.

### Genealogia
- Genealogia została przebudowana w diagram Graphviz pokazujący relacje rodzic–dziecko.
- Głowy linii są oznaczane koroną.


## v7.1 — poprawka widoku hodowli i genealogii

- Naprawiono widok hodowli, który w niektórych układach nie renderował kart smoków.
- Uproszczono układ kart, żeby nie zależał od zbyt złożonego zagnieżdżania kolumn.
- Jaja nadal są w hodowli.
- Genealogia pokazuje teraz najpierw tekstową listę relacji rodzic → dziecko.
- Diagram Graphviz jest dodatkowy, więc jeśli nie wyrenderuje się w środowisku, relacje nadal są widoczne.


## v7.2 — prawdziwy graf genealogii

- Genealogia nie polega już na `st.graphviz_chart`.
- Aplikacja generuje własny obraz PNG drzewa genealogicznego.
- Smoki są układane poziomami według pokolenia.
- Linie pokazują relacje rodzic → dziecko.
- Głowa linii jest oznaczona koroną.
- Smoki, które odeszły/sprzedały się, mają bardziej szary węzeł.
- Lista relacji zostaje pod grafem jako kontrola danych.


## v7.3 — poprawka relacji genealogicznych

- Naprawiono rysowanie linii w genealogii.
- Nie ma już wspólnej „szyny” sugerującej fałszywe pokrewieństwo.
- Każda linia oznacza konkretną relację rodzic → dziecko.
- Jeśli dziecko ma dwóch rodziców, dostaje dwie osobne linie.
- Rodzice spoza hodowli są widoczni w drzewie jako osobne, niebieskawe węzły.
- Dzicy partnerzy i partnerzy z obcych hodowli są podpisani w relacjach.
- Poprawiono renderowanie polskich znaków przez wymuszenie fontu Unicode.


## v7.4 — naprawa przeskakiwania widoku

- Naprawiono błąd, w którym kliknięcie statusu/przycisku na karcie smoka potrafiło przerzucić aplikację do innego widoku.
- Wybrany widok jest teraz zapamiętywany w `st.session_state.current_view`.
- Reruny po akcjach na smokach nie powinny już zmieniać zakładki/widoku.


## v8.1 — czyste przepisanie interfejsu

Ta wersja nie łata starego układu, tylko przepisuje `app.py` pod nowy layout:

- górny pasek z wyborem widoku, przyciskiem następnego dnia, licznikiem dnia i monetami
- tooltip przy monetach z opisem ekonomii
- zwijany feed dnia pod górnym paskiem
- widok hodowli w dwóch kolumnach:
  - siatka kompaktowych kart smoków
  - panel szczegółów wybranego smoka
- jaja są w hodowli
- akcje zbiorcze: status, wycena, sprzedaż

## v9 — feedback, feed i ekonomia

- Widok schadzek jest bardziej kompaktowy: mniejsze portrety, prognoza i przycisk „Umów schadzkę” wyżej.
- Krótki mechaniczny feed z emotikonami jest widoczny od razu.
- Pełny klimatyczny feed jest w rozwijanej historii.
- Po akcjach pojawia się krótki natychmiastowy feedback.
- Dodano bazowy koszt utrzymania wszystkich aktywnych smoków.
- Tooltip monet pokazuje pełniejszy breakdown ekonomii.


## v10 — modularny renderer smoków 2D

- Zastąpiono prostszy renderer portretów nowym systemem warstw.
- Smok jest składany z modułów:
  - tło/status,
  - cień,
  - skrzydła,
  - ogon,
  - korpus,
  - szyja/głowa,
  - rogi,
  - oczy,
  - wzory,
  - wiek/status/głowa linii.
- Wygląd nadal wynika z istniejących cech smoka:
  - kolor,
  - oczy,
  - wzór,
  - rogi,
  - rozmiar,
  - temperament,
  - mutacyjność,
  - rzadkość,
  - status,
  - etap życia.
- Smoki powinny być bardziej czytelne, bardziej różne i nadal generatywne.


## v11 silhouette upgrade
- procedural dragon renderer upgraded for a more dragon-like silhouette
- wedge-shaped heads, S-curve neck, better wings, structured torso, jointed legs, longer tail, dorsal spines
- no changes to saves, data model, phenotype/genotype, or external assets


## v12 — jakość linii, nie masowa sprzedaż

Ta wersja zmienia kierunek ekonomii i hodowli:

### Ekonomia / sprzedaż
- Sprzedaż młodych i przeciętnych smoków jest dużo mniej opłacalna.
- Dodano nasycenie rynku: częsta sprzedaż podobnych / słabszych smoków obniża przyszłe ceny.
- Sprzedaż jakościowego smoka może zmniejszyć nasycenie rynku i budować reputację hodowli.
- Cena rynkowa i wartość hodowlana są teraz rozdzielone.
- Ocena hodowlana pokazuje wartość hodowlaną i prestiż linii.
- Wycena rynkowa pokazuje konkretną cenę sprzedaży w tej turze.
- Prestiż linii lekko pomaga ekonomii, ale nie jest maszynką do monet.

### Cel gry / linia
- Dodano funkcje wartości hodowlanej smoka i prestiżu linii.
- Głowa linii i najlepsze smoki mają większe znaczenie.
- Sprzedaż dobrego smoka daje monety, ale traci się jego wartość dla linii.

### Wygląd / genetyka widoczna
- Rozszerzono pule widocznych cech:
  - więcej kolorów,
  - więcej wzorów,
  - więcej oczu,
  - więcej rogów.
- Mutacje przy krzyżowaniu mogą teraz wprowadzać nowe widoczne cechy, a nie tylko mieszać cechy rodziców.
- Renderer avatar.py obsługuje nowe kolory, wzory, oczy i rogi.

### Lore / content
- Rozszerzono listę imion smoków.
- Dodano więcej tekstów temperamentu dla części osobowości.


## v12.1 — hotfix

- Naprawiono błąd `NameError: temperament_compatibility is not defined` w widoku schadzek.
- Dodano prostą funkcję opisu kompatybilności temperamentów do prognozy połączenia.
- Mechanika rozmnażania nie została zmieniona — to tylko opis w preview.


## v12.2 — hotfix raportów

- Naprawiono błąd `AttributeError: 'str' object has no attribute 'get'`.
- UI obsługuje teraz raporty zapisane jako tekst oraz jako słownik.
- Dotyczy raportu oceny hodowlanej i raportu testu genetycznego.


## v13 — core loop redesign: hodowla, linia i przetrwanie

Najważniejsze zmiany:

### Życie smoków
- Smoki żyją dłużej.
- Młodość trwa 6 dni.
- Dorosłość trwa do 32 dnia.
- Starość zaczyna się później i daje więcej czasu na sukcesję.
- Młode smoki nie mogą się rozmnażać.
- Stare smoki nadal mogą się rozmnażać, ale z karą do szansy.

### Jaja
- Jaja mają imię robocze, które można nadać w hodowli.
- Jaja są widoczne jako przyszłe smoki, nie tylko timer.
- Jaja mają status/promise: zwykłe, obiecujące, dziwne, wyjątkowe.
- Czas wykluwania zależy od potencjału genetycznego.
- Dłuższy czas wykluwania jest omenem wyjątkowości.
- Wyklucie generuje mocniejszy komunikat w feedzie.

### Ekonomia
- Każdy smok kosztuje utrzymanie.
- Większa hodowla dostaje dodatkowy koszt skali.
- Młode, stare i jaja kosztują dodatkowo.
- Praca smoków ma większe znaczenie jako finansowanie hodowli.
- Praca męczy smoka i zwiększa stres / ryzyko.

### Praca smoków
- Młode smoki mogą pracować, ale mniej efektywnie.
- Stare smoki mogą pracować, ale ostrożniej.
- Predyspozycje do pracy mocniej zależą od cech, temperamentu, wieku, kondycji i więzi.

### Reprodukcja premium
- Podstawowa szansa rozmnożenia jest trochę niższa.
- Przygotowanie ma większe znaczenie.
- Rzadkie mutacje są rzadsze.
- Głowa linii stabilizuje cechy i lekko wzmacnia rzadkość potomstwa.

### Linia i prestiż
- Prestiż linii liczy najlepsze smoki, głowę linii, różnorodność i związane smoki.
- Głowa linii ma większe znaczenie ekonomiczne i hodowlane.


## v13.1 — hotfix wykluwania

- Naprawiono błąd `KeyError: 'genotype'` / próbę ponownego wykluwania jaj w `app.py`.
- W v13 funkcja `advance_day()` sama obsługuje wykluwanie, dodawanie smoka i relacje rodzic–dziecko.
- `do_next_day()` tylko dodaje raporty do feedu.


## v13.2 — final publish / onboarding

- Pierwszy smok jest teraz losowy, nie zawsze Zadra.
- Na starcie można nadać imię pierwszemu smokowi albo zostawić losowe.
- Górny niebieski feed ma krótki onboarding: co można zrobić w pierwszej turze.
- Skrótowy feed stara się pokazywać krótsze, kompletne komunikaty.
- Dodano stopkę autorską:
  - koncept: Mikołaj Wicher,
  - kontakt: wicher.ema@gmail.com,
  - współpraca: ChatGPT.


## v14 — genetyka i playtest

Najważniejsze nowe rzeczy:
- prosty system nosicielstwa cech (carrier genes),
- lepsza prognoza dziedziczenia w widoku Schadzki,
- test genetyczny może ujawniać nosicielstwo,
- ocena hodowlana podpowiada, czy smok jest lepszy do linii czy do sprzedaży/pracy,
- wycena rynkowa jest zawsze dostępna,
- sprzedaż pokazuje konkretną cenę transakcji,
- statystyki, odpoczynek i głowa linii mają bardziej czytelne opisy,
- lokalna telemetria playtestowa zapisuje podstawowe akcje gracza.
