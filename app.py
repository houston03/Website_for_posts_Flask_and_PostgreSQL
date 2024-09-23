from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'cairocoders-ednalan'


conn = psycopg2.connect(
        host='localhost',
        dbname='my_db',
        user='postgres',
        password='root',
        port=5432,)


@app.route('/')
def home():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


    if 'loggedin' in session:

        cursor.execute('SELECT * FROM news WHERE user_id = %s', (session['id'],))
        user_news = cursor.fetchall()


        return render_template('home_one.html', username=session['username'], user_news=user_news)


    return redirect(url_for('login'))


@app.route('/')
def home_one():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


    cursor.execute('SELECT * FROM news WHERE user_id = %s', (session['id'],))
    user_news = cursor.fetchall()


    return render_template('home_one.html', user_news=user_news)

@app.route('/about')
def about():
        return render_template('about.html')


@app.route('/one')
def one():
        return render_template('one.html')


@app.route('/two')
def two():
        return render_template('two.html')

'''
@app.route('/three', methods=['GET', 'POST'])
def three():
    dominant_emotion = None
    emotion_score = None
    if request.method == 'POST':
        
        file = request.files['file']
        if file:
            
            img = Image.open(file.stream)
            img = np.array(img)

            
            emo_detector = FER(mtcnn=True)
            dominant_emotion, emotion_score = emo_detector.top_emotion(img)

    return render_template('three.html', dominant_emotion=dominant_emotion, emotion_score=emotion_score)
'''


@app.route('/cont')
def cont():
        return render_template('cont.html')


app.config['DATABASE_URI'] = 'postgresql://user:password@host:port/database'

@app.route('/rating')
def rating():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM news')
    all_news = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("""
            SELECT news_id FROM favorites WHERE user_id = %s
        """, (session['id'],))
        favorite_ids = {row['news_id'] for row in cursor.fetchall()}  # Store favorite news IDs in a set

    # Get the count of favorites for each news article
    cursor.execute("""
        SELECT news_id, COUNT(*) as favorite_count FROM favorites GROUP BY news_id
    """)
    favorite_counts = {row['news_id']: row['favorite_count'] for row in cursor.fetchall()}

    return render_template('rating.html', user_news=all_news, favorite_ids=favorite_ids, favorite_counts=favorite_counts)



