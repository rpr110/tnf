import mysql.connector

# Replace these values with your actual database credentials
db_config = {
    "host": "faceproof-production-db.c2pyeebkcdqx.eu-west-2.rds.amazonaws.com",
    "user": "admin",
    "password": "QdWeYEk7xD2",
    "database": "FACEPROOF_DB_TEST"
}

db_config2 = {
    "host": "calcot-faceproof-mysql-db.c2pyeebkcdqx.eu-west-2.rds.amazonaws.com",
    "user": "admin",
    "password": "QdWeYEk7xD2",
    "database": "NFACE_DB_TEST"
}

# Establish a connection to the database
try:
    connection = mysql.connector.connect(**db_config)
    connection2 = mysql.connector.connect(**db_config2)
    
    if connection.is_connected():
        print("Connected to MySQL database")

        # Create a cursor to execute SQL queries
        cursor = connection.cursor(dictionary=True)  # Use dictionary=True to fetch results as dictionaries

        # Execute the SELECT query
        query = "SELECT * FROM Faceproof_Logs"
        cursor.execute(query)

        # Fetch all records
        records = cursor.fetchall()

        # Loop through the fetched records
        for record in records:
            print(record)

            # Insert record into the second database
            query2 = """
                INSERT INTO Faceproof_Logs (
                    session_code, endpoint, user_id, company_id,
                    status_id, service_id, status_code, ip_address,
                    output, execution_time, create_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            import random
            # You need to provide the values to be inserted
            values = (
                record["session_code"], f"/{record['endpoint'].split('/')[-1]}", record["user_id"],
                random.randint(1,2), record["status_id"], random.randint(1,2),
                record["status_code"], record["ip_address"], record["output"],
                record["execution_time"], record["create_date"]
            )
            if record["status_id"] !=None and record["service_id"] !=None:
                cursor2 = connection2.cursor()
                cursor2.execute(query2, values)
                connection2.commit()
                cursor2.close()

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connections to MySQL closed")

except mysql.connector.Error as error:
    print("Error while connecting to MySQL:", error)
