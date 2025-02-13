# DeepSchedule – Struktura bazy danych

Ten projekt zawiera skrypt w języku **Python** (z użyciem biblioteki [PyMySQL](https://pypi.org/project/PyMySQL/)), który łączy się z bazą MySQL i tworzy następujące tabele:

1. [Przedmiot](#tabela-przedmiot)
2. [Nauczyciel](#tabela-nauczyciel)
3. [Oddzial](#tabela-oddzial)
4. [Sala](#tabela-sala)
5. [NauczycielOddzialPrzedmiot](#tabela-nauczycieloddzialprzedmiot) (tabela łącznikowa)

Dane wstawiane do każdej z tabel są przykładowe i mają służyć prezentacji działania aplikacji.

---

## Spis treści

1. [Wymagania](#wymagania)
2. [Sposób użycia](#sposób-użycia)
3. [Schemat bazy danych](#schemat-bazy-danych)
   1. [Tabela `Przedmiot`](#tabela-przedmiot)
   2. [Tabela `Nauczyciel`](#tabela-nauczyciel)
   3. [Tabela `Oddzial`](#tabela-oddzial)
   4. [Tabela `Sala`](#tabela-sala)
   5. [Tabela `NauczycielOddzialPrzedmiot`](#tabela-nauczycieloddzialprzedmiot)
4. [Uwagi końcowe](#uwagi-końcowe)

---

## Wymagania

- Python 3.x  
- Zainstalowana biblioteka PyMySQL:
  ```bash
  pip install pymysql
  ```
- Dostępna baza MySQL (domyślnie korzystamy z parametrów: host, user, password, port i nazwa bazy ustawione w skrypcie).

---

## Sposób użycia

1. Skonfiguruj parametry połączenia w skrypcie (np. `initialize_database.py`), w zmiennych:
   ```python
   host = '193.111.249.78'
   user = 'u5_AF6h3cTZj3'
   password = 'f.AY5y6GmUtdCD5Sx1=.bByx'
   database = 's5_deepschedule'
   port = 3306
   ```
2. Uruchom skrypt:
   ```bash
   python initialize_database.py
   ```
3. Skrypt:
   - Połączy się z bazą `s5_deepschedule`.
   - Usunie (DROP) istniejące tabele (z wyłączeniem wymuszonego sprawdzania kluczy obcych).
   - Stworzy nowe tabele zgodnie z opisanym poniżej schematem.
   - Uzupełni je przykładowymi danymi.

---

## Schemat bazy danych

Poniższy diagram przedstawia zależności między tabelami:

```
  Przedmiot               Nauczyciel               Oddzial
      |                      |                         |
      |                      |                         |
      |                      |                         |
      \-------- NauczycielOddzialPrzedmiot ----------/
                            
                 Sala (niezależna tabela)
```

### Tabela `Przedmiot`
Przechowuje listę przedmiotów szkolnych.

| Kolumna | Typ         | Opis                                                   |
|---------|------------|---------------------------------------------------------|
| ID      | INT PK AI   | Unikatowy identyfikator (PRIMARY KEY, AUTO_INCREMENT)  |
| Nazwa   | VARCHAR(100)| Nazwa przedmiotu (np. Matematyka, Polski, Informatyka) |

**PK** = Primary Key  
**AI** = Auto Increment  

---

### Tabela `Nauczyciel`
Przechowuje informacje o nauczycielach i innych pracownikach szkoły.

| Kolumna            | Typ                                                                                                                                          | Opis                                                                                                    |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| ID                 | INT PK AI                                                                                                                                   | Unikatowy identyfikator                                                                                 |
| Imie               | VARCHAR(100)                                                                                                                                | Imię nauczyciela (np. Jan)                                                                              |
| Nazwisko           | VARCHAR(100)                                                                                                                                | Nazwisko (np. Kowalski)                                                                                 |
| Rola               | ENUM('dyrektor','nauczyciel','pedagog','pedagog specjalny','psycholog','wicedyrektor')                                                     | Rola pełniona w placówce                                                                                 |
| GodzinyDostepnosci | VARCHAR(255)                                                                                                                                | Informacja o godzinach, w których nauczyciel jest dostępny (np. „Pn-Pt 8:00-13:00”)                      |
| Etat               | ENUM('pelen','czesc')                                                                                                                       | Status etatu: pełny lub częściowy                                                                        |

---

### Tabela `Oddzial`
Przechowuje listę oddziałów (klas).

| Kolumna | Typ          | Opis                                                  |
|---------|-------------|--------------------------------------------------------|
| ID      | INT PK AI    | Unikatowy identyfikator                               |
| Nazwa   | VARCHAR(50)  | Nazwa oddziału (np. 1A, 1B, 2A)                        |

---

### Tabela `Sala`
Przechowuje listę sal (pomieszczeń) wraz z ich przeznaczeniem i dostępnością.

| Kolumna            | Typ                                                                        | Opis                                                                                      |
|--------------------|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| ID                 | INT PK AI                                                                   | Unikatowy identyfikator sali                                                              |
| Nazwa              | VARCHAR(100)                                                                | Nazwa/oznaczenie sali (np. Sala 101)                                                      |
| Przeznaczenie      | ENUM('komputerowa','lekcyjna','biologiczna','inne') NOT NULL               | Typ/przeznaczenie sali (komputerowa, lekcyjna, biologiczna, inne)                         |
| GodzinyDostepnosci | VARCHAR(255)                                                                | Opis godzin, w których sala jest dostępna (np. "Pn-Pt 8:00-16:00")                        |

---

### Tabela `NauczycielOddzialPrzedmiot`
Tabela łącznikowa, która wskazuje:

- **który nauczyciel** (NauczycielID)  
- uczy **jakiego przedmiotu** (PrzedmiotID)  
- w **którym oddziale** (OddzialID)

Dodatkowo przechowuje liczbę rocznych godzin planowanych dla danego przedmiotu w danym oddziale.

| Kolumna        | Typ    | Opis                                                                                         |
|----------------|--------|-----------------------------------------------------------------------------------------------|
| ID             | INT PK AI | Unikatowy identyfikator w tabeli                                                          |
| NauczycielID   | INT FK    | Klucz obcy do `Nauczyciel(ID)`                                                             |
| OddzialID      | INT FK    | Klucz obcy do `Oddzial(ID)`                                                                |
| PrzedmiotID    | INT FK    | Klucz obcy do `Przedmiot(ID)`                                                              |
| RoczneGodziny  | INT NOT NULL | Łączna liczba godzin w skali roku (np. 120)                                            |

**Klucze obce**:
- `FOREIGN KEY (NauczycielID) REFERENCES Nauczyciel(ID)`  
- `FOREIGN KEY (OddzialID) REFERENCES Oddzial(ID)`  
- `FOREIGN KEY (PrzedmiotID) REFERENCES Przedmiot(ID)`

---

## Uwagi końcowe

- Skrypt **usuwa** (DROP) istniejące tabele na rzecz nowej struktury. W efekcie wszystkie dotychczasowe dane w tych tabelach zostaną utracone.  
- Możesz zmodyfikować kolejność, w której tabele są usuwane, lub użyć `SET FOREIGN_KEY_CHECKS=0`, aby wyłączyć tymczasowo wymuszanie integralności kluczy obcych.  
- Jeśli potrzebujesz dodać kolejne kolumny (np. godziny lekcji, nazwa szkoły, itp.), zrób to w odpowiednich tabelach, dopasowując definicję do potrzeb.  

W ten sposób powstaje baza danych, która przechowuje informacje o:
- przedmiotach,  
- nauczycielach (wraz z rolą i dostępnością),  
- oddziałach (klasach),  
- salach o różnych przeznaczeniach,  
- ilości godzin poszczególnych przedmiotów w danych oddziałach (oraz nauczycieli, którzy ich uczą).  

---
