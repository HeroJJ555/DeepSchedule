import pymysql

def initialize_database():
    host = '193.111.249.78'
    user = 'u5_AF6h3cTZj3'
    password = 'f.AY5y6GmUtdCD5Sx1=.bByx'
    database = 's5_deepschedule'
    port = 3306
    create_tables_queries = [
        """
        CREATE TABLE IF NOT EXISTS Przedmiot (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Nazwa VARCHAR(100) NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Nauczyciel (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Imie VARCHAR(100) NOT NULL,
            Nazwisko VARCHAR(100) NOT NULL,
            Rola ENUM('dyrektor','nauczyciel','pedagog','pedagog specjalny','psycholog','wicedyrektor') NOT NULL,
            GodzinyDostepnosci VARCHAR(255),
            Etat ENUM('pelen','czesc') NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Oddzial (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Nazwa VARCHAR(50) NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Sala (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Nazwa VARCHAR(100) NOT NULL,
            Przeznaczenie ENUM('komputerowa','lekcyjna','chemiczna','fizyczna','biologiczna','wf','inne') NOT NULL,
            GodzinyDostepnosci VARCHAR(255)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS NauczycielOddzialPrzedmiot (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            NauczycielID INT NOT NULL,
            OddzialID INT NOT NULL,
            PrzedmiotID INT NOT NULL,
            TygodnioweGodziny INT NOT NULL,  -- Zamiast RoczneGodziny
            FOREIGN KEY (NauczycielID) REFERENCES Nauczyciel(ID),
            FOREIGN KEY (OddzialID) REFERENCES Oddzial(ID),
            FOREIGN KEY (PrzedmiotID) REFERENCES Przedmiot(ID)
        );
        """
    ]

    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Połączono z bazą, resetowanie i tworzenie tabel ...")

        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")

            cursor.execute("DROP TABLE IF EXISTS NauczycielOddzialPrzedmiot")
            cursor.execute("DROP TABLE IF EXISTS Sala")
            cursor.execute("DROP TABLE IF EXISTS Nauczyciel")
            cursor.execute("DROP TABLE IF EXISTS Oddzial")
            cursor.execute("DROP TABLE IF EXISTS Przedmiot")

            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

            for query in create_tables_queries:
                cursor.execute(query)
            connection.commit()

        print("Tabele zostały utworzone od nowa.")

        with connection.cursor() as cursor:
            # 1) Przedmioty
            przedmioty = ["Matematyka", "Polski", "Informatyka", "Biologia"]
            insert_przedmiot = "INSERT INTO Przedmiot (Nazwa) VALUES (%s)"
            for p in przedmioty:
                cursor.execute(insert_przedmiot, (p,))

            # 2) Oddziały
            oddzialy = ["1A", "1B", "2A"]
            insert_oddzial = "INSERT INTO Oddzial (Nazwa) VALUES (%s)"
            for o in oddzialy:
                cursor.execute(insert_oddzial, (o,))

            # 3) Sale
            sale = [
                ("Sala 101", "komputerowa", "Pn-Pt 8:00-16:00"),
                ("Sala 102", "lekcyjna", "Pn-Pt 8:00-15:00"),
                ("Sala 201", "biologiczna", "Pn-Pt 9:00-16:00"),
            ]
            insert_sala = "INSERT INTO Sala (Nazwa, Przeznaczenie, GodzinyDostepnosci) VALUES (%s, %s, %s)"
            for s in sale:
                cursor.execute(insert_sala, s)

            # 4) Nauczyciele
            nauczyciele = [
                ("Jan", "Kowalski", "dyrektor", "Pn-Pt 8:00-13:00", "pelen"),
                ("Anna", "Nowak", "nauczyciel", "Pn-Śr 10:00-15:00", "czesc"),
                ("Maria", "Zielińska", "psycholog", "Pn-Pt 9:00-12:00", "pelen"),
                ("Piotr", "Wójcik", "nauczyciel", "Wt-Czw 8:00-14:00", "pelen"),
                ("Ewelina", "Malinowska", "wicedyrektor", "Pn-Pt 8:00-14:00", "pelen")
            ]
            insert_nauczyciel = """
                INSERT INTO Nauczyciel (Imie, Nazwisko, Rola, GodzinyDostepnosci, Etat)
                VALUES (%s, %s, %s, %s, %s)
            """
            for n in nauczyciele:
                cursor.execute(insert_nauczyciel, n)

            # 5) Relacje w tabeli łącznikowej z kolumną 'TygodnioweGodziny'
            #
            # Przykład: (NauczycielID, OddzialID, PrzedmiotID, TygodnioweGodziny)
            nauczyciel_oddzial_przedmiot = [
                (2, 1, 1, 4),   # Anna Nowak (ID=2) - Matematyka (1) - 1A (1), 4h tygodniowo
                (4, 1, 3, 2),   # Piotr Wójcik (4) - Informatyka (3) - 1A (1), 2h tygodniowo
                (1, 2, 1, 3),   # Jan Kowalski (1) - Matematyka (1) - 1B (2), 3h tygodniowo
                (5, 3, 4, 2)    # Ewelina (5) - Biologia (4) - 2A (3), 2h tygodniowo
            ]
            insert_nop = """
                INSERT INTO NauczycielOddzialPrzedmiot
                (NauczycielID, OddzialID, PrzedmiotID, TygodnioweGodziny)
                VALUES (%s, %s, %s, %s)
            """
            for row in nauczyciel_oddzial_przedmiot:
                cursor.execute(insert_nop, row)

            connection.commit()

        print("Wstawiono przykładowe dane!")

    except pymysql.MySQLError as e:
        print("Błąd podczas tworzenia / wypełniania tabel:", e)
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            print("Połączenie z MySQL zamknięte.")


if __name__ == "__main__":
    initialize_database()
