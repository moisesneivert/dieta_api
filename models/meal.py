from database import db
from datetime import datetime

class Meal(db.Model):
    __tablename__ = "meals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    in_diet = db.Column(db.Boolean, nullable=False, default=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("meals", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "datetime": self.datetime.isoformat(),
            "in_diet": self.in_diet,
            "user_id": self.user_id,
        }
