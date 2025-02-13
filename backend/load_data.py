import pymysql
from config import DB_CONFIG

def load_data_from_db():
    """
    Łączy się z bazą MySQL i pobiera dane:
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
