"""Modelo puente que guarda el progreso del usuario."""

from __future__ import annotations

from datetime import datetime

from src.extensions import db


class WatchEntry(db.Model):
    """Relacion entre un usuario y un contenido (pelicula o serie)."""

    __tablename__ = "watch_entries"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "content_type",
            "content_id",
            name="uq_user_content",
        ),
    )

    # TODO: definir columnas basicas (id, user_id, content_type, content_id, status).
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # 'movie' o 'series'
    content_type = db.Column(db.String(20), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    # 'pending', 'watching', 'watched'
    status = db.Column(db.String(20), nullable=False, default="pending")

    # TODO: agregar columnas de progreso (current_season, current_episode, watched_episodes, total_episodes).
    current_season = db.Column(db.Integer, nullable=True, default=1)
    current_episode = db.Column(db.Integer, nullable=True, default=1)
    watched_episodes = db.Column(db.Integer, nullable=True, default=0)
    total_episodes = db.Column(db.Integer, nullable=True, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # TODO: establecer claves foraneas hacia User, Movie y Series segun el tipo.
    # Se usan relaciones polimorficas "condicionales"
    movie_content_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=True)
    series_content_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=True)

    # TODO: modelar las relaciones back_populates con User, Movie y Series.
    user = db.relationship("User", back_populates="watch_entries")

    movie_content = db.relationship(
        "Movie",
        foreign_keys=[movie_content_id],
        back_populates="watch_entries",
    )
    series_content = db.relationship(
        "Series",
        foreign_keys=[series_content_id],
        back_populates="watch_entries",
    )

    def __init__(self, *args, **kwargs):
        """Asigna content_id a la clave foranea correcta."""
        super().__init__(*args, **kwargs)
        if self.content_type == "movie":
            self.movie_content_id = self.content_id
            # Para peliculas, los episodios son 1
            self.total_episodes = 1
            self.watched_episodes = 0
        elif self.content_type == "series":
            self.series_content_id = self.content_id
            # total_episodes deberia calcularse al agregar la serie

    def percentage_watched(self) -> float:
        """Calcula el porcentaje completado para el contenido asociado."""
        # TODO: implementar calculo utilizando watched_episodes y total_episodes.
        if self.status == "watched":
            return 100.0
        if not self.total_episodes or self.total_episodes == 0:
            return 0.0
        
        # Asegurar que los vistos no superen el total
        watched = min(self.watched_episodes or 0, self.total_episodes)
        
        percentage = (watched / self.total_episodes) * 100
        return round(percentage, 2)

    def mark_as_watched(self) -> None:
        """Marca el contenido como completado."""
        # TODO: actualizar atributos y timestamps para reflejar el estado final.
        self.status = "watched"
        if self.content_type == "movie":
            self.watched_episodes = 1
        elif self.content_type == "series" and self.total_episodes:
            self.watched_episodes = self.total_episodes
            if self.series_content and self.series_content.seasons:
                # Opcional: setear a la ultima temporada/episodio
                last_season = max(s.number for s in self.series_content.seasons)
                self.current_season = last_season
                self.current_episode = next(
                    s.episodes_count for s in self.series_content.seasons if s.number == last_season
                )
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Serializa la entrada para respuestas JSON."""
        # TODO: reemplazar con serializacion acorde al modelo final.
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "content_id": self.content_id,
            "status": self.status,
            "current_season": self.current_season,
            "current_episode": self.current_episode,
            "watched_episodes": self.watched_episodes,
            "total_episodes": self.total_episodes,
            "percentage_watched": self.percentage_watched(),
            "updated_at": self.updated_at,
        }