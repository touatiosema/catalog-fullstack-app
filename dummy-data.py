import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from database_setup import Item, Base, Category, User
 
engine = create_engine('postgres://osema:RanDom_123@localhost:5432/catalog')
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
session = DBSession()


user1 = User(
    name='Osema',
    email='osema.touati@gmail.com',
    picture='https://img.com/sdf'
)

session.add(user1)
session.commit()

category1 = Category(name='Soccer')

session.add(category1)
session.commit()

item1 = Item(
    name='Snowboard',
    description='It is an exciting snowboard. You will feel like in heaven after driving it!',
    category=category1,
    user=user1
)

session.add(item1)
session.commit()

category1 = Category(name='Basketball')

session.add(category1)
session.commit()

item1 = Item(
    name='Snaks',
    description='Very good snaks i guess.',
    category=category1,
    user=user1
)

session.add(item1)
session.commit()


print('Elements succussfully added!')




