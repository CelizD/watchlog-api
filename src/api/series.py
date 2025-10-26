"""Endpoints relacionados con series y temporadas."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from src.extensions import db
from src.models.seasons import Season
from src.models.series import Series

bp = Blueprint("series", __name__, url_prefix="/series")


class SeriesService:
    """Gestiona las operaciones CRUD sobre Series y Seasons."""

    # TODO: inyectar modelos Series y Season junto a la sesion de base de datos.
    def __init__(self):
        self.db_session = db.session

    def list_series(self) -> list[dict]:
        """Retorna la lista de series disponibles."""
        # TODO: consultar las series existentes y devolverlas serializadas.
        series_list = Series.query.order_by(Series.title).all()
        # No incluimos temporadas en el listado general por performance
        return [series.to_dict(include_seasons=False) for series in series_list]

    def create_series(self, payload: dict) -> dict:
        """Crea una nueva serie."""
        # TODO: validar payload (titulo, temporadas, etc.) y persistir la serie.
        if "title" not in payload or "total_seasons" not in payload:
            raise ValueError("Los campos 'title' y 'total_seasons' son obligatorios.")

        series = Series(**payload)
        self.db_session.add(series)
        try:
            self.db_session.commit()
            return series.to_dict()
        except IntegrityError:
            self.db_session.rollback()
            raise ValueError("Error al guardar la serie.")
        except Exception:
            self.db_session.rollback()
            raise

    def get_series(self, series_id: int) -> dict | None:
        """Obtiene una serie y sus temporadas asociadas."""
        # TODO: recuperar el registro y manejar la ausencia del recurso.
        # Usamos lazy="joined" en el modelo, asi que las temporadas vienen
        series = Series.query.get(series_id)
        return series.to_dict(include_seasons=True) if series else None

    def update_series(self, series_id: int, payload: dict) -> dict | None:
        """Actualiza los campos permitidos de una serie."""
        # TODO: definir que campos son editables e implementar la actualizacion.
        series = Series.query.get(series_id)
        if not series:
            return None

        allowed_fields = [
            "title",
            "total_seasons",
            "synopsis",
            "genres",
            "image_url",
        ]
        for key, value in payload.items():
            if key in allowed_fields:
                setattr(series, key, value)

        try:
            self.db_session.commit()
            return series.to_dict(include_seasons=True)
        except Exception:
            self.db_session.rollback()
            raise

    def delete_series(self, series_id: int) -> bool:
        """Elimina una serie del catalogo."""
        # TODO: decidir estrategia de borrado e implementarla.
        series = Series.query.get(series_id)
        if not series:
            return False

        try:
            # El borrado en cascada eliminara las temporadas asociadas
            self.db_session.delete(series)
            self.db_session.commit()
            return True
        except Exception:
            self.db_session.rollback()
            raise

    def add_season(self, series_id: int, payload: dict) -> dict:
        """Agrega una temporada a una serie existente."""
        # TODO: validar numero de temporada y cantidad de episodios.
        series = Series.query.get(series_id)
        if not series:
            raise ValueError(f"La serie con id {series_id} no existe.")

        if "number" not in payload or "episodes_count" not in payload:
            raise ValueError(
                "Los campos 'number' y 'episodes_count' son obligatorios."
            )

        # Validar que no exista ya esa temporada
        exists = Season.query.filter_by(
            series_id=series_id, number=payload["number"]
        ).first()
        if exists:
            raise ValueError(
                f"La temporada {payload['number']} ya existe para esta serie."
            )

        new_season = Season(series_id=series_id, **payload)
        self.db_session.add(new_season)
        self.db_session.commit()
        return new_season.to_dict()


service = SeriesService()


@bp.get("/")
def list_series():
    """Devuelve todas las series registradas."""
    # TODO: invocar service.list_series y devolver respuesta paginada si aplica.
    try:
        series = service.list_series()
        return jsonify(series), 200
    except Exception as e:
        return jsonify({"error": f"Error al listar series: {e}"}), 500


@bp.post("/")
def create_series():
    """Crea una nueva serie."""
    payload = request.get_json(silent=True) or {}
    # TODO: usar service.create_series y devolver 201 con la nueva serie.
    try:
        new_series = service.create_series(payload)
        return jsonify(new_series), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.get("/<int:series_id>")
def retrieve_series(series_id: int):
    """Devuelve los detalles de una serie."""
    # TODO: invocar service.get_series y construir respuesta con temporadas.
    series = service.get_series(series_id)
    if not series:
        return jsonify({"error": "Serie no encontrada"}), 404
    return jsonify(series), 200


@bp.put("/<int:series_id>")
def update_series(series_id: int):
    """Actualiza la informacion de una serie."""
    payload = request.get_json(silent=True) or {}
    # TODO: invocar service.update_series y devolver la serie actualizada.
    try:
        series = service.update_series(series_id, payload)
        if not series:
            return jsonify({"error": "Serie no encontrada"}), 404
        return jsonify(series), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.delete("/<int:series_id>")
def delete_series(series_id: int):
    """Elimina una serie del catalogo."""
    # TODO: invocar service.delete_series y devolver 204.
    try:
        deleted = service.delete_series(series_id)
        if not deleted:
            return jsonify({"error": "Serie no encontrada"}), 404
        return "", 204  # No Content
    except Exception as e:
        if "FOREIGN KEY constraint failed" in str(e):
            return jsonify(
                {"error": "No se puede borrar la serie, esta en uso en una watchlist."}
            ), 409
        return jsonify({"error": f"Error interno: {e}"}), 500


@bp.post("/<int:series_id>/seasons")
def add_season(series_id: int):
    """Agrega una temporada a una serie existente."""
    payload = request.get_json(silent=True) or {}
    # TODO: invocar service.add_season y devolver la temporada creada.
    try:
        new_season = service.add_season(series_id, payload)
        return jsonify(new_season), 201
    except ValueError as ve:
        # Esto captura "Serie no encontrada" (404) o "Temporada ya existe" (400)
        if "no existe" in str(ve):
            return jsonify({"error": str(ve)}), 404
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500