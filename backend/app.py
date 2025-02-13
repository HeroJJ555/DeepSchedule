import pymysql
import numpy as np
import random, math, time
from config import DB_CONFIG, PLAN_TABLE  # plik config.py jak wcześniej

# -------------------------------------
# Funkcja pobierania danych z bazy MySQL
# -------------------------------------
def load_data_from_db():
    """
    Łączy się z bazą MySQL i pobiera:
      - oddziały,
      - nauczycieli,
      - przedmioty,
      - sale,
      - informacje z tabeli NauczycielOddzialPrzedmiot (TygodnioweGodziny).
    Zwraca słownik z danymi.
    """
    connection = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT ID, Nazwa FROM Oddzial")
            oddzialy = cursor.fetchall()
            
            cursor.execute("SELECT ID, Imie, Nazwisko, Etat, Rola, GodzinyDostepnosci FROM Nauczyciel")
            nauczyciele = cursor.fetchall()
            
            cursor.execute("SELECT ID, Nazwa FROM Przedmiot")
            przedmioty = cursor.fetchall()
            
            cursor.execute("SELECT ID, Nazwa, Przeznaczenie, GodzinyDostepnosci FROM Sala")
            sale = cursor.fetchall()
            
            cursor.execute("""
                SELECT NauczycielID, OddzialID, PrzedmiotID, TygodnioweGodziny
                FROM NauczycielOddzialPrzedmiot
            """)
            plan_info = cursor.fetchall()
            
        return {
            "oddzialy": oddzialy,
            "nauczyciele": nauczyciele,
            "przedmioty": przedmioty,
            "sale": sale,
            "plan_info": plan_info
        }
    finally:
        connection.close()

# -------------------------------------
# Definicja parametrów
# -------------------------------------
NUM_DNI = 5       # dni tygodnia (0: poniedziałek ... 4: piątek)
NUM_SLOTOW = 8    # slotów lekcyjnych dziennie

# -------------------------------------
# Klasa generująca plan lekcji przy użyciu Simulated Annealing
# -------------------------------------
class PlanGenerator:
    def __init__(self, data):
        self.nauczyciele = data["nauczyciele"]
        self.oddzialy = data["oddzialy"]
        self.przedmioty = data["przedmioty"]
        self.sale = data["sale"]
        plan_info = data["plan_info"]
        # Tworzymy listę lekcji – każdy rekord powiela się tyle razy, ile wynosi TygodnioweGodziny.
        self.lessons = []
        for row in plan_info:
            n_id = row["NauczycielID"]
            o_id = row["OddzialID"]
            p_id = row["PrzedmiotID"]
            hours = row["TygodnioweGodziny"]
            for _ in range(hours):
                self.lessons.append((n_id, o_id, p_id))
        self.num_lessons = len(self.lessons)
        self.action_space = NUM_DNI * NUM_SLOTOW * len(self.sale)  # możliwe kombinacje

    def random_schedule(self):
        """Generuje losowy plan – listę przydziałów (dla każdej lekcji losowy (dzień, slot, sala))."""
        schedule = []
        for _ in range(self.num_lessons):
            a = random.randrange(self.action_space)
            schedule.append(a)
        return schedule

    def decode_assignment(self, action):
        """Dekoduje skalarową akcję na (dzień, slot, sala)."""
        total_rooms = len(self.sale)
        day = action // (NUM_SLOTOW * total_rooms)
        remainder = action % (NUM_SLOTOW * total_rooms)
        slot = remainder // total_rooms
        room = remainder % total_rooms
        return (day, slot, room)

    def cost(self, schedule):
        """
        Oblicza koszt planu:
          - Kara za konflikt: jeżeli w tym samym (dzień, slot) przypisano
            tę samą klasę (oddział) lub nauczyciela lub salę.
          - Bonus: premiuje, gdy kolejne lekcje tego samego przedmiotu są obok siebie
            oraz gdy plan ma niewiele luk (okienek) w ciągu dnia.
        Niższy koszt = lepszy plan.
        """
        conflict_penalty = 10.0
        bonus_adjacent = -1.0
        bonus_gap = -1.0
        
        total_cost = 0.0
        # Mapa: (day, slot) -> lista indeksów lekcji
        schedule_map = {}
        for i, action in enumerate(schedule):
            assign = self.decode_assignment(action)
            key = (assign[0], assign[1])
            if key not in schedule_map:
                schedule_map[key] = []
            schedule_map[key].append(i)
        
        # Sprawdzenie konfliktów
        for key, indices in schedule_map.items():
            if len(indices) > 1:
                # Dla każdej pary konfliktujących lekcji, dodajemy karę.
                for i in indices:
                    for j in indices:
                        if i >= j:
                            continue
                        lesson_i = self.lessons[i]
                        lesson_j = self.lessons[j]
                        # Jeżeli ta sama klasa lub ten sam nauczyciel lub przypisana sala (na poziomie slotu) – konflikt.
                        if lesson_i[0] == lesson_j[0] or lesson_i[1] == lesson_j[1]:
                            total_cost += conflict_penalty
        # Bonusy za strukturę – dla każdego dnia:
        for day in range(NUM_DNI):
            # Zbierz wszystkie lekcje w danym dniu
            day_indices = []
            for i, action in enumerate(schedule):
                assign = self.decode_assignment(action)
                if assign[0] == day:
                    day_indices.append((assign[1], self.lessons[i][2]))  # (slot, subject)
            if not day_indices:
                continue
            day_indices.sort(key=lambda x: x[0])
            # Bonus za kolejne lekcje tego samego przedmiotu
            for i in range(1, len(day_indices)):
                if day_indices[i][1] == day_indices[i-1][1]:
                    total_cost += bonus_adjacent
            # Bonus za spójność: mniejsze luki między pierwszym a ostatnim slotem
            slots = [x[0] for x in day_indices]
            gap = (max(slots) - min(slots) + 1) - len(slots)
            total_cost += bonus_gap * gap
        return total_cost

    def simulated_annealing(self, initial_temp=100.0, final_temp=1.0, alpha=0.99, max_iter=10000):
        current_schedule = self.random_schedule()
        current_cost = self.cost(current_schedule)
        best_schedule = list(current_schedule)
        best_cost = current_cost
        temp = initial_temp
        iter = 0
        while temp > final_temp and iter < max_iter:
            # Wylosuj sąsiedni plan – zmień losowy element
            new_schedule = list(current_schedule)
            idx = random.randrange(self.num_lessons)
            new_schedule[idx] = random.randrange(self.action_space)
            new_cost = self.cost(new_schedule)
            delta = new_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_schedule = new_schedule
                current_cost = new_cost
                if current_cost < best_cost:
                    best_schedule = list(current_schedule)
                    best_cost = current_cost
            temp *= alpha
            iter += 1
        print(f"Simulated annealing zakończone po {iter} iteracjach. Best cost: {best_cost:.2f}")
        return best_schedule

    def generate_plan(self):
        schedule = self.simulated_annealing()
        # Zapisz przypisania jako listę dekodowanych wyników
        assignments = [self.decode_assignment(a) for a in schedule]
        self.assignments = assignments
        return assignments

