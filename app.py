from dotenv import load_dotenv
import os
load_dotenv()

from flask import Flask, render_template, session, request, redirect, url_for, flash
from nlp_utils import extract_order_items
from supabase_client import create_user, login_user


from supabase import create_client

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print("SUPABASE_URL =", SUPABASE_URL)
print("SUPABASE_KEY =", "Exists" if SUPABASE_KEY else "Missing")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

data = supabase.table("products").select("*").execute()
print("Supabase data:", data)

@app.route("/")
def landing():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            response = login_user(email, password)
            if response.user:
                session["user_id"] = response.user.id
                session["email"] = response.user.email
                flash("Login successful!")
                return redirect(url_for("home"))
            else:
                flash("Login failed. Check credentials.")
        except Exception as e:
            flash(f"Error: {e}")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            response = create_user(email, password)
            if response.user:
                flash("Account created! Please check your email to confirm and then log in.")
                return redirect(url_for("login"))
            else:
                flash("Signup failed.")
        except Exception as e:
            flash(f"Error: {e}")
        return redirect(url_for("signup"))

    return render_template("signup.html")

@app.route("/home")
def home():
    try:
        response = supabase.table("products").select("*").execute()
        print("Supabase response:", response)
        print("Response dir:", dir(response))
        print("Response as dict:", response.__dict__ if hasattr(response, '__dict__') else response)
        products = getattr(response, "data", None)
        if products is None:
            products = response.get("data", []) if isinstance(response, dict) else []
        print("Products:", products)
        if products:
            return render_template("home.html", products=products)
        else:
            flash("No products found.")
            return render_template("home.html", products=[])
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash(f"Error loading products: {e}")
        return render_template("home.html", products=[])
    


@app.route("/product/<string:id>")
def product_detail(id):
    result = supabase.table("products").select("*").eq("id", id).single().execute()
    product = result.data
    return render_template("product_detail.html", product=product)




@app.route("/cart")
def cart():
    if "user_id" not in session:
        flash("Please log in to view your cart.")
        return redirect(url_for("login"))
    return render_template("cart.html")

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        flash("Please log in to proceed to checkout.")
        return redirect(url_for("login"))

    if request.method == "POST":
        order_text = request.form["order_text"]
        items = extract_order_items(order_text)
        if items:
            flash(f"Order items extracted: {items}")
        else:
            flash("No valid order items found.")
        return redirect(url_for("home"))
    return render_template("checkout.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("landing"))

if __name__ == "__main__":
    app.run(debug=True)
