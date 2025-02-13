# DeepSchedule – Struktura bazy danych

Skrypt [`initialize_database.py`](./backend/initialize_database.py) w języku **Python** (z biblioteką
[PyMySQL](https://pypi.org/project/PyMySQL/)) łączy się z bazą MySQL i tworzy następujące
tabele:

1. [Przedmiot](#tabela-przedmiot)
2. [Nauczyciel](#tabela-nauczyciel)
3. [Oddzial](#tabela-oddzial)
4. [Sala](#tabela-sala)
5. [NauczycielOddzialPrzedmiot](#tabela-nauczycieloddzialprzedmiot) (łącznik)

Po utworzeniu tabel do każdej z nich wstawiane są **przykładowe dane**.

---

## Wymagania

- Python 3.x
- Biblioteka PyMySQL:
  ```bash
  pip install pymysql
  ```
- Działający serwer MySQL, z utworzoną bazą (domyślnie `s5_deepschedule`).

---

## Sposób użycia

1. Skonfiguruj parametry połączenia w pliku `initialize_database.py`:
   ```python
   host = '193.111.249.78'
   user = 'u5_AF6h3cTZj3'
   password = 'f.AY5y6GmUtdCD5Sx1=.bByx'
   database = 's5_deepschedule'
   port = 3306
   ```
2. Uruchom:
   ```bash
   python initialize_database.py
   ```
3. Skrypt:
   - Usunie istniejące tabele (z wyłączonym `FOREIGN_KEY_CHECKS`).
   - Stworzy na nowo wszystkie wymagane tabele.
   - Wstawi przykładowe rekordy demonstrujące strukturę i działanie.

---

## Schemat bazy danych

Poniżej poglądowy diagram relacji:

```
  Przedmiot               Nauczyciel               Oddzial
      |                      |                         |
      |                      |                         |
      |                      |                         |
      \-------- NauczycielOddzialPrzedmiot ----------/
                            
                 Sala (niezależna tabela)
```

### Tabela `Przedmiot`

| Kolumna | Typ         | Opis                                                |
|---------|------------|------------------------------------------------------|
| ID      | INT PK AI   | Unikatowy identyfikator (PRIMARY KEY)               |
| Nazwa   | VARCHAR(100)| Nazwa przedmiotu (np. Matematyka, Polski, Informatyka)|

---

### Tabela `Nauczyciel`

| Kolumna            | Typ                                                                                          | Opis                                                                                         |
|--------------------|----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| ID                 | INT PK AI                                                                                   | Unikatowy identyfikator                                                                      |
| Imie               | VARCHAR(100)                                                                                 | Imię nauczyciela (np. Jan)                                                                    |
| Nazwisko           | VARCHAR(100)                                                                                 | Nazwisko (np. Kowalski)                                                                       |
| Rola               | ENUM('dyrektor','nauczyciel','pedagog','pedagog specjalny','psycholog','wicedyrektor') NOT NULL | Pełniona funkcja/rola w placówce                                                              |
| GodzinyDostepnosci | VARCHAR(255)                                                                                 | Opis godzin dostępności (np. „Pn-Pt 8:00-13:00”)                                              |
| Etat               | ENUM('pelen','czesc') NOT NULL                                                               | Status etatu: pełny lub częściowy                                                             |

---

### Tabela `Oddzial`

| Kolumna | Typ        | Opis                                                   |
|---------|-----------|---------------------------------------------------------|
| ID      | INT PK AI  | Unikatowy identyfikator                                |
| Nazwa   | VARCHAR(50)| Nazwa oddziału (np. „1A”, „2B”)                         |

---

### Tabela `Sala`

| Kolumna            | Typ                                                    | Opis                                                                |
|--------------------|--------------------------------------------------------|----------------------------------------------------------------------|
| ID                 | INT PK AI                                             | Unikatowy identyfikator sali                                        |
| Nazwa              | VARCHAR(100)                                          | Nazwa/oznaczenie sali (np. „Sala 101”)                               |
| Przeznaczenie      | ENUM('komputerowa','lekcyjna','biologiczna','inne') NOT NULL | Rodzaj sali (komputerowa/lekcyjna/biologiczna/itp.)                  |
| GodzinyDostepnosci | VARCHAR(255)                                          | Opis godzin, w których sala jest dostępna                            |

---

### Tabela `NauczycielOddzialPrzedmiot`

Tabela łącznikowa, która wskazuje, **który nauczyciel** uczy **jakiego przedmiotu** w **którym oddziale**, oraz ile godzin tygodniowo przeznaczonych jest na ten przedmiot.

| Kolumna           | Typ         | Opis                                                                                  |
|-------------------|------------|----------------------------------------------------------------------------------------|
| ID                | INT PK AI   | Unikatowy identyfikator rekordu                                                       |
| NauczycielID      | INT FK      | Klucz obcy do `Nauczyciel(ID)`                                                        |
| OddzialID         | INT FK      | Klucz obcy do `Oddzial(ID)`                                                           |
| PrzedmiotID       | INT FK      | Klucz obcy do `Przedmiot(ID)`                                                         |
| TygodnioweGodziny | INT NOT NULL| Liczba godzin przedmiotu tygodniowo w danym oddziale                                  |

**Klucze obce**:
- `FOREIGN KEY (NauczycielID) REFERENCES Nauczyciel(ID)`
- `FOREIGN KEY (OddzialID) REFERENCES Oddzial(ID)`
- `FOREIGN KEY (PrzedmiotID) REFERENCES Przedmiot(ID)`

---

## Uwagi końcowe

- Obecny skrypt usuwa każdą istniejącą tabelę (`DROP TABLE IF EXISTS ...`), więc **wszystkie dane w tych tabelach** zostają usunięte.
- Po ponownym uruchomieniu skryptu, tabela zostaje stworzona na nowo i wypełniona **przykładowymi** danymi.  
- Można dowolnie modyfikować i rozwijać tę strukturę, np. dodając kolumny do `Nauczyciel`, `Sala` lub poszerzając rolę tabeli `NauczycielOddzialPrzedmiot` o godziny w konkretnych dniach, plan lekcji itp.
