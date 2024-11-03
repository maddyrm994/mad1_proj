# Import necessary libraries and modules
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, redirect, request, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Create a Flask application
app=Flask(__name__)

# Configure the application settings
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "thisisasecretkey"

# Initialize a SQLAlchemy database
db=SQLAlchemy(app)

# Define the User model for the database
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # instead of explicit password data
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(50), nullable=True)
    isadmin = db.Column(db.Boolean, nullable=False, default=False)
    iscreator = db.Column(db.Boolean, nullable=False, default=False)

    # password property
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    # password setting
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    # password checking
    def check_password(self, password):
        return check_password_hash(self.passhash, password)

# Define the Song model for the database
class Song(db.Model):
    __tablename__ = 'song'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    songname = db.Column(db.String(50), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    # storing file path instead of actual file
    songlyrics_path = db.Column(db.String(255), nullable=True)
    songduration = db.Column(db.Time, nullable=False)
    songdateofcreation = db.Column(db.Date, nullable=False)
    playlists = db.relationship('Playlist', backref='song', lazy=True)

# Define the Album model for the database
class Album(db.Model):
  __tablename__ = 'album'
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  albumname = db.Column(db.String(50), nullable=False)
  albumgenre = db.Column(db.String(50), db.ForeignKey('genre.genrename'), nullable=False)
  albumartist = db.Column(db.String(50), nullable=False)
  albumnoofsongs = db.Column(db.Integer, nullable=False, default=0)
  songs  = db.relationship('Song', backref='album', lazy=True)

# Define the Genre model for the database
class Genre(db.Model):
  __tablename__ = 'genre'
  id = db.Column(db.Integer, primary_key=True)
  genrename = db.Column(db.String(50), nullable=False)
  albums = db.relationship('Album', backref='genre', lazy=True)

# Define the Playlist model for the database
class Playlist(db.Model):
    __tablename__ = 'playlist'
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    songid = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True, nullable=False)

# Ensure the database tables are created
with app.app_context():
  db.create_all()
  # Create an admin user if it doesn't exist
  admin = User.query.filter_by(username='admin').first()
  if not admin:
    admin = User(username='admin', password='admin123', name='Admin', isadmin=True, iscreator=True)
    db.session.add(admin)
    db.session.commit()

# Additional models thoughts (commented out for now)
'''
class Artist_Album(db.Model):
  __tablename__='artist_album'
  artist_id=db.Column(db.Integer, db.ForeignKey('artist.artist_id'), primary_key=True)
  album_id=db.Column(db.Integer, db.ForeignKey('album.album_id'))

class Artist_Song(db.Model):
  __tablename__='artist_song'
  artist_id=db.Column(db.Integer, db.ForeignKey('artist.artist_id'), primary_key=True)
  song_id=db.Column(db.Integer, db.ForeignKey('song.song_id'))

class Album_Song(db.Model):
  __tablename__='album_song'
  album_id=db.Column(db.Integer, db.ForeignKey('album.album_id'), primary_key=True)
  song_id=db.Column(db.Integer, db.ForeignKey('song.song_id'))

class Playlist_Song(db.Model):
  __tablename__= 'playlist_song'
  playlist_id=db.Column(db.Integer, db.ForeignKey('playlist.playlist_id'), primary_key=True)
  song_id=db.Column(db.Integer, db.ForeignKey('song.song_id'))

'''

######

'''
@app.route('/')
def home_page():
    return render_template("welcome.html")
'''

# Define a decorator for route functions that require authentication
def auth_required(func):
  @wraps(func)
  def inner(*args, **kwargs):
    if 'user_id' not in session:
      flash('You need to login first.')
      return redirect (url_for('login_page'))
    return func(*args, **kwargs)
  return inner

