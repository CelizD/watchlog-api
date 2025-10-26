"""Modelo que representa una temporada de una serie."""

from __future__ import annotations

from src.extensions import db


class Season(db.Model):
    """Temporada asociada a una serie."""

    __tablename__ = "seasons"
    __table_args__ = (
        db.UniqueConstraint("series_id", "number", name="uq_series_season_number"),
    )

    # TODO: definir columnas (id, series_id, number, episodes_count).
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)  # Numero de temporada
    episodes_count = db.Column(db.Integer, nullable=False, default=0)

    # TODO: establecer restriccion unica por (series_id, number).
    # Hecho arriba con __table_args__

    # TODO: configurar relacion back_populates con Series.
    series = db.relationship("Series", back_populates="seasons")

    def to_dict(self) -> dict:
        """Serializa la temporada en un diccionario."""
        # TODO: reemplazar esta implementacion por la serializacion real.
        return {
            "id": self.id,
            "series_id": self.series_id,
            "number": self.number,
            "episodes_count": self.episodes_count,
        }