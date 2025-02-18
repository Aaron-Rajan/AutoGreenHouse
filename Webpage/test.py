import pymysql

# AWS RDS MySQL Configuration
DB_USER = "admin"
DB_PASSWORD = "400321812"
DB_HOST = "ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com"
DB_NAME = "ssigdata"

try:
    # Connect to MySQL
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

    print("✅ Connected to MySQL!")

    with connection.cursor() as cursor:
        # Select all records from sensor_data table
        cursor.execute("SELECT * FROM sensor_data;")
        rows = cursor.fetchall()

        if rows:
            print("\n📊 Data in 'sensor_data' table:")
            for row in rows:
                print(row)
        else:
            print("\n⚠ No data found in 'sensor_data'.")

    connection.close()

except pymysql.err.OperationalError as e:
    print(f"❌ Connection failed: {e}")
except Exception as e:
    print(f"⚠ Unexpected error: {e}")