# Define a decorator for route functions that require admin privileges
def admin_required(func):
  @wraps(func)
  def inner(*args, **kwargs):
    if 'user_id' not in session:
      flash('You need to login first.')
      return redirect (url_for('login_page'))
    user = User.query.get(session['user_id'])
    # prevent unauthorised access
    if not user.isadmin:
      flash('You are not authorised to view this page.')
      return redirect(url_for('index_page'))
    return func(*args, **kwargs)
  return inner

# Define the route for the home page
@app.route('/')
@auth_required
def index_page():
    user = User.query.get(session['user_id'])
    # admin home page
    if user.isadmin:
        return redirect(url_for('admin_page'))
    parameter = request.args.get('parameter')
    search = request.args.get('search')
    # search fucntioning
    if not parameter or not search:
        return render_template("index.html", user=user, albums=Album.query.all())
    if parameter == 'album':
        albums = Album.query.filter(Album.albumname.like('%' + search + '%')).all()
        return render_template('index.html', user=user, albums=albums)
    if parameter == 'song':
        # Assuming you want to filter by song name
        songs = Song.query.filter(Song.songname.like('%' + search + '%')).all()
        # If you want to show albums containing those songs
        albums = [song.album for song in songs]
        return render_template('index.html', user=user, albums=albums)
    return render_template('index.html', user=user, albums=Album.query.all(), songs=Song.query.all())

# Define the route for the admin page
@app.route('/admin')
@admin_required
def admin_page():
    user = User.query.get(session['user_id'])
    # avoid unauthorised viewing
    if not user.isadmin:
        flash('You are not authorised to view this page.')
        return redirect(url_for('index_page'))
    # keeping track of number of users, creators
    creators_count = User.query.filter_by(iscreator=True).count()
    return render_template("admin.html", user=user, users=User.query.all(), songs=Song.query.all(), albums=Album.query.all(), creators_count=creators_count, genres=Genre.query.all())

# Define the route for the profile page
@app.route('/profile')
@auth_required
def profile_page():
  return render_template("profile.html", user=User.query.get(session['user_id']))

# Define the route for updating profile information
@app.route('/profile', methods=['POST'])
@auth_required
def profile_page_post():
    user = User.query.get(session['user_id'])
    username = request.form.get('username')
    name = request.form.get('name')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    # checking validity of bio-data
    if username == '' or password == '' or cpassword == '':
        flash('Username or password cannot be empty.')
        return redirect(url_for('profile_page'))
    if not user.check_password(cpassword):
        flash('Incorrect password.')
        return redirect(url_for('profile_page'))
    if User.query.filter_by(username=username).first() and username != user.username:
        flash('User with this username already exists. Please choose some other username.')
        return redirect(url_for('profile_page'))
    # storing the information after validity check
    user.username = username
    user.name = name
    user.password = password
    db.session.commit()
    flash('Profile updated successfully.')
    return redirect(url_for('profile_page'))

# Define the route for the login page
@app.route('/login')
def login_page():
  return render_template("login.html")

# Define the route for processing login information
@app.route('/login', methods=['POST'])
def login_page_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    # checking validity of login credentials
    if username == '' or password == '':
        flash('Username or Password cannot be empty.')
        return redirect(url_for('login_page'))
    if not user:
        flash('User does not exist.')
        return redirect(url_for('login_page'))
    if not user.check_password(password):
        flash('Incorrect password.')
        return redirect(url_for('login_page'))
    session['user_id'] = user.id
    return redirect(url_for('index_page'))

# Define the route for the registration page
@app.route('/register')
def register_page():
  return render_template("register.html")

# Define the route for processing user registration
@app.route('/register', methods=['POST'])
def register_page_post():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    # checking validity of registration details
    if username == '' or password == '':
        flash('Username or Password cannot be empty.')
        return redirect(url_for('register_page'))
    if User.query.filter_by(username=username).first():
        flash('User with this username already exists. Please choose some other username.')
        return redirect(url_for('register_page'))
    # storing the information after validity check
    user = User(username=username, password=password, name=name)
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered.')
    return redirect(url_for('login_page'))

