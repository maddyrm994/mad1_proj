# Music Streaming Application

This project is a music streaming web application that allows users to play songs, read lyrics, create playlists, and lets creators upload their own music. The app is managed by an admin who oversees data and user interactions.

## Features
- **User Roles**: Separate roles for users, creators, and admins.
- **User Functionalities**: 
  - Play songs
  - View lyrics
  - Create playlists
  - Upload music (for creator role)
- **Admin Functionalities**: Manage application data, including user and music information.
- **Authentication & Authorization**: Secure login and registration, with role-based access control.
- **Feedback**: User feedback provided via flash messages for actions like registration, login, and updates.

## Technologies Used
- **Backend**: Flask, Flask-SQLAlchemy, Werkzeug
- **Frontend**: HTML/CSS, Bootstrap, Jinja2
- **Database**: SQLite

## Database Design
The database is structured to ensure data normalization, integrity, and flexibility, with primary and foreign key relationships. Default values and nullable fields are applied where appropriate.

## API Design
The application has several endpoints with `GET` and `POST` methods for various user-related, admin-related, profile-related, and genre-related actions. These routes manage CRUD operations for users, songs, albums, genres, and playlists.

## Architecture
This application follows the Model-View-Controller (MVC) pattern:
- **Models**: Defined in `app.py` using SQLAlchemy, covering entities such as User, Song, Album, Genre, and Playlist.
- **Controllers**: Handle routing and application logic, with each route linked to specific pages and actions.
- **Views**: HTML templates stored in the "templates" folder, with static files (CSS, images) stored in "static".

---
