from flask import Flask, render_template, session,request, redirect, url_for, flash
from nlp_utils import extract_order_items
from models import db, bcrypt, User
import os


app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)

@app.route("/")
def landing():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful!")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! You can now log in.")
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/product/<int:id>")
def product_detail(id):
    # Placeholder for product details
    return render_template("product_detail.html", product_id=id)

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


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
