from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user
from tmdbv3api import TMDb
from myproject.models import User, Reviews, Watchlist
from myproject import db, app
from myproject.forms import LoginForm, RegistrationFrom, UpdateUserForm, ReviewsForm
from myproject.picture_handler import add_profile_pic
# from tmdbv3api import Movie
import requests

# app = Flask(__name__)

api_key = 'd02af6c7dd1f2fd4f2f426fadb5ee4b0'
api_url = 'https://api.themoviedb.org/3/movie/top_rated?api_key=' + api_key + '&language=en-US&page=1'

# noinspection SpellCheckingInspection
tmdb = TMDb()
tmdb.api_key = api_key
tmdb.language = 'en'
tmdb.debug = True


# @app.route()
def generate_url(page_no):
    r = requests.get(
        'https://api.themoviedb.org/3/movie/top_rated?api_key=' + api_key + '&language=en-US&page=' + str(page_no))
    return r


@app.route('/')
def home():
    r = requests.get('https://api.themoviedb.org/3/trending/all/week?api_key=d02af6c7dd1f2fd4f2f426fadb5ee4b0')
    movie_data = {}
    if r.status_code == 200:
        data = r.json()['results']
        for i in data:
            if i['media_type'] == 'movie':
                movie_data[i['id']] = i['poster_path']
    return render_template('home.html', movie_data=movie_data)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You Logged Out!")
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user.check_password(form.password.data) and user is not None:
            login_user(user)
            flash('Login Successful!')

            next = request.args.get('next')

            if next is None or not next[0] == '/':
                next = url_for('index', page_no=1)

            return redirect(next)
        else:
            flash('Invalid Credentials!')
            return redirect('login')

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationFrom()

    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks for Registration!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateUserForm()

    if form.validate_on_submit():
        print(form)
        if form.profile_image.data:
            username = current_user.username
            pic = add_profile_pic(form.profile_image.data, username)
            current_user.profile_image = pic

        if form.user_bio.data:
            current_user.user_bio = form.user_bio.data

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('User Account Updated')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.user_bio.data = current_user.user_bio

    profile_image = url_for('static', filename='profile_pics/' + current_user.profile_image)
    return render_template('account.html', profile_image=profile_image, form=form)


