from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'


class Blog(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180))
    body = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    published_date = db.Column(db.DateTime)

    def __init__(self, title, body, owner, published_date=None ):
        self.title = title
        self.body = body
        self.owner=owner
        if published_date is None:
            published_date = datetime.utcnow()
        self.published_date = published_date

    def is_valid(self):
        
        if self.title and self.body :
            return True
        else:
            return False
    

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120))
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self,username,password):
        self.username = username
        self.pw_hash = make_pw_hash(password)   
    
    

@app.route("/", methods=['POST','GET'])
def index():
    users=User.query.all()
    return render_template('index.html', users=users)


@app.route("/blog")
def display_blog():
    entry_id = request.args.get('id')  
    user_id=request.args.get('userid')
    posts = Blog.query.order_by(Blog.published_date.desc())
    if (entry_id):
        post = Blog.query.filter_by(id=entry_id).first()
        return render_template('newpost.html',title="Blog",post=post, posts=posts,
        published_date=post.published_date, user_id=post.owner_id)
    if (user_id):
        entries=Blog.query.filter_by(owner_id=user_id).all()
        return render_template('singleUser.html',entries=entries)
    else:  
        return render_template('blog.html', posts = posts)
 

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    title_error = ''
    body_error = ''
    existing_user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        new_title = request.form['title']
        new_body = request.form['body']

        new_entry = Blog(new_title, new_body, existing_user)
        
        if (new_title == "") or (new_body == "") :
            title_error="please fill the title"
            body_error="please fill the body"
            return render_template('newpost.html',
                title="Create new blog entry",
                new_title=new_title,
                new_body=new_body, title_error=title_error,body_error=body_error)

        if ((not title_error) or (not body_error)):
            db.session.add(new_entry)
            db.session.commit()

            url = "/blog?id=" + str(new_entry.id)
            return redirect(url)

    return render_template('newpost.html',title="Create new blog entry",
                title_error=title_error,body_error=body_error)
        
@app.before_request
def require_login():
    allowed_routes = ['login','display_blog','index','signup']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User.query.filter_by(username=username).first()

        if (username == "") or (password == "") :
            login_error="Invalid username and password"
            return render_template('login.html',
                username=username,password=password,login_error=login_error)

        elif new_user and check_pw_hash(password, new_user.pw_hash):
            session['username']=username 
            flash("Logged in")         
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'error')
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

    
        existing_user = User.query.filter_by(username=username).first()
        
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = new_user.username
            return redirect("/newpost")
        else:
            return "<h1>Invalid user</h1>"    
    return render_template('signup.html')       

@app.route('/logout')
def logout():

        del session['username']
        return redirect('/blog')
     


if __name__ == '__main__':

    app.run()
