"""Modelo para series disponibles en el catalogo."""

from __future__ import annotations

from datetime import datetime

from src.extensions import db


class Series(db.Model):
    """Representa una serie cargada por los usuarios."""

    __tablename__ = "series"

    # TODO: definir columnas (id, title, total_seasons, created_at, updated_at).
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, index=True)
    total_seasons = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    # TODO: agregar columnas opcionales (synopsis, genres, image_url) si se desean.
    synopsis = db.Column(db.Text, nullable=True)
    genres = db.Column(db.String(150), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

    # TODO: configurar relacion con Season (one-to-many) y WatchEntry.
    seasons = db.relationship(
        "Season",
        back_populates="series",
        lazy="joined",
        cascade="all, delete-orphan",
    )
    # Relacion polimorfica (via WatchEntry)
    watch_entries = db.relationship(
        "WatchEntry",
        back_populates="series_content",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Devuelve una representacion legible del modelo."""
        return f"<Series id={self.id} title={self.title}>"

    def to_dict(self, include_seasons: bool = False) -> dict:
        """Serializa la serie y opcionalmente sus temporadas."""
        # TODO: reemplazar por serializacion real usando marshmallow o similar.
        data = {
            "id": self.id,
            "title": self.title,
            "total_seasons": self.total_seasons,
            "synopsis": self.synopsis,
            "genres": self.genres,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_seasons:
            # TODO: serializar temporadas reales en lugar de lista vacia.
            data["seasons"] = [season.to_dict() for season in self.seasons]
        return data