# -------------------------------------
# Funkcja zapisu planu do bazy danych (backend)
# -------------------------------------

def save_plan_to_db(generator):
    connection = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"]
    )
    try:
        with connection.cursor() as cursor:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {PLAN_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nauczyciel_id INT,
                oddzial_id INT,
                przedmiot_id INT,
                day INT,
                slot INT,
                room INT
            );
            """
            cursor.execute(create_sql)
            for i, assign in enumerate(generator.assignments):
                if assign is None:
                    continue
                day, slot, room = assign
                lesson = generator.lessons[i]
                nauczyciel_id, oddzial_id, przedmiot_id = lesson
                insert_sql = f"""
                INSERT INTO {PLAN_TABLE} (nauczyciel_id, oddzial_id, przedmiot_id, day, slot, room)
                VALUES (%s, %s, %s, %s, %s, %s);
                """
                cursor.execute(insert_sql, (nauczyciel_id, oddzial_id, przedmiot_id, day, slot, room))
        connection.commit()
        print(f"Plan zapisany do bazy w tabeli '{PLAN_TABLE}'.")
    finally:
        connection.close()

# -------------------------------------
# Funkcja pomocnicza do wyświetlania planu w tabelce
# -------------------------------------
def print_plan(generator):
    def find_by_id(lst, id_val):
        for item in lst:
            if item["ID"] == id_val:
                return item
        return None

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    header = f"{'Idx':<5} {'Teacher':<25} {'Class':<10} {'Subject':<15} {'Day':<10} {'Slot':<6} {'Room':<15}"
    print(header)
    print("-" * len(header))
    for i, assign in enumerate(generator.assignments):
        if assign is None:
            continue
        teacher = find_by_id(generator.nauczyciele, generator.lessons[i][0])
        oddzial = find_by_id(generator.oddzialy, generator.lessons[i][1])
        subject = find_by_id(generator.przedmioty, generator.lessons[i][2])
        room = generator.sale[assign[2]]
        day_name = days[assign[0]] if assign[0] < len(days) else str(assign[0])
        teacher_name = (teacher["Imie"] + " " + teacher["Nazwisko"]) if teacher else "N/A"
        class_name = oddzial["Nazwa"] if oddzial else "N/A"
        subject_name = subject["Nazwa"] if subject else "N/A"
        room_name = room["Nazwa"] if room else "N/A"
        print(f"{i:<5} {teacher_name:<25} {class_name:<10} {subject_name:<15} {day_name:<10} {assign[1]:<6} {room_name:<15}")

# -------------------------------------
# Główna funkcja
# -------------------------------------
def main():
    data = load_data_from_db()
    generator = PlanGenerator(data)
    print("Action space size:", generator.action_space)
    print("Generowanie planu...")
    assignments = generator.generate_plan()
    print("\nWygenerowany plan lekcji:")
    print_plan(generator)
    save_plan_to_db(generator)

if __name__ == "__main__":
    main()
