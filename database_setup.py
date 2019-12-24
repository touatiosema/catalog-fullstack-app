from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """Class to create the table 'user'."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'id': self.id,
           'name': self.name,
           'email': self.email,
           'picture': self.picture
        }


# Category table
class Category(Base):
    __tablename__ = 'category'

    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'id': self.id,
           'name': self.name,
           'items': self.items
        }


# Items table
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id', ondelete='CASCADE'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    user = relationship(User)
    creation_time = Column(DateTime, default=func.now())
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'id': self.id,
           'description': self.description,
           'creation_time': self.creation_time,
        }


engine = create_engine('postgres://osema:RanDom_123@localhost:5432/catalog')


Base.metadata.create_all(engine)
