#!/usr/local/bin/python3
"""
The application.py module is a standalone module intended to act as a webserver
hosting the site for a Catalog Item App.

This Catalog Item App is intended to allow users to maintain a list of items
that fall under a variety of categories. Both the item and the category it
falls under are user specified.

Currently an item is unique even if it falls under different categories - ie
you CANNOT have a ball under the category of baseball and a ball under the
category of soccer.
"""
from flask import Flask, render_template, url_for, request, redirect, flash
from flask import jsonify, g
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Item, Category, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import random
import string
import json
import requests
import logging

# Store off Google CLIENT_ID and APPLICATION_NAME
CLIENT_ID = json.loads(open("google_client_secrets.json", "r").read())[
    "web"]["client_id"]
APPLICATION_NAME = "Catalog Project Application"

# Create the connections and sessions to the catalog database
# engine = create_engine("sqlite:///catalog.db")
engine = create_engine('postgresql://db_admin:admin@localhost:5432/catalogStore')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create debug log for capturing events that happen during execution
# Log output to file and to the console for now
logging.basicConfig(filename='logs/debug.log', filemode='w', level=logging.DEBUG)
consoleHandler = logging.StreamHandler()
logging.getLogger('').addHandler(consoleHandler)

app = Flask(__name__)

@app.route('/')
def showItems():
    """
    Function that handles the routes to '/' and '/catalog' and will render the
    initial home page that show all the items in the database as well as the
    categories they fall under.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    A flask template for items.html.
    """
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).order_by(Item.name)
    users = session.query(User)
    return render_template("items.html", items=items, categories=categories,
                           users=users)

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host="0.0.0.0", port=8088)