@app.route('/add_favorite/<int:news_id>', methods=['POST'])
def add_favorite(news_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if 'loggedin' in session:
        try:
            cursor.execute("INSERT INTO favorites (user_id, news_id) VALUES (%s, %s)",
                           (session['id'], news_id))
            conn.commit()
            flash('Post added to favorites!', 'success')
        except Exception as e:
            flash('This news is already in your favorites.', 'error')
            print(e)

    return redirect(url_for('rating'))  # Redirect back to the rating page


@app.route('/remove_favorite/<int:news_id>', methods=['POST'])
def remove_favorite(news_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if 'loggedin' in session:
        try:
            cursor.execute("DELETE FROM favorites WHERE user_id = %s AND news_id = %s",
                           (session['id'], news_id))
            conn.commit()
            flash('Post removed from favorites!', 'success')
        except Exception as e:
            flash('An error occurred while removing from favorites.', 'error')
            print(e)

    return redirect(url_for('rating'))  # Redirect back to favorites


@app.route('/favorites')
def favorites():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if 'loggedin' in session:
        cursor.execute("""
            SELECT news.* FROM favorites
            JOIN news ON favorites.news_id = news.id
            WHERE favorites.user_id = %s
        """, (session['id'],))
        favorite_news = cursor.fetchall()

        return render_template('favorites.html', user_news=favorite_news)

    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check if "username" and "password" POST requests exist (user submitted form)
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
                username = request.form['username']
                password = request.form['password']
                print(password)

                # Check if account exists using MySQL
                cursor.execute('SELECT * FROM usersreg WHERE username = %s', (username,))
                # Fetch one record and return result
                account = cursor.fetchone()

                if account:
                        password_rs = account['password']
                        print(password_rs)
                        # If account exists in users table in out database
                        if check_password_hash(password_rs, password):
                                # Create session data, we can access this data in other routes
                                session['loggedin'] = True
                                session['id'] = account['id']
                                session['username'] = account['username']
                                # Redirect to home page
                                return redirect(url_for('home'))
                        else:
                                # Account doesnt exist or username/password incorrect
                                flash('Incorrect username/password')
                else:
                        # Account doesnt exist or username/password incorrect
                        flash('Incorrect username/password')

        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check if "username", "password" and "email" POST requests exist (user submitted form)
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
                # Create variables for easy access
                fullname = request.form['fullname']
                username = request.form['username']
                password = request.form['password']
                email = request.form['email']

                _hashed_password = generate_password_hash(password)

                # Check if account exists using MySQL
                cursor.execute('SELECT * FROM usersreg WHERE username = %s', (username,))
                account = cursor.fetchone()
                print(account)
                # If account exists show error and validation checks
                if account:
                        flash('Account already exists!')
                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                        flash('Invalid email address!')
                elif not re.match(r'[A-Za-z0-9]+', username):
                        flash('Username must contain only characters and numbers!')
                elif not username or not password or not email:
                        flash('Please fill out the form!')
                else:
                        # Account doesnt exists and the form data is valid, now insert new account into users table
                        cursor.execute("INSERT INTO usersreg (fullname, username, password, email) VALUES (%s,%s,%s,%s)",
                                       (fullname, username, _hashed_password, email))
                        conn.commit()
                        flash('You have successfully registered!')
        elif request.method == 'POST':
                # Form is empty... (no POST data)
                flash('Please fill out the form!')
        # Show registration form with message (if any)
        return render_template('register.html')


@app.route('/logout')
def logout():
        # Remove session data, this will log the user out
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        # Redirect to login page
        return redirect(url_for('login'))


@app.route('/profile')
def profile():
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check if user is loggedin
        if 'loggedin' in session:
                cursor.execute('SELECT * FROM usersreg WHERE id = %s', [session['id']])
                account = cursor.fetchone()
                # Show the profile page with account info
                return render_template('profile.html', account=account)
        # User is not loggedin redirect to login page
        return redirect(url_for('login'))



@app.route('/create_news', methods=['GET', 'POST'])

def create_news():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'description' in request.form and 'main_text' in request.form and 'note' in request.form:
        description = request.form.get('description', '')
        main_text = request.form.get('main_text', '')
        note = request.form.get('note', '')
        user_id = session['id']

        # Validate data here
        if not description or not main_text:
            flash('Description and main text are required!', 'error')
            return render_template('create_news.html')

        try:
            cursor.execute(
                "INSERT INTO news (description, main_text, note, user_id) VALUES (%s, %s, %s, %s)",
                (description, main_text, note, user_id))
            conn.commit()
            flash('Post created successfully!', 'success')
            return redirect(url_for('home'))  # Redirect to the home or news page
        except Exception as e:
            flash('An error occurred while creating post.', 'error')
            # Optionally log the error
            print(e)

    return render_template('create_news.html')


@app.route('/edit_news/<int:news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST':
        description = request.form.get('description', '')
        main_text = request.form.get('main_text', '')
        note = request.form.get('note', '')

        # Validate data here
        if not description or not main_text:
            flash('Description and main text are required!', 'error')
            return render_template('edit_news.html', news_id=news_id)

        try:
            cursor.execute(
                "UPDATE news SET description=%s, main_text=%s, note=%s WHERE id=%s AND user_id=%s",
                (description, main_text, note, news_id, session['id']))
            conn.commit()
            flash('Pots updated successfully!', 'success')
            return redirect(url_for('home_one'))
        except Exception as e:
            flash('An error occurred while updating Post.', 'error')
            print(e)

    cursor.execute('SELECT * FROM news WHERE id = %s AND user_id = %s', (news_id, session['id']))
    news = cursor.fetchone()

    if not news:
        flash('Post not found or you do not have permission to edit it.', 'error')
        return redirect(url_for('home_one'))

    return render_template('edit_news.html', news=news)

@app.route('/delete_news/<int:news_id>', methods=['POST'])
def delete_news(news_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute("DELETE FROM news WHERE id = %s AND user_id = %s", (news_id, session['id']))
        conn.commit()
        flash('Post deleted successfully!', 'success')
    except Exception as e:
        flash('An error occurred while deleting Post.', 'error')
        print(e)

    return redirect(url_for('home_one'))




