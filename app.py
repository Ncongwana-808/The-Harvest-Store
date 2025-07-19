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
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            response = create_user(email, password, name)
            if response.user:
                flash("Account created! Please check your email to confirm and then log in.")
                session["user_id"] = response.user.id
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
    cart = session.get("cart", [])
    total_price = sum(item["product"]["price"] * item["quantity"] for item in cart)
    return render_template("cart.html", cart=cart, total_price=total_price)

@app.route("/cart/add/<string:product_id>")  # Changed from <int:product_id>
def add_to_cart(product_id):
    if "user_id" not in session:
        flash("Please log in to add items to your cart.")
        return redirect(url_for("login"))

    response = supabase.table("products").select("*").eq("id", product_id).single().execute()
    product = response.data

    if not product:
        flash("Product not found.")
        return redirect(url_for("home"))

    cart = session.get("cart", [])

    # Prevent duplicate entries
    for item in cart:
        if item["product"]["id"] == product_id:
            flash(f'{product["name"]} is already in your cart.')
            session["cart"] = cart
            return redirect(url_for("home"))

    cart.append({"product": product, "quantity": 1})
    session["cart"] = cart
    flash(f'Added {product["name"]} to cart.')
    return redirect(url_for("home"))

@app.route("/cart/remove/<string:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", [])
    cart = [item for item in cart if item["product"]["id"] != product_id]
    session["cart"] = cart
    flash("Item removed from cart.")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET"])
def checkout():
    cart = session.get("cart", [])
    
    cart_total = 0
    for item in cart:
        product = item["product"]  # no need to fetch again from Supabase
        if product:
            cart_total += float(product["price"]) * item["quantity"]

    return render_template("checkout.html", cart=cart, cart_total=round(cart_total, 2))


@app.route('/payfast', methods=['POST'])
def payfast_payment():
    merchant_id = '10040590'
    merchant_key = '7clmc94m2qx8v'

    name = request.form.get('name')
    address = request.form.get('address')
    amount = request.form.get('amount')

    return_url = 'http://localhost:5000/payment_success'
    cancel_url = 'http://localhost:5000/payment_cancel'
    notify_url = 'http://localhost:5000/payment_notify'

    payfast_url = (
        f"https://sandbox.payfast.co.za/eng/process?"
        f"merchant_id={merchant_id}&"
        f"merchant_key={merchant_key}&"
        f"amount={amount}&"
        f"item_name=Order%20from%20{name}&"
        f"return_url={return_url}&"
        f"cancel_url={cancel_url}&"
        f"notify_url={notify_url}"
    )

    return redirect(payfast_url)


@app.route("/payment_success", methods=["GET"])
def payment_success():
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cart = session.get("cart", [])

    if not cart:
        flash("No items in cart to process.")
        return redirect(url_for("home"))

    try:
        # ✅ Calculate total amount
        total_price = sum(item["product"]["price"] * item.get("quantity", 1) for item in cart)

        # ✅ Insert order with total_amount
        order_data = {
            "user_id": user_id,
            "status": "Paid",
            "total_amount": total_price  # <-- required field
        }
        order_response = supabase.table("orders").insert(order_data).execute()
        order_id = order_response.data[0]["id"]

        # ✅ Insert order items
        for item in cart:
            product_id = item["product"]["id"]
            quantity = item.get("quantity", 1)

            order_item_data = {
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity
            }
            supabase.table("order_item").insert(order_item_data).execute()

        # ✅ Clear cart
        session["cart"] = []

        flash("Payment successful! Your order has been placed.")
        return redirect(url_for("home"))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Something went wrong saving your order: {str(e)}")
        return redirect(url_for("home"))


@app.route("/payment_cancel")
def payment_cancel():
    flash("Payment cancelled. You can continue shopping.")
    return redirect(url_for("cart"))

@app.route("/payment_notify", methods=["POST"])
def payment_notify():
    data = request.form.to_dict()
    print("PayFast Notification:", data)

    # You can add further signature validation and logging here
    return "OK", 200  # PayFast expects a 200 response




@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("landing"))

if __name__ == "__main__":
    app.run(debug=True)