# Define the route for logging out
@app.route('/logout')
def logout_page():
  session.pop('user_id', None)
  return redirect(url_for('login_page'))

# Define the route for the genres page (admin only)
@app.route('/genres')
@admin_required
def genres_page():
    return render_template('genres.html', user=User.query.get(session['user_id']), users=User.query.all(), songs=Song.query.all(), albums=Album.query.all(), genres=Genre.query.all())

# Define the route for adding a new genre (admin only)
@app.route('/genre/add')
@admin_required
def add_genre_page():
  return render_template('genre/add_genre.html', user=User.query.get(session['user_id']))

# Define the route for processing the addition of a new genre (admin only)
@app.route('/genre/add', methods=['POST'])
@admin_required
def add_genre_page_post():
    name = request.form.get('name')
    # checking validity of genre details
    if name == '':
        flash('Genre name can not be empty.')
        return redirect(url_for('add_genre_page'))
    if len(name) > 50:
        flash('Genre name can not be greater than 50 characters.')
        return redirect(url_for('add_genre_page'))
    # storing genre information after validity check
    genre = Genre(genrename=name)
    db.session.add(genre)
    db.session.commit()
    flash('Genre added successfully.')
    return redirect(url_for('admin_page'))

# Define the route for editing an genre (admin only)
@app.route('/genre/<int:id>/edit')
@admin_required
def edit_genre_page(id):
  return render_template('genre/edit_genre.html', user=User.query.get(session['user_id']), genre=Genre.query.get(id))

# Define the route for processing the edit form for an genre (admin only)
@app.route('/genre/<int:id>/edit', methods=['POST'])
@admin_required
def edit_genre_page_post(id):
    genre = genre.query.get(id)
    name = request.form.get('name')
    # checking genre details for valid updation
    if name == '':
        flash('Genre name can not be empty.')
        return redirect(url_for('edit_genre_page', id=id))
    if len(name) > 50:
        flash('Genre name can not be greater than 50 characters.')
        return redirect(url_for('edit_Genre_page', id=id))
    # updating genre details after validity check
    genre.genrename = name
    db.session.commit()
    flash('Genre updated successfully.')
    return redirect(url_for('admin_page'))

# Define the route for deleting an genre (admin only)
@app.route('/genre/<int:id>/delete')
@admin_required
def delete_genre_page(id):
    genre = Genre.query.get(id)
    if not genre:
        flash('Genre does not exist.')
        return redirect(url_for('admin_page'))
    return render_template('genre/delete_genre.html', user=User.query.get(session['user_id']), genre=genre)

# Define the route for processing the deletion of an genre (admin only)
@app.route('/genre/<int:id>/delete', methods=['POST'])
@admin_required
def delete_genre_page_post(id):
  genre = Genre.query.get(id)
  if not genre:
    flash('Genre does not exist.')
    return redirect(url_for('admin_page'))
  db.session.delete(genre)
  db.session.commit()
  flash('Genre deleted successfully')
  return redirect(url_for('admin_page'))

# Define the route for the albums page (admin only)
@app.route('/albums')
@admin_required
def albums_page():
    return render_template('albums.html', user=User.query.get(session['user_id']), users=User.query.all(), songs=Song.query.all(), albums=Album.query.all())

# Define the route for adding a new album (admin only)
@app.route('/album/add')
@admin_required
def add_album_page():
  return render_template('album/add_album.html', user=User.query.get(session['user_id']))

# Define the route for processing the addition of a new album (admin only)
@app.route('/album/add', methods=['POST'])
@admin_required
def add_album_page_post():
    name = request.form.get('name')
    genre = request.form.get('genre')
    artist = request.form.get('artist')
    # checking validity of album details
    if name == '' or genre == '' or artist == '':
        flash('Album name or Genre name or Artist name can not be empty.')
        return redirect(url_for('add_album_page'))
    if len(name) > 50 or len(genre) > 50 or len(artist) > 50:
        flash('Album name or Genre name or Artist name can not be greater than 50 characters.')
        return redirect(url_for('add_album_page'))
    # storing album information after validity check
    album = Album(albumname=name, albumgenre=genre, albumartist=artist)
    db.session.add(album)
    db.session.commit()
    flash('Album added successfully.')
    return redirect(url_for('admin_page'))

