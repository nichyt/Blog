from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
import werkzeug.security
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, Comments_form
from flask_gravatar import Gravatar
import cryptography
from urllib.parse import urlparse, urljoin
from functools import wraps
from flask_gravatar import Gravatar


day = date

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

## Gravatar picture
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

##CONFIGURE TABLES
with app.app_context():
    class User(UserMixin, db.Model):
        __tablename__ = "users"
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(100), unique=True)
        password = db.Column(db.String(100))
        name = db.Column(db.String(100))
        posts = relationship("BlogPost", back_populates="author")
        comments = relationship("Comment", back_populates="comment_author")


    class BlogPost(db.Model):
        __tablename__ = "blog_posts"
        id = db.Column(db.Integer, primary_key=True)
        author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
        author = relationship("User", back_populates="posts")
        title = db.Column(db.String(250), unique=True, nullable=False)
        subtitle = db.Column(db.String(250), nullable=False)
        date = db.Column(db.String(250), nullable=False)
        body = db.Column(db.Text, nullable=False)
        img_url = db.Column(db.String(250), nullable=False)
        comments = relationship("Comment", back_populates="parent_post")


    class Comment(db.Model):
        __tablename__ = "comments"
        id = db.Column(db.Integer, primary_key=True)
        post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
        author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
        parent_post = relationship("BlogPost", back_populates="comments")
        comment_author = relationship("User", back_populates="comments")
        text = db.Column(db.Text, nullable=False)


    #db.create_all()

def is_safe_redirect_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )

def get_safe_redirect(url):
    if url and is_safe_redirect_url(url):
        return url

    url = request.referrer
    if url and is_safe_redirect_url(url):
        return url

    return "/"

#Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

## LOGIN
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()


    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register',methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        hash_and_salted_password = werkzeug.security.generate_password_hash(form.password.data, method='pbkdf2:sha256',
                                                                            salt_length=8)
        try:
            new_user = User()
            new_user.email = form.email.data
            new_user.password = hash_and_salted_password
            new_user.name = form.name.data

            db.session.add(new_user)
            db.session.commit()

        except:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        login_user(new_user)
        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login',methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email entered.
        user = User.query.filter_by(email=email).first()

        #Check stored password hash against entered password hashed.

        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            login_user(user)
            flash(f'Welcome {user.name}')
            return redirect(get_safe_redirect(url_for("get_all_posts", name="Niclas")))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():

    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def show_post(post_id):
    form = Comments_form()
    comments = Comment.query.all()
    requested_post = BlogPost.query.get(post_id)

    for mail in comments:
        print (mail.comment_author.email)

    # post_to_delete = Comment.query.get(1)
    # db.session.delete(post_to_delete)
    # db.session.commit()

    if form.validate_on_submit():
        print("TESTAR")
        test = requested_post
        print(current_user)
        new_comment = Comment()
        new_comment.parent_post = requested_post
        new_comment.comment_author = current_user
        new_comment.text = form.comment_text.data

        db.session.add(new_comment)
        db.session.commit()

        return redirect(url_for("show_post", post_id=post_id))

    return render_template("post.html", form=form, post=requested_post, all_comments=comments, current_user=current_user, test="hyttbro@gmail.com")

@app.route("/about")
@login_required
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():

        new_post = BlogPost()
        new_post.title = form.title.data
        new_post.subtitle = form.subtitle.data
        new_post.date = day.today().strftime("%B %d, %Y")
        new_post.body = form.body.data
        new_post.img_url = form.img_url.data
        new_post.author_id = current_user.id

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author_id = post.author
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id, current_user=current_user))

    return render_template("make-post.html", form=edit_form, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts', current_user=current_user))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
