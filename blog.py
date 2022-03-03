from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask import request


# With this lines we configurate our MySql database with flask
app = Flask(__name__)
app.secret_key = "redkoi"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "redkoiblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


class LoginForm(Form):
    username = StringField("Username:")
    password = PasswordField("Password: ")


# Creating user register form with WTForms
class RegisterForm(Form):
    name = StringField("Your Name:",
                       validators=[validators.length(min=1), validators.DataRequired("Please Enter Your Name.")])
    username = StringField("Your Username:",
                           validators=[validators.length(min=1), validators.DataRequired("Please Enter an Username.")])
    mail = StringField("Your E-mail:", validators=[validators.Email("Please Enter a Valid E-mail."),
                                                   validators.DataRequired("Please Enter an E-mail.")])
    password = PasswordField("Your Password:", validators=[
        validators.DataRequired("Please Enter a Password."),
        validators.EqualTo(fieldname="confirm", message="Your password is doesn't match.")])
    confirm = PasswordField("Please Enter Your Password Again:")


# this function shows page which will seems first when the site requested(the main page)
@app.route("/")
def index():
    return render_template("index.html")  # with this line i used my 'index' named html code


# this function shows you an page when site got /creator request
@app.route("/creator")
def creator():
    return "Made by RedKoi"


# this function will be our decorator function to use it on checking logged in for access to dashboard
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login or sign in before.")
            return redirect(url_for("login"))

    return decorated_function


# function for dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    request = "select * from articles where author = %s"
    result = cursor.execute(request, (session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")


# Function for allowing users to log in them accounts if their login indexes matches with user info's on the db
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        req = "Select * From user where username = %s"
        result = cursor.execute(req, (username,))
        if result != 0:
            data = cursor.fetchone()
            real_password = data["password"]
            real_username = data["username"]
            if sha256_crypt.verify(password_entered, real_password) and real_username == username:
                flash("Login is succeed!")
                session["logged_in"] = True  # this line will make site logged in session
                session["username"] = username
                return redirect(url_for("index"))
            elif sha256_crypt.verify(password_entered, real_password) == False and real_username != username:
                flash("There is not such an user.")
                return redirect(url_for("login"))
            else:
                flash("Your password is incorrect.")
                return redirect(url_for("login"))
        else:
            flash("There is not such an user.")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)


# Function will allow user to log out if user logged in
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# Function for adding register form on website
@app.route("/register", methods=["GET", "POST"])  # the Method used for getting and posting requests
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        mail = form.mail.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        req = "Insert into user(name,username,mail,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(req, (name, username, mail, password))
        mysql.connection.commit()
        cursor.close()
        flash("Your register is succeed!",
              "danger")  # we used flash function which we import for flashing message when register succeed
        return redirect(url_for("login"))  # if we get new user register(post request) we will turn back to main page
    else:
        return render_template("register.html", form=form)  # otherwise(get request) we will see register page


# this function is for when we get /about request it will show you about page
@app.route("/about")
def about():
    return render_template("about.html")


# this function will allow us to get details from articles
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    request = "Select * from articles where id = %s"
    result = cursor.execute(request, (id,))
    if result > 0:
        article1 = cursor.fetchone()
        return render_template("article.html", article=article1)
    else:
        return render_template("article.html")


# this function is for when we get /articles request it will show you article page
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    request = "select * from articles"
    result = cursor.execute(request)
    if result > 0:
        article = cursor.fetchall()
        return render_template("articles.html", article=article)
    else:
        return render_template("articles.html")
    return render_template("about.html")


# function for adding article
@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        req = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(req, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Succesfully Added!")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form=form)

#for edit articles
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        request1 = "SELECT  * FROM articles WHERE id=%s AND author = %s"
        result = cursor.execute(request1,(id,session["username"]))
        if result==0:
            flash("There is not such an article or you dont have permission to do that!")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)

    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        request = "UPDATE articles SET title = %s AND content = %s WHERE id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(request,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Updated successfully!")
        return redirect(url_for("dashboard"))
# for deleting articles
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    request = "SELECT * FROM articles WHERE author = %s and id = %s"
    result = cursor.execute(request,(session["username"],id))
    if result > 0:
        req2 = "DELETE FROM articles WHERE id = %s"
        cursor.execute(req2,(id,))
        mysql.connection.commit()
        flash("Deleted successfully!")
        return redirect(url_for("dashboard"))
    else:
        flash("There is not such an article or you dont have permission to do!")
        return redirect(url_for("index"))

# form for articles
class ArticleForm(Form):
    title = StringField("Header", validators=[validators.length(min=1, max=100)])
    content = TextAreaField("Content", validators=[validators.length(min=10)])


# Thats a kind of complicated part. I suggest you to make a quick search about this block of code.
if __name__ == "__main__":
    app.run(debug=True)
