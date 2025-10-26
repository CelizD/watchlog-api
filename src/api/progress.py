"""Endpoints para controlar el progreso de los usuarios."""

from __future__ import annotations

from functools import wraps

from flask import Blueprint, jsonify, request, abort

from src.extensions import db
from src.models.movie import Movie
from src.models.series import Series
from src.models.watch_entry import WatchEntry

bp = Blueprint("progress", __name__, url_prefix="")


def require_user_id(f):
    """Decorador para validar el header X-User-Id."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get("X-User-Id", type=int)
        if not user_id:
            # 401 Unauthorized
            abort(401, description="Header X-User-Id es obligatorio.")
        
        # Pasa el user_id como argumento a la ruta
        kwargs["user_id"] = user_id
        return f(*args, **kwargs)
    return decorated_function


class ProgressService:
    """Coordina operaciones sobre la lista de seguimiento y progreso."""

    # TODO: inyectar modelos User, Series, Movie y WatchEntry con sus esquemas.
    def __init__(self):
        self.db_session = db.session

    def list_watchlist(self, user_id: int) -> list[dict]:
        """Devuelve los contenidos asociados a un usuario."""
        # TODO: consultar entradas filtradas por user_id y calcular porcentajes.
        entries = WatchEntry.query.filter_by(user_id=user_id).order_by(
            WatchEntry.updated_at.desc()
        ).all()
        return [entry.to_dict() for entry in entries]

    def add_movie(self, user_id: int, movie_id: int) -> dict:
        """Agrega una pelicula a la lista del usuario."""
        # TODO: validar existencia del usuario y pelicula antes de crear el registro.
        movie = Movie.query.get(movie_id)
        if not movie:
            raise ValueError(f"Pelicula con id {movie_id} no encontrada.")

        exists = WatchEntry.query.filter_by(
            user_id=user_id, content_type="movie", content_id=movie_id
        ).first()
        if exists:
            raise ValueError("Pelicula ya esta en la watchlist.")

        entry = WatchEntry(
            user_id=user_id,
            content_type="movie",
            content_id=movie_id,
            status="pending",
        )
        self.db_session.add(entry)
        self.db_session.commit()
        return entry.to_dict()

    def add_series(self, user_id: int, series_id: int) -> dict:
        """Agrega una serie a la lista del usuario."""
        # TODO: crear WatchEntry inicial con temporadas/episodios en cero.
        series = Series.query.get(series_id)
        if not series:
            raise ValueError(f"Serie con id {series_id} no encontrada.")

        exists = WatchEntry.query.filter_by(
            user_id=user_id, content_type="series", content_id=series_id
        ).first()
        if exists:
            raise ValueError("Serie ya esta en la watchlist.")

        # Calculamos el total de episodios de la serie
        total_ep = sum(season.episodes_count for season in series.seasons)

        entry = WatchEntry(
            user_id=user_id,
            content_type="series",
            content_id=series_id,
            status="pending",
            total_episodes=total_ep,
            watched_episodes=0,
            current_season=1,
            current_episode=1,
        )
        self.db_session.add(entry)
        self.db_session.commit()
        return entry.to_dict()

    def update_series_progress(self, user_id: int, series_id: int, payload: dict) -> dict:
        """Actualiza el progreso de una serie en la lista del usuario."""
        # TODO: validar limites de temporadas y episodios, recalcular porcentaje.
        entry = WatchEntry.query.filter_by(
            user_id=user_id, content_type="series", content_id=series_id
        ).first()

        if not entry:
            raise ValueError("Entrada no encontrada en la watchlist.")

        # Campos actualizables
        if "watched_episodes" in payload:
            watched = int(payload["watched_episodes"])
            # Validar limites
            entry.watched_episodes = max(0, min(watched, entry.total_episodes or 0))

        if "current_season" in payload:
            entry.current_season = int(payload["current_season"])
        
        if "current_episode" in payload:
            entry.current_episode = int(payload["current_episode"])
        
        if "status" in payload:
            if payload["status"] == "watched":
                entry.mark_as_watched()
            else:
                entry.status = payload["status"]
        
        # Recalcular estado basado en episodios
        if entry.status != "watched":
            if (entry.watched_episodes or 0) >= (entry.total_episodes or 0) and entry.total_episodes > 0:
                entry.mark_as_watched()
            elif (entry.watched_episodes or 0) > 0:
                entry.status = "watching"
            else:
                entry.status = "pending"

        self.db_session.commit()
        return entry.to_dict()


service = ProgressService()


@bp.get("/me/watchlist")
@require_user_id
def get_my_watchlist(user_id: int):
    """Devuelve la lista de seguimiento del usuario actual."""
    # TODO: validar el header y manejar autenticacion simulada.
    try:
        watchlist = service.list_watchlist(user_id)
        return jsonify(watchlist), 200
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.post("/watchlist/movies/<int:movie_id>")
@require_user_id
def add_movie_to_watchlist(user_id: int, movie_id: int):
    """Agrega una pelicula a la lista del usuario."""
    # TODO: invocar service.add_movie y devolver 201 con la entrada creada.
    try:
        new_entry = service.add_movie(user_id, movie_id)
        return jsonify(new_entry), 201
    except ValueError as ve:
        if "no encontrada" in str(ve):
            return jsonify({"error": str(ve)}), 404
        return jsonify({"error": str(ve)}), 409  # Conflict
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.post("/watchlist/series/<int:series_id>")
@require_user_id
def add_series_to_watchlist(user_id: int, series_id: int):
    """Agrega una serie a la lista del usuario."""
    # TODO: invocar service.add_series y devolver 201 con la entrada creada.
    try:
        new_entry = service.add_series(user_id, series_id)
        return jsonify(new_entry), 201
    except ValueError as ve:
        if "no encontrada" in str(ve):
            return jsonify({"error": str(ve)}), 404
        return jsonify({"error": str(ve)}), 409  # Conflict
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.patch("/progress/series/<int:series_id>")
@require_user_id
def update_series_progress(user_id: int, series_id: int):
    """Actualiza los datos de progreso de una serie."""
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "Payload vacio"}), 400
        
    # TODO: invocar service.update_series_progress y devolver el recurso actualizado.
    try:
        updated_entry = service.update_series_progress(user_id, series_id, payload)
        return jsonify(updated_entry), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500