@app.route('/reviews/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def reviews(movie_id):
    form = ReviewsForm()
    movieid = str(movie_id)
    r = requests.get(
        "https://api.themoviedb.org/3/movie/" + movieid + "?api_key=d02af6c7dd1f2fd4f2f426fadb5ee4b0"
                                                          "&append_to_response"
                                                          "=credits")
    if r.status_code == 200:
        title = r.json()['title']
        poster_path = r.json()['poster_path']

    if form.validate_on_submit():
        review_post = Reviews(review_text=form.review_text.data, movie_id=movie_id, movie_title=title,
                              user_id=current_user.id)
        db.session.add(review_post)
        db.session.commit()
        print(review_post)
        flash('Review Posted!')
        return redirect(url_for('view_reviews'))

    return render_template('reviews.html', movie_id=movieid, title=title, poster_path=poster_path, form=form)


@app.route('/view_reviews')
@login_required
def view_reviews():
    page = request.args.get('page', 1, type=int)
    review_post = Reviews.query.order_by(Reviews.review_date.desc()).paginate(page=page, per_page=10)

    return render_template('view_reviews.html', review_post=review_post)


@app.route('/members')
def members():
    members_username = User.query.order_by(User.username)
    # members_profile_pic = User.query.(User.profile_image)
    return render_template('members.html', members_username=members_username)


# @app.route('/films')
# @login_required
# def basic_index():
#    page_no = 1
#    r = generate_url(page_no)
#    if r.status_code == 200:
#        data = r.json().get('results', [])
#        movies = {r['id']: r for r in data}
#        movies_keys = movies.keys()
#    return render_template('base2.0.html', movies_keys=movies_keys, movies=movies, page_no=page_no)


@app.route('/films/<int:page_no>')
@login_required
def index(page_no):
    if page_no <= 0:
        page_no = 1
    else:
        page_no = page_no
    r = generate_url(page_no)
    if r.status_code == 200:
        data = r.json().get('results', [])
        movies = {r['id']: r for r in data}
        movies_keys = movies.keys()
    return render_template('base2.0.html', movies_keys=movies_keys, movies=movies, page_no=page_no)


def generate_recommendations_url(movieid):
    r = requests.get('https://api.themoviedb.org/3/movie/' + movieid +
                     '/recommendations?api_key=d02af6c7dd1f2fd4f2f426fadb5ee4b0&language=en-US&page=1')
    if r.status_code == 200:
        data = r.json().get('results', [])
        movies = {r['id']: r for r in data}

    return movies


@app.route('/movie_page/<int:movieid>')
@login_required
def display_movie_info(movieid):
    if movieid is not None:
        movie_id = str(movieid)
        recommendations_data = generate_recommendations_url(movie_id)
    else:
        return redirect('data_error.html')

    r = requests.get(
        "https://api.themoviedb.org/3/movie/" + movie_id + "?api_key=d02af6c7dd1f2fd4f2f426fadb5ee4b0"
                                                           "&append_to_response"
                                                           "=credits")

    if r.status_code == 200:
        # data = r.json().get('results', [])
        # movies = {r['id']: r for r in data}
        # movies_keys = movies.keys()
        crew_data = r.json()['credits']['crew']
        crew = {r['job']: r for r in crew_data}
        # print(crew)
        for i in crew:
            if i == 'Director':
                director_name = crew[i]['name']
                person_id = crew[i]['id']

        title = r.json()['title']
        overview = r.json()['overview']
        if r.json()['backdrop_path'] is not None:
            backdrop_path = 'https://image.tmdb.org/t/p/original/' + r.json()['backdrop_path']
        else:
            backdrop_path = " "
        vote_average = r.json()['vote_average']
        release_date = r.json()['release_date']
        vote_count = r.json()['vote_count']
        poster = r.json()['poster_path']
    return render_template('movie_page.html', person_id=person_id, director_name=director_name, poster=poster,
                           title=title, overview=overview, backdrop_path=backdrop_path,
                           vote_average=vote_average, release_date=release_date, vote_count=vote_count,
                           recommendations_data=recommendations_data, movie_id=movie_id)


@app.route('/person_details/<int:person_id>')
@login_required
def display_person_details(person_id):
    if person_id is not None:
        person_id = str(person_id)
    else:
        return redirect('data_error.html')
    res = requests.get('https://api.themoviedb.org/3/person/' + person_id + '?api_key=d02af6c7dd1f2fd4f2f426fadb5ee4b0'
                                                                            '&language=en-US&append_to_response=credits')
    movies_data = res.json()['credits']['crew']
    movie_dict = {}
    for movie_index in movies_data:
        if movie_index['job'] == 'Director':
            movie_dict[movie_index['id']] = movie_index['poster_path']
    person_details = res.json()
    person_name = person_details['name']
    also_known_as = person_details['also_known_as']
    biography = person_details['biography']
    birthday = person_details['birthday']
    place_of_birth = person_details['place_of_birth']
    popularity = person_details['popularity']
    profile_path = 'https://image.tmdb.org/t/p/original/' + person_details['profile_path']
    return render_template('person_details.html', person_name=person_name, also_known_as=also_known_as,
                           biography=biography, birthday=birthday, place_of_birth=place_of_birth,
                           popularity=popularity, profile_path=profile_path, movie_dict=movie_dict)


def search_all(query_string):
    r = requests.get('https://api.themoviedb.org/3/search/multi?query="' + query_string +
                     '"&api_key=d02af6c7dd1f2fd4f2f426fadb5ee4b0&language=en-US')
    if r.status_code == 200:
        search_data = r.json()['results']

    return search_data


@app.route('/search', methods=['GET', 'POST'])
def search():
    keyword_ = request.form['keyword']
    query_string = keyword_.replace(' ', '+')
    movie_data = {}
    person_data = {}
    search_data = search_all(query_string)
    for i in search_data:
        if i['media_type'] == 'movie':
            movie_data[i['id']] = i['title']
        elif i['media_type'] == 'person':
            person_data[i['id']] = i['name']
    return render_template('search.html', query_string=query_string, movie_data=movie_data, person_data=person_data)


@app.route('/watchlist')
@login_required
def watchlist():
    print(current_user.id)
    watchlist_user = Watchlist.query.filter_by(user_id=current_user.id)
    movie_data = {}
    for list in watchlist_user:
        movie_id = str(list.movie_id)
        r = requests.get(
            "https://api.themoviedb.org/3/movie/" + movie_id + "?api_key=d02af6c7dd1f2fd4f2f426fadb5ee4b0"
                                                               "&append_to_response"
                                                               "=credits")
        if r.status_code == 200:
            title = r.json()['title']
            poster_path = r.json()['poster_path']
            movie_data[movie_id] = [title, poster_path]

    return render_template('watchlist.html', movie_data=movie_data)


@app.route('/add_to_watchlist/<int:movie_id>')
def add_to_watchlist(movie_id):
    watchlist_user = Watchlist(movie_id=movie_id, user_id=current_user.id)
    db.session.add(watchlist_user)
    db.session.commit()
    flash('Added to Watchlist')
    return redirect(url_for('watchlist'))


if __name__ == '__main__':
    app.run(debug=True)  # host='0.0.0.0', port=5000,
