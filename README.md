# DeepSchedule Backend

Ten projekt to backend systemu generowania planu lekcji, napisany w Pythonie. Wykorzystuje model AI (REINFORCE) do generowania planu lekcji na podstawie danych pobranych z bazy MySQL, a następnie zapisuje wygenerowany plan do bazy. Backend udostępnia API (przy użyciu Flask), które pozwala frontendowi na pobieranie planu.

## Wymagania

- Python 3.11
- Baza MySQL (konfiguracja w `config.py`)
- Poniższe pakiety (zainstalowane za pomocą `pip install -r requirements.txt`):
  - Flask==2.2.5
  - Flask-Cors==3.0.10
  - pymysql==1.1.0
  - tensorflow==2.15.0
  - tensorflow-probability==0.23.0

## Konfiguracja

- Plik `config.py` zawiera ustawienia połączenia z bazą MySQL oraz nazwę tabeli, w której zapisany jest plan:

## API Endpointy

- **GET `/api/plan`**  
  Zwraca aktualny plan lekcji zapisany w bazie w formacie JSON.

- **POST `/api/plan/generate`**  
  Uruchamia proces generowania planu lekcji przy użyciu modelu AI i zapisuje nowy plan do bazy. Następnie zwraca wygenerowany plan w formacie JSON.

## Model AI

Backend korzysta z modelu AI opartego na algorytmie REINFORCE (policy gradient):

- **Środowisko (`TimetableEnv`)** – buduje listę lekcji do przydzielenia i obsługuje logikę przydziału, w tym sprawdzanie konfliktów (np. jedna klasa nie może mieć dwóch lekcji w tym samym czasie).
- **Model polityki (`PolicyModel`)** – prosta sieć neuronowa w TensorFlow, która na podstawie stanu generuje rozkład akcji.
- **Trening** – algorytm REINFORCE, który zbiera epizody, liczy zdyskontowane nagrody i aktualizuje model.

## Zapisywanie planu

Wygenerowany plan jest zapisywany do bazy danych w tabeli `PlanLekcji`. Każdy rekord zawiera:
- `nauczyciel_id`
- `oddzial_id`
- `przedmiot_id`
- `day` (dzień tygodnia, 0=Monday, 4=Friday)
- `slot` (numer slotu lekcyjnego)
- `room` (indeks sali)

Frontend (planowany wkrótce) będzie pobierał dane z API i prezentował je użytkownikowi.

---

© 2025 DeepSchedule. Wszystkie prawa zastrzeżone.