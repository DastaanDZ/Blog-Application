from flask import render_template, request, redirect, url_for, session
from flask import current_app as app

from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt


from application.models import Post
from application.models import User
from application.models import Follow

from application.models import RegisterForm
from application.models import LoginForm

from application.database import db

# from application.models import Article

# @app.route("/", methods=["GET", "POST"])
# def articles():
#     articles = Article.query.all()    
#     return render_template("articles.html", articles=articles)

# @app.route("/articles_by/<user_name>", methods=["GET", "POST"])
# def articles_by_author(user_name):
#     articles = Article.query.filter(Article.authors.any(username=user_name))
#     return render_template("articles_by_author.html", articles=articles, username=user_name)
bcrypt = Bcrypt(app)


@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print('!!!!!!!! LOGIN VALIDATED !!!!!!!!')
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            print('!!!!!!!! USER FOUND !!!!!!!!')
            if bcrypt.check_password_hash(user.password, form.password.data):
                print('!!!!!!!! PASSWORD MATCHED  !!!!!!!!')
                login_user(user)
                print('!!!!!!!! USER LOGGEDIN  !!!!!!!!')
                return redirect(url_for('feed', user_id=user.id))
            else:
                return 'Invalid password'
        else:
            return 'Invalid username or password'
    else:
        # return render_template('login.html')
        return render_template('login.html',form = form, search = False, profile = False, login = True)

@app.route('/logout')
@login_required
def logout():
    # Remove the user_id from the session
    logout_user()
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    print('!!!!!!!!!!!!!!!! I AM IN REGISTER    !!!!!!!!!!!!!!!')
    if form.validate_on_submit():
        print('!!!!!!!!!!!!!!!!!    VALIDATED   !!!!!!!!!!!!!!')
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data,password=hashed_password)
        db.session.add(new_user)
        print('!!!!!!!!!!!!!!!  ADDED TO SESSION    !!!!!!!!!!!!!')
        db.session.commit()
        print('!!!!!!!!!!!!!!!  COMMITED    !!!!!!!!!!!!!')
        return redirect(url_for('login'))
    else:
        print('!!!!!!!! GOING TO REGISTER.HTML  !!!!!!!!!!')
        return render_template('register.html', form=form)

@app.route('/feed/<user_id>')
def feed(user_id):
    # Check if user_id is a valid integer
    if user_id.isdigit():
        user_id = int(user_id)
        # Query the user with the given id and render the template
        user = User.query.get(user_id)
        follows = Follow.query.filter_by(follower_id=user.id).all()
        followed_ids = [follow.followed_id for follow in follows]
        followed_ids.append(user.id)
        posts = Post.query.filter(Post.author_id.in_(followed_ids)).order_by(Post.timestamp.desc()).all()
        return render_template('feed.html', posts=posts, user_id=user_id, user=user)
    else:
        # Return a 404 error if the user id is not a valid integer
        return "Error: Invalid user id", 404


@app.route('/new_post/<int:user_id>', methods=['GET', 'POST'])
@login_required
def new_post(user_id):
    if request.method == 'POST':
        title = request.form['title']
        caption = request.form['caption']
        image_url = request.form['image_url']
        user = User.query.get(user_id)
        if user:
            post = Post(title=title, caption=caption, image_url=image_url, author=user)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('feed', user_id=user_id))
        else:
            return 'User not found'
    else:
        return render_template('new_post.html',user_id=user_id)


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get(post_id)
    if request.method == 'POST':
        title = request.form['title']
        caption = request.form['caption']
        image_url = request.form['image_url']
        post.title = title
        post.caption = caption
        post.image_url = image_url
        db.session.commit()
        return redirect(url_for('feed', user_id=post.author_id))
    else:
        return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    if request.method == 'POST':
        print('!!!!!!!!!! POST REQUEST RECIEVED !!!!!!!!!!!!')
        try:
            # Query the object from the database within a session
            post = Post.query.get(post_id)
            print('!!!!!!!!!! POST QUERIED !!!!!!!!!!!!')

            if post:
                print('!!!!!!!!!! INSIDE IF POST !!!!!!!!!!!!')
                db.session.delete(post)
                print('!!!!!!!!!! DELETE POST SESSNION CREATED !!!!!!!!!!!!')
                db.session.commit()
                print('!!!!!!!!!! DELETE POST CHANGES COMMITTED !!!!!!!!!!!!')
                return redirect(url_for('feed', user_id=post.author_id))
            else:
                return 'Post not found'
        except Exception as e:
            # Handle any exceptions that might occur
            print(e)
            db.session.rollback()
    else:
        print(post_id)
        return render_template('delete_post.html', post_id=post_id)






