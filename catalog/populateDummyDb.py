#!/usr/local/bin/python3
"""
The populateDummyDb.py module is a module intended utilize the object model for
the Catalog Application and prepopulate the DB with some content to develop
against.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Item, Category, User

# engine = create_engine("sqlite:///catalog.db")
engine = create_engine('postgresql://db_admin:admin@localhost:5432/catalogstore')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

itemsList = (
    {"category": "kitchen",
     "items": (
         {"name": "fork", "description": ""},
         {"name": "knife", "description": ""},
         {"name": "spoon", "description": ""},
         {"name": "plate", "description": ""},
         {"name": "bowl", "description": ""})
     },
    {"category": "bathroom",
        "items": (
            {"name": "toothbrush", "description": ""},
            {"name": "toothpaste", "description": ""},
            {"name": "floss", "description": ""},
            {"name": "razor", "description": ""},
            {"name": "hairbrush", "description": ""})
     }
)

# Create the admin user
defUser = User(name="Admin", email="admin@example.com", picture="")
session.add(defUser)
session.commit()

# Create dummy items
for category in itemsList:
    someCategory = Category(name=category["category"])
    session.add(someCategory)
    session.commit()
    newCat = session.query(Category).filter_by(name=someCategory.name).one()
    print("New Category {0}\n".format(category))
    for item in category["items"]:
        someItem = Item(
            user_id=defUser.id,
            name=item["name"],
            description=item["description"],
            category_id=newCat.id)

        session.add(someItem)
        print("added {0}\n".format(item))
    print("=======================\n")
session.commit()
print("DB populated")