# Define the route for viewing details of a specific album (admin only)
@app.route('/album/<int:id>/open')
@admin_required
def open_album_page(id):
  return render_template('album/open_album.html', user=User.query.get(session['user_id']), album=Album.query.get(id))

# Define the route for adding a new song (admin only)
@app.route('/song/add-song')
@admin_required
def add_song_page():
    album_id = request.args.get('album_id', type=int, default=-1)
    return render_template('song/add_song.html', user=User.query.get(session['user_id']), album=Album.query.get(album_id), albums=Album.query.all())

# Define the route for processing the addition of a new song (admin only)
@app.route('/song/add-song', methods=['POST'])
@admin_required
def add_song_page_post():
    name = request.form.get('name')
    songduration_str = request.form.get('songduration')
    songdateofcreation_str = request.form.get('songdateofcreation')
    album_id = request.form.get('album_id', type=int)
    #checking validity of song details
    if name == '' or songduration_str == '' or songdateofcreation_str == '' or album_id is None:
        flash('Song name, duration, date of creation, or album ID cannot be empty.')
        return redirect(url_for('add_song_page'))
    try:
        songduration = datetime.strptime(songduration_str, '%H:%M:%S').time()
        songdateofcreation = datetime.strptime(songdateofcreation_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid Song duration or date of creation format.')
        return redirect(url_for('add_song_page'))
    album = Album.query.get(album_id)
    if not album:
        flash('Album does not exist.')
        return redirect(url_for('add_song_page'))
    # storing song information after validity check
    song = Song(songname=name, album_id=album_id, songduration=songduration, songdateofcreation=songdateofcreation)
    db.session.add(song)
    db.session.commit()
    flash('Song added successfully.')
    return redirect(url_for('open_album_page', id=album.id))
    
# Define the route for viewing details of a specific song (admin only)
@app.route('/song/<int:id>/open-song')
@admin_required
def open_song_page(id):
    song = Song.query.get(id)
    if not song:
        flash('Song does not exist.')
        return redirect(url_for('admin_page'))
    return render_template('song/open_song.html', user=User.query.get(session['user_id']), song=song)

# Define the route for updating an existing song (admin only)
@app.route('/song/<int:id>/edit-song')
@admin_required
def edit_song_page(id):
    song = Song.query.get(id)
    return render_template('song/edit_song.html', user=User.query.get(session['user_id']), song=song, albums=Album.query.all())

# Define the route for processing the updating of an existing song (admin only)
@app.route('/song/<int:id>/edit-song', methods=['POST'])
@admin_required
def edit_song_page_post(id):
    name = request.form.get('name')
    songduration_str = request.form.get('songduration')
    songdateofcreation_str = request.form.get('songdateofcreation')
    album_id = request.form.get('album_id', type=int)
    # checking song details for valid updation
    if name == '' or songduration_str == '' or songdateofcreation_str == '' or album_id is None:
        flash('Song name, duration, date of creation, or album ID cannot be empty.')
        return redirect(url_for('add_song_page'))
    try:
        songduration = datetime.strptime(songduration_str, '%H:%M:%S').time()
        songdateofcreation = datetime.strptime(songdateofcreation_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid Song duration or date of creation format.')
        return redirect(url_for('add_song_page'))
    album = Album.query.get(album_id)
    if not album:
        flash('Album does not exist.')
        return redirect(url_for('add_song_page'))
    # updating song details after validity check
    song = Song.query.get(id)
    song.songname = name
    song.album_id = album_id
    song.songduration = songduration
    song.songdateofcreation = songdateofcreation
    db.session.commit()
    flash('Song updated successfully.')
    return redirect(url_for('open_album_page', id=album.id))


#Additional routes (commented out for now)
'''
@app.route('/song/<int:id>/listen-song')
@admin_required
def listen_song_page(id):
  return "LISTEN"

@app.route('/song/<int:id>/lyrics-song')
@admin_required
def lyrics_song_page(id):
  return "LYRICS"
'''

# Define the route for deleting a song (admin only)
@app.route('/song/<int:id>/delete-song')
@admin_required
def delete_song_page(id):
    song = Song.query.get(id)
    if not song:
        flash('Song does not exist.')
        return redirect(url_for('admin_page'))
    return render_template('song/delete_song.html', user=User.query.get(session['user_id']), song=song)

# Define the route for processing the deletion of a song (admin only)
@app.route('/song/<int:id>/delete-song', methods=['POST'])
@admin_required
def delete_song_page_post(id):
  song = Song.query.get(id)
  if not song:
    flash('Song does not exist.')
    return redirect(url_for('admin_page'))
  db.session.delete(song)
  db.session.commit()
  flash('Song deleted successfully')
  return redirect(url_for('admin_page'))

# Define the route for editing an album (admin only)
@app.route('/album/<int:id>/edit')
@admin_required
def edit_album_page(id):
  return render_template('album/edit_album.html', user=User.query.get(session['user_id']), album=Album.query.get(id))

# Define the route for processing the edit form for an album (admin only)
@app.route('/album/<int:id>/edit', methods=['POST'])
@admin_required
def edit_album_page_post(id):
    album = Album.query.get(id)
    name = request.form.get('name')
    genre = request.form.get('genre')
    artist = request.form.get('artist')
    # checking album details for valid updation
    if name == '' or genre == '' or artist == '':
        flash('Album name or Genre name or Artist name can not be empty.')
        return redirect(url_for('edit_album_page', id=id))
    if len(name) > 50 or len(genre) > 50 or len(artist) > 50:
        flash('Album name can not be greater than 50 characters.')
        return redirect(url_for('edit_album_page', id=id))
    # updating album details after validity check
    album.albumname = name
    album.albumgenre = genre
    album.albumartist = artist
    db.session.commit()
    flash('Album updated successfully.')
    return redirect(url_for('admin_page'))

# Define the route for deleting an album (admin only)
@app.route('/album/<int:id>/delete')
@admin_required
def delete_album_page(id):
    album = Album.query.get(id)
    if not album:
        flash('Album does not exist.')
        return redirect(url_for('admin_page'))
    return render_template('album/delete_album.html', user=User.query.get(session['user_id']), album=album)

# Define the route for processing the deletion of an album (admin only)
@app.route('/album/<int:id>/delete', methods=['POST'])
@admin_required
def delete_album_page_post(id):
  album = Album.query.get(id)
  if not album:
    flash('Album does not exist.')
    return redirect(url_for('admin_page'))
  db.session.delete(album)
  db.session.commit()
  flash('Album deleted successfully')
  return redirect(url_for('admin_page'))

# Define the route for adding a song to a playlist (authenticated users only)
@app.route('/playlist/<int:song_id>/add', methods=['POST'])
@auth_required
def add_to_playlist_page(song_id):
    song = Song.query.get(song_id)
    if not song:
        flash('Song does not exist.')
        return redirect(url_for('index_page'))
    playlist = Playlist.query.filter_by(userid=session['user_id']).filter_by(songid=song_id).first()
    if playlist:
        # Update the existing playlist entry with the new song ID
        playlist.songid = song.id
        db.session.commit()
        flash('Song added to playlist successfully.')
        return redirect(url_for('index_page'))
    playlist = Playlist(userid=session['user_id'], songid=song_id)
    db.session.add(playlist)
    db.session.commit()
    flash('Song added to playlist successfully.')
    return redirect(url_for('index_page'))

# Define the route for viewing lyrics of a specific song
@app.route('/song/<int:song_id>/lyrics')
@auth_required
def song_lyrics_page(song_id):
    song = Song.query.get(song_id)
    if not song:
        flash('Song does not exist.')
        return redirect(url_for('index_page'))
    return render_template('song/open_song.html', user=User.query.get(session['user_id']), song=song, songs=Song.query.all())

# Define the route for viewing user playlists (authenticated users only)
@app.route('/playlist')
@auth_required
def playlists_page():
    return render_template('playlists.html', user=User.query.get(session['user_id']), users=User.query.all(), songs=Song.query.all(), albums=Album.query.all(), playlists=Playlist.query.filter_by(userid=session['user_id']).all())


'''
@app.route('/playlist')
@auth_required
def playlists_page():
    user = User.query.get(session['user_id'])
    song = Song.query.get(id)
    playlists = Playlist.query.filter_by(userid=user.id).all()    
    # Extract song details for each playlist entry
    return render_template('playlists.html', user=user, song=song)
'''

# Define the route for the creator page
@app.route('/creator')
@auth_required
def creators_page():
    user = User.query.get(session['user_id'])
        # Check if the user is not already a creator
    if not user.iscreator:
        # Set the iscreator status to True
        user.iscreator = True
        db.session.commit()
    return render_template('creators.html', user=user)

@app.route('/creator/upload')
@auth_required
def upload_song_page():
    album_id = request.args.get('album_id', type=int, default=-1)
    return render_template('upload_song.html', user=User.query.get(session['user_id']), album=Album.query.get(album_id), albums=Album.query.all())

@app.route('/creator/upload', methods=['POST'])
@auth_required
def upload_song_page_post():
    name = request.form.get('name')
    songduration_str = request.form.get('songduration')
    songdateofcreation_str = request.form.get('songdateofcreation')
    album_id = request.form.get('album_id', type=int)
    #checking validity of song details
    if name == '' or songduration_str == '' or songdateofcreation_str == '' or album_id is None:
        flash('Song name, duration, date of creation, or album ID cannot be empty.')
        return redirect(url_for('upload_song_page'))
    try:
        songduration = datetime.strptime(songduration_str, '%H:%M:%S').time()
        songdateofcreation = datetime.strptime(songdateofcreation_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid Song duration or date of creation format.')
        return redirect(url_for('upload_song_page'))
    album = Album.query.get(album_id)
    if not album:
        flash('Album does not exist.')
        return redirect(url_for('upload_song_page'))
    # storing song information after validity check
    song = Song(songname=name, album_id = album_id, songduration=songduration, songdateofcreation=songdateofcreation)
    db.session.add(song)
    db.session.commit()
    flash('Song added successfully.')
    return redirect(url_for('upload_song_page', id=album.id))


# Additional routes (commented out for now)
'''
@app.route('/admin_login')
def admin_login_page():
  return render_template("admin_login.html")

@app.route("/user_home")
def user_home_page():
  return render_template("user_home.html")

@app.route("/admin_home")
def admin_home_page():
  return render_template("admin_home.html")

@app.route("/creator")
def creator_page():
  return render_template("creator.html")

@app.route("/song1")
def song1_page():
  return render_template("song1.html")

@app.route("/upload",methods=['POST'])
def upload_page():
  return render_template("upload.html")
'''

# Additional routes (commented out for now)
'''
@app.route('/upload', methods=['GET', 'POST'])
def upload():
  if request.method == 'POST':
    file = request.files['file']
    if file:
      filename = file.filename
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

      song = Song(filename=filename)
      db.session.add(song)
+      db.session.commit()
      return redirect(url_for('upload'))
  return render_template('upload.html')
'''

# Start the Flask application
if __name__ == "__main__":
  app.run()
#    app.run(host='localhost', port=5000)
