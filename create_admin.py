from db import connect_to_db, create_user
#is used to create an admin user and to create another user change the username and password below
if __name__ == "__main__":
    conn = connect_to_db()
    # change username & password as you like
    create_user(conn, "admin", "supersecretpassword", is_admin=True)
    print("✅ Admin user created successfully!")
