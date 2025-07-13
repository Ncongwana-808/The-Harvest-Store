import os
from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_user(username, email, password):
    # Hash the password using SHA-256
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    response = supabase.table("users").insert({
        "username": username,
        "email": email,
        "password": hashed_password
    }).execute()
    return response
