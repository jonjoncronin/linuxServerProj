#!/usr/local/bin/python3
"""
The models.py module is a module intended define the object model for the
Catalog Application.

This object model should be used heavily by the application.py standalone
module.
"""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import random
import string

Base = declarative_base()


class User(Base):
    """
    User class to represent users that wish to use the Catalog App.

    Inheritence
    =======================================================
    Base -
        A sqlalchemy declarative_base
    """
    __tablename__ = "AppUser"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    """
    Category class to represent different categories set by users and for which
    items fall under.

    Inheritence
    =======================================================
    Base -
        A sqlalchemy declarative_base
    """
    __tablename__ = "Category"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    @property
    def serialize(self):
        """
        A property of a Category that allows a caller to serialze the data that
        represents a specific Category object

        Parameters
        =======================================================
        self -
            The category to serialize.

        Returns
        =======================================================
        dictionary containing the information that makes up a Category.
        """
        return {
            "id": self.id,
            "name": self.name,
        }


class Item(Base):
    """
    Item class to represent different items set by users and for which fall
    under different categories.

    Inheritence
    =======================================================
    Base -
        A sqlalchemy declarative_base
    """
    __tablename__ = "Item"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("Category.id"))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey("AppUser.id"))
    user = relationship(User)

    @property
    def serialize(self):
        """
        A property of an Item that allows a caller to serialze the data that
        represents a specific Item object

        Parameters
        =======================================================
        self -
            The item to serialize.

        Returns
        =======================================================
        dictionary containing the information that makes up an Item.
        """
        return {
            "cat_id": self.category_id,
            "description": self.description,
            "id": self.id,
            "title": self.name,
        }


# engine = create_engine("sqlite:///catalog.db")
engine = create_engine('postgresql://db_admin:admin@localhost:5432/catalogstore')

Base.metadata.create_all(engine)
