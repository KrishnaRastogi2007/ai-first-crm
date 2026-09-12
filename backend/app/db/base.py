"""
SQLAlchemy models ke base/metadata ko manage karne ke liye.

Memory:

base.py = models ki foundation

"""
from sqlalchemy.orm import DeclarativeBase # ORM--> Object Relational Mapping .
# Its Work Is To Connect/Mapp Python Objects/Classes With DataBase Tables .
# DeclarativeBase Is An Base Class Of SQLAlchemy , That Provides Foundation For Creation Of Declearative ORM Model.
class Base(DeclarativeBase):
    pass