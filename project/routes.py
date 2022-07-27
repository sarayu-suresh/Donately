import email
from email.mime import image
from fileinput import filename
import os
import secrets
from PIL import Image
from datetime import datetime, date
from flask import render_template, url_for,flash, redirect, request, abort
from project import app,db,bcrypt,mail
from project.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, SearchForm, RequestResetForm, ResetPasswordForm, ConnectForm
from project.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/home")
def home():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    posts = Post.query
    for post in posts:
        if post.expiry_date:
            if post.expiry_date < datetime.today():
                db.session.delete(post)
                db.session.commit()
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=15)
    return render_template("home.html", posts=posts, form=form)
    

@app.route("/search", methods=['POST'])
def search():
    form = SearchForm()
    posts = Post.query
    if form.validate_on_submit():
        if form.types.data == '3':
            posts = posts.filter(Post.title.like('%'+form.item.data+'%'))
            posts = posts.order_by(Post.title).all()
        elif form.types.data =='2':
            posts = posts.filter(Post.title.like('%'+form.item.data+'%')).filter(Post.type=='2')
            posts = posts.order_by(Post.title).all()
        elif form.types.data =='1':
            posts = posts.filter(Post.title.like('%'+form.item.data+'%')).filter(Post.type=='1')
            posts = posts.order_by(Post.title).all()
        return render_template("search.html", form=form, posts=posts)
    else:
        return redirect(url_for('home'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created successfully! Proceed to log in!', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Login Unsuccessful! Please Check Username and Email', 'danger')
    return render_template('login.html', title='Log In', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash(f'Account updated successfully!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/'+ current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    users =User.query.all()
    if form.validate_on_submit():
        post = Post(title=form.title.data, expiry_date=form.expiry_date.data, content=form.content.data, contact=form.contact.data, location=form.location.data, type=form.type.data, author=current_user)
        if form.pic.data:
            pic_file = save_picture(form.pic.data)
            post.img_file = pic_file
        db.session.add(post)
        db.session.commit()
        for user in users: 
            if user!=current_user:
                msg = Message(
                        'Donately',
                        sender='19br12556@rit.ac.in',
                        recipients = [user.email]
                    )
                msg.body = f'''Check out the new item posted by {current_user.username} in Donately!
                '''
                mail.send(msg)
        flash(f'Post Created Successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form,users=users, legend='New Post')

@app.route("/post/<int:post_id>")
def post(post_id):
    form = SearchForm()
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post, form=form)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        post.contact=form.contact.data
        post.location=form.location.data
        post.expiry_date=form.expiry_date.data
        post.type=form.type.data
        if form.pic.data:
            pic_file = save_picture(form.pic.data)
            post.img_file = pic_file
        db.session.commit()
        flash(f'Post Updated Successfully!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.contact.data = post.contact
        form.location.data = post.location
        form.expiry_date.data = post.expiry_date
        form.type.data = post.type  
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash(f'Post Deleted Successfully!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=3)
    return render_template("user_posts.html", posts=posts, form=form, user=user)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='19br12556@rit.ac.in',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/post/<int:post_id>/connect")
@login_required
def connect_post(post_id):
    post = Post.query.get_or_404(post_id)
    user = post.author
    msg = Message('Donately',
                  sender='19br12556@rit.ac.in',
                  recipients=[user.email])
    msg.body = f'''{current_user.username} is interested in your item: {post.title} posted at Donately!
    Connect with user at {current_user.email}
                '''
    mail.send(msg)
    flash(f'Notified Owner about your interest!', 'success')
    return redirect(url_for('post', post_id=post.id))
