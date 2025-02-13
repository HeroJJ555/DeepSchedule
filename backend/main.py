from sqlalchemy import create_engine

DATABASE_URL = "jdbc:mysql://u5_AF6h3cTZj3:f.AY5y6GmUtdCD5Sx1%3D.bByx@193.111.249.78:3306/s5_deepschedule"

engine = create_engine(DATABASE_URL)

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("Połączenie udane, wynik zapytania:", result.fetchone())
    except Exception as e:
        print("Błąd podczas łączenia z bazą danych:", e)

if __name__ == "__main__":
    test_connection()
