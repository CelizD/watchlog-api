"""Endpoints relacionados con peliculas."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from src.extensions import db
from src.models.movie import Movie

bp = Blueprint("movies", __name__, url_prefix="/movies")


class MovieService:
    """Orquesta la logica de negocio para el recurso Movie."""

    # TODO: inyectar dependencias necesarias (db.session, modelos, esquemas, etc.).
    def __init__(self):
        self.db_session = db.session
        self.model = Movie

    def list_movies(self) -> list[dict]:
        """Retorna todas las peliculas registradas."""
        # TODO: consultar la base de datos y serializar a una lista de dicts.
        movies = self.model.query.order_by(self.model.title).all()
        return [movie.to_dict() for movie in movies]

    def create_movie(self, payload: dict) -> dict:
        """Crea una nueva pelicula."""
        # TODO: validar el payload y persistir un nuevo registro Movie.
        # Una validacion simple, se podria usar Marshmallow/Pydantic
        if "title" not in payload:
            raise ValueError("El campo 'title' es obligatorio.")

        movie = self.model(**payload)
        self.db_session.add(movie)
        try:
            self.db_session.commit()
            return movie.to_dict()
        except IntegrityError:
            self.db_session.rollback()
            raise ValueError("Error al guardar la pelicula.")
        except Exception:
            self.db_session.rollback()
            raise

    def get_movie(self, movie_id: int) -> dict | None:
        """Obtiene una pelicula por su identificador."""
        # TODO: buscar la pelicula y manejar el caso de no encontrada.
        movie = self.model.query.get(movie_id)
        return movie.to_dict() if movie else None

    def update_movie(self, movie_id: int, payload: dict) -> dict | None:
        """Actualiza los datos de una pelicula."""
        # TODO: aplicar cambios permitidos y guardar en la base de datos.
        movie = self.model.query.get(movie_id)
        if not movie:
            return None

        # Campos permitidos para actualizacion
        allowed_fields = ["title", "genre", "release_year"]
        for key, value in payload.items():
            if key in allowed_fields:
                setattr(movie, key, value)

        try:
            self.db_session.commit()
            return movie.to_dict()
        except Exception:
            self.db_session.rollback()
            raise

    def delete_movie(self, movie_id: int) -> bool:
        """Elimina una pelicula existente."""
        # TODO: definir si el borrado debe ser logico o fisico.
        movie = self.model.query.get(movie_id)
        if not movie:
            return False

        try:
            self.db_session.delete(movie)
            self.db_session.commit()
            return True
        except Exception:
            self.db_session.rollback()
            raise


service = MovieService()


@bp.get("/")
def list_movies():
    """Lista todas las peliculas disponibles."""
    # TODO: invocar service.list_movies y devolver la respuesta serializada.
    try:
        movies = service.list_movies()
        return jsonify(movies), 200
    except Exception as e:
        return jsonify({"error": f"Error al listar peliculas: {e}"}), 500


@bp.post("/")
def create_movie():
    """Crea una pelicula a partir de los datos enviados."""
    payload = request.get_json(silent=True) or {}
    # TODO: validar payload, manejar errores y devolver el recurso creado.
    try:
        new_movie = service.create_movie(payload)
        return jsonify(new_movie), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.get("/<int:movie_id>")
def retrieve_movie(movie_id: int):
    """Devuelve el detalle de una pelicula concreta."""
    # TODO: invocar service.get_movie y manejar 404 cuando corresponda.
    movie = service.get_movie(movie_id)
    if not movie:
        return jsonify({"error": "Pelicula no encontrada"}), 404
    return jsonify(movie), 200


@bp.put("/<int:movie_id>")
def update_movie(movie_id: int):
    """Actualiza la informacion de una pelicula."""
    payload = request.get_json(silent=True) or {}
    # TODO: invocar service.update_movie y devolver el recurso actualizado.
    try:
        movie = service.update_movie(movie_id, payload)
        if not movie:
            return jsonify({"error": "Pelicula no encontrada"}), 404
        return jsonify(movie), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.delete("/<int:movie_id>")
def delete_movie(movie_id: int):
    """Elimina una pelicula del catalogo."""
    # TODO: invocar service.delete_movie y devolver 204 al completar.
    try:
        deleted = service.delete_movie(movie_id)
        if not deleted:
            return jsonify({"error": "Pelicula no encontrada"}), 404
        return "", 204  # No Content
    except Exception as e:
        # Manejar error si la pelicula esta en uso (FK constraint)
        if "FOREIGN KEY constraint failed" in str(e):
            return jsonify(
                {"error": "No se puede borrar la pelicula, esta en uso en una watchlist."}
            ), 409
        return jsonify({"error": f"Error interno: {e}"}), 500