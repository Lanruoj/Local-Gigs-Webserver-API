from main import db, bcrypt, jwt
from utils import search_table, update_record
from flask import Blueprint, jsonify, request, abort, Markup
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from marshmallow.exceptions import ValidationError
from datetime import datetime
from models.gig import Gig
from schemas.gig_schema import gig_schema, gigs_schema
from models.performance import Performance
from schemas.performance_schema import performance_schema
from models.artist import Artist
from schemas.artist_schema import artist_schema, artists_schema, ArtistSchema
from models.watch_artist import WatchArtist
from schemas.watch_artist_schema import watch_artist_schema
from models.user import User
from schemas.user_schema import user_schema


artists = Blueprint("artists", __name__, url_prefix="/artists")

@artists.route("/template", methods=["GET"])
def get_artist_template():
    # RETURN AN EMPTY ARTIST JSON ARRAY TEMPLATE
    artist_template = {
        "name": "...",
        "genre": "..."
    }

    return artist_template


@artists.route("/", methods=["GET"])
def search_artists():
    # SEARCH ARTISTS TABLE - BY DEFAULT RETURN ALL BUT TAKES OPTIONAL QUERY STRING ARGUMENTS FOR FILTERING AND SORTING
    artists = search_table(Artist, artists_schema)
    
    return artists


@artists.route("/", methods=["POST"])
@jwt_required()
def add_artist():
    # FETCH USER WITH user_id AS RETURNED BY get_jwt_identity() FROM JWT TOKEN
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.logged_in:
        return abort(401, description="User must be logged in")
    
    artist_fields = artist_schema.load(request.json)
    # CREATE NEW ARTIST FROM REQUEST FIELDS
    artist = Artist(
        name = artist_fields["name"],
        genre = artist_fields["genre"]
    )
    # ADD ARTIST TO SESSION AND COMMIT TO DATABASE
    db.session.add(artist)
    db.session.commit()

    return jsonify(artist_schema.dump(artist))


@artists.route("/<int:artist_id>", methods=["GET"])
def get_artist(artist_id):
    # FETCH ARTIST WITH id MATCHING artist_id FROM PATH PARAMETER
    artist = Artist.query.get(artist_id)

    return jsonify(artist_schema.dump(artist))


@artists.route("/<int:artist_id>", methods=["PUT"])
@jwt_required()
def update_artist(artist_id):
    # FETCH USER WITH user_id AS RETURNED BY get_jwt_identity() FROM JWT TOKEN
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.logged_in:
        return abort(401, description="User must be logged in")
    # UPDATE ARTIST FROM REQUEST BODY
    update = update_record(artist_id, Artist, artist_schema)
    # COMMIT CHANGES TO DATABASE
    db.session.commit()

    return update


@artists.route("/<int:artist_id>", methods=["DELETE"])
@jwt_required()
def delete_artist(artist_id):
    # FETCH USER WITH user_id AS RETURNED BY get_jwt_identity() FROM JWT TOKEN
    user = User.query.get(int(get_jwt_identity()))
    if not user.admin or not user.logged_in:
        return abort(401, description="Unauthorised - must be an administrator to delete artists")
    # FETCH ARTIST FROM PATH PARAMETER WITH MATCHING id
    artist = Artist.query.get(artist_id)
    if not artist:
        return abort(404, description="Artist does not exist")
    # DELETE ARTIST FROM SESSION AND COMMIT TO DATABASE
    db.session.delete(artist)
    db.session.commit()

    return jsonify(message=f"{artist.name} has been deleted")



@artists.route("/watch", methods=["POST"])
@jwt_required()
def watch_artist():
    watch_artist_fields = watch_artist_schema.load(request.json, partial=True)
    # FETCH USER WITH user_id AS RETURNED BY get_jwt_identity() FROM JWT TOKEN
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.logged_in:
        return abort(401, description="Unauthorised - user must be logged in")
    # FETCH USER'S WATCHED ARTISTS FROM THE WATCHARTISTS TABLE
    users_watched_artists = WatchArtist.query.filter_by(user_id=user.id).all()
    # FETCH ARTIST FROM THE REQUEST BODY'S artist_id
    artist = Artist.query.get(watch_artist_fields["artist_id"])
    if not artist:
        return abort(404, description="Artist does not exist")
    # CHECK IF USER IS ALREADY WATCHING THE ARTIST
    for wa in users_watched_artists:
        if wa.artist_id == watch_artist_fields["artist_id"]:
            artist = Artist.query.get(watch_artist_fields["artist_id"])

            return abort(400, description=f"{user.first_name} already watching {artist.name}")
    

    new_watched_artist = WatchArtist(
        user_id = user.id,
        artist_id = watch_artist_fields["artist_id"]
    )
    db.session.add(new_watched_artist)
    db.session.commit()

    return jsonify(watch_artist_schema.dump(new_watched_artist))