@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user:
        posts = Post.query.filter_by(author=user).all()
        followers = Follow.query.filter_by(followed_id=user_id).count()
        followed = Follow.query.filter_by(follower_id=user_id).count()
        return render_template('profile.html', user=user, posts=posts, followers=followers, followed=followed, user_id=user_id)
    else:
        return 'User not found'

@app.route('/follow/<int:followed_id>', methods=['GET', 'POST'])
@login_required
def follow(followed_id):
    # Get the current user
    current_user_id = current_user.get_id()
    print(current_user)
    print('!!!!!!!!!!   USER ID OBTAINED  !!!!!!!!!')
    # Check if a follow relationship already exists between the current user and the user to be followed
    follow_relationship = Follow.query.filter_by(follower_id=current_user_id, followed_id=followed_id).first()
    if follow_relationship:
        print('!!!!!!!!!!  RELATIONSHIP FOUND ALREADY A FOLLOWER  !!!!!!!!!')
        # If a follow relationship already exists, delete it
        db.session.delete(follow_relationship)
        print('!!!!!!!!!!  RELATIONSHIP DELETED  !!!!!!!!!')
        db.session.commit()
        print('!!!!!!!!!!  DELETED COMMITED  !!!!!!!!!')
    else:
        print('!!!!!!!!!!  RELATIONSHIP NOT FOUND, NOT A FOLLOWER ALREADY  !!!!!!!!!')
        # If a follow relationship does not exist, create one
        follow_relationship = Follow(follower_id=current_user_id, followed_id=followed_id)
        print('!!!!!!!!!!  RELATIONSHIP FOLLOW CREATEDX  !!!!!!!!!')
        db.session.add(follow_relationship)
        print('!!!!!!!!!!  RELATIONSHIP FOLLOW ADDED  !!!!!!!!!')
        db.session.commit()
        print('!!!!!!!!!!  RELATIONSHIP FOLLOW COMMITTED  !!!!!!!!!')

    print('!!!!!!!!!!  REDIRECTING TO FEED  !!!!!!!!!')
    return redirect(url_for('feed', user_id=current_user_id))

@app.route('/unfollow/<int:user_id>', methods=['GET', 'POST'])
def unfollow(user_id):
    # Get the current user and the user to be unfollowed
    current_user = User.query.get(session['user_id'])
    user_to_unfollow = User.query.get(user_id)

    # Query the Follow object and delete it from the database
    follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_to_unfollow.id).first()
    db.session.delete(follow)
    db.session.commit()

    # Update the number of followers for the user being unfollowed
    user_to_unfollow.followers -= 1
    db.session.commit()

    return redirect(url_for('feed', user_id=current_user.id))

@app.route('/search', methods=['POST'])
def search():
    query = request.form['search-query']
    users = User.query.filter(User.username.contains(query)).all()
    return render_template('search_results.html', users=users, query=query, user_id=current_user.id)

@app.route('/view_profile/<int:user_id>')
def view_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return 'User not found'
    posts = Post.query.filter_by(author_id=user_id).all()
    followers = Follow.query.filter_by(followed_id=user_id).count()
    followed = Follow.query.filter_by(follower_id=user_id).count()
    return render_template('view_profile.html', user=user, posts=posts, followers=followers, followed=followed)

@app.route('/view_followers/<int:user_id>')
def view_followers(user_id):
    user = User.query.get(user_id)
    followers = Follow.query.filter_by(followed_id=user_id).all()
    return render_template('view_followers.html', user=user, followers=followers)

@app.route('/view_following/<int:user_id>')
def view_following(user_id):
    user = User.query.get(user_id)
    following = Follow.query.filter_by(follower_id=user_id).all()
    return render_template('view_following.html', user=user, following=following)

@app.route('/post_detail/<int:post_id>')
def post_detail(post_id):
    # quering the post from database
    post = Post.query.get(post_id)
    if post:
        return render_template('post_detail.html',post=post)
    else:
        return 'Post does not exist anymore'
    