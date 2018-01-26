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
engine = create_engine('postgresql://db_admin:admin@localhost:5432/catalogstore')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create debug log for capturing events that happen during execution
# Log output to file and to the console for now
logging.basicConfig(filename='logs/debug.log', filemode='a+', level=logging.DEBUG)
consoleHandler = logging.StreamHandler()
logging.getLogger('').addHandler(consoleHandler)

app = Flask(__name__)
app.secret_key = "super_secret_key"

@app.route('/')
@app.route('/catalog/')
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


@app.route('/catalog/category/<int:category_id>/')
def showItemsForCategory(category_id):
    """
    Function that handles the routes to 'catalog/category/<someCategory>' and
    will render a page that shows the items associated with a specific
    category.

    Parameters
    =======================================================
    category_id - int
        The category_id for which to show items for.

    Returns
    =======================================================
    A flask template for categoryItems.html.
    """
    categories = session.query(Category).order_by(Category.name).all()
    targetCategory = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).order_by(Item.name)
    users = session.query(User)
    return render_template("categoryItems.html",
                           items=items, categories=categories,
                           targetCategory=targetCategory, users=users)


@app.route('/catalog/JSON')
def allItemsByAllCategoryJSON():
    """
    Function that handles the routes to 'catalog/JSON' and will return a JSON
    formatted stream to the caller for all the categories and their items
    currently in the database.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    JSON formatted stream for all the categories and their items.
    """
    categories = session.query(Category).order_by(Category.name).all()
    cate_dict = [entry.serialize for entry in categories]
    index = 0
    for entry in cate_dict:
        items = session.query(Item).filter_by(
            category_id=entry["id"]).order_by(Item.name).all()
        items_dict = {"Item": [item.serialize for item in items]}
        cate_dict[index].update(items_dict)
        index += 1
    return jsonify(Category=cate_dict)


@app.route('/catalog/item/<int:item_id>/JSON')
def itemDetailsJSON(item_id):
    """
    Function that handles the routes to 'catalog/item/<someItem>/JSON' and will
    return a JSON formatted stream to the caller for all the details of a
    specific item.

    Parameters
    =======================================================
    item_id - int
        The item_id of the item in the DB to retrieve details for.

    Returns
    =======================================================
    JSON formatted stream of the items details.
    """
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/catalog/category/JSON')
def allCategoriesJSON():
    """
    Function that handles the routes to 'catalog/category/JSON' and will
    return a JSON formatted stream to the caller for all the categories
    currently in the DB.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    JSON formatted stream of the categories.
    """
    categories = session.query(Category).order_by(Category.name).all()
    return jsonify(Category=[entry.serialize for entry in categories])


@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def newItem():
    """
    Function that handles the routes to 'catalog/item/new' and will render a
    page that shows the input form for creating a new item.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    On GET - A flask template for new.html.
    On POST - A flask template for items.html.
    """
    if "username" not in login_session:
        return redirect(url_for("showAuth"))

    categories = session.query(Category).order_by(Category.name).all()
    if request.method == "POST":
        if request.form["name"]:
            logging.debug("attempting to add item - {0}".
                          format(request.form["name"]))
            try:
                existingItem = session.query(Item).filter_by(
                    name=request.form["name"]).one()
            except:
                existingItem = ""
                pass
            if not existingItem:
                try:
                    existingCategory = session.query(Category).filter_by(
                        name=request.form["category"]).one()
                except:
                    existingCategory = ""
                    pass
                if not existingCategory:
                    newCategory = Category(name=request.form["category"])
                    try:
                        session.add(newCategory)
                        # You think you need to commit this new category
                        # before adding the item because you need the unique
                        # id for the item -> category relationship.
                        # SqlAlchemy is smart enough to not need that commit
                        # call.
                        # session.commit()
                        existingCategory = session.query(Category).filter_by(
                            name=request.form["category"]).one()
                    except:
                        logging.debug("Unable to add {0} category to the DB".
                                      format(newCategory))
                        flash("Failed to add item {0}".
                              format(request.form["name"]))
                        return redirect(url_for("showItems"))

                newItem = Item(user_id=login_session["user_id"],
                               name=request.form["name"],
                               description=request.form["description"],
                               category_id=existingCategory.id)
                try:
                    session.add(newItem)
                    session.commit()
                except:
                    logging.debug("Unable to add {0} item to the DB".
                                  format(newItem))
                    flash("Failed to add item {0}".
                          format(request.form["name"]))
                    pass
            else:
                logging.debug("{0} already exists with category {1}".
                              format(request.form["name"],
                                     existingItem.category))
                flash("Failed to add item {0}".format(request.form["name"]))
                return redirect(url_for("showItems"))
        logging.debug("Item {0} was added".format(request.form["name"]))
        flash("Item {0} added to the catalog".format(request.form["name"]))
        return redirect(url_for("showItems"))
    else:
        return render_template("new.html", categories=categories)


@app.route('/catalog/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    """
    Function that handles the routes to 'catalog/item/<someItem>/edit' and will
    render a page that shows the input form for editing a specific item. Due to
    table dependencies an edit action will be processed as a delete->add
    action.

    Parameters
    =======================================================
    item_id - int
        The item_id of the item in the DB to be editted.

    Returns
    =======================================================
    On GET - A flask template for edit.html.
    On POST - A flask template for items.html.
    """
    if "username" not in login_session:
        return redirect(url_for("showAuth"))

    categories = session.query(Category).order_by(Category.name).all()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    item_name = editedItem.name

    # check to see if the current user can edit the item
    creator = getUserInfo(editedItem.user_id)
    if creator.id != login_session["user_id"]:
        logging.debug("{0} does have permission to edit the {1} item".
                      format(login_session["username"], item_name))
        flash("{0} does have permission to edit the {1} item".format(
            login_session["username"], item_name))
        return redirect(url_for("showItems"))

    if request.method == "POST":
        logging.debug("attempting to edit an item {0}".format(item_name))

        # remove the previous item and cleanup any empty category
        category = editedItem.category
        logging.debug("Deleting item {0}".format(item_name))
        session.delete(editedItem)
        # now check to see if the category needs to be removed
        itemsForCat = session.query(Item.id).join(
            Category).filter_by(name=category.name)
        # count = session.query(func.count(itemsForCat)).scalar()
        count = itemsForCat.count()
        logging.debug("{0} items left in category {1}".format(count, category.name))
        if count == 0:
            try:
                logging.debug("Deleting {0} from the DB".format(category.name))
                session.delete(category)
            except:
                logging.debug("Unable to delete {0} from the DB".
                              format(category))
                pass
        session.commit()

        # add the new item and category if they don't exist
        logging.debug("attempting to add item {0}".format(item_name))
        try:
            existingItem = session.query(Item).filter_by(name=item_name).one()
        except:
            existingItem = ""
            pass
        if not existingItem:
            try:
                existingCategory = session.query(Category).filter_by(
                    name=request.form["category"]).one()
            except:
                existingCategory = ""
                pass
            if not existingCategory:
                newCategory = Category(name=request.form["category"])
                try:
                    session.add(newCategory)
                    # You think you need to commit this new category
                    # before adding the item because you need the unique
                    # id for the item -> category relationship.
                    # SqlAlchemy is smart enough to not need that commit
                    # call.
                    # session.commit()
                    existingCategory = session.query(Category).filter_by(
                        name=request.form["category"]).one()
                    logging.debug("New category {0} created".
                                  format(newCategory.name))
                except:
                    logging.debug("Unable to add {0} category to the DB".
                                  format(newCategory))
                    flash("Failed to edit item {0}".format(item_name))
                    return redirect(url_for("showItems"))

            newItem = Item(user_id=login_session["user_id"], name=item_name,
                           description=request.form["description"],
                           category_id=existingCategory.id)
            try:
                session.add(newItem)
                session.commit()
            except:
                logging.debug("Unable to add {0} item to the DB".
                              format(newItem))
                flash("Failed to edit item {0}".format(item_name))
                pass
        else:
            loggin.debug("{0} already exists with category {1}".
                         format(item_name, existingItem.category))
            flash("Failed to edit item {0}".format(item_name))
        logging.debug("Item {0} has been editted".format(item_name))
        flash("Item {0} has been modified".format(item_name))
        return redirect(url_for("showItems"))
    else:
        return render_template("edit.html", item=editedItem,
                               categories=categories)


@app.route('/catalog/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    """
    Function that handles the routes to 'catalog/item/<someItem>/delete' and
    will render a page that shows the confirmation page for deleting a specific
    item.

    Parameters
    =======================================================
    item_id - int
        The item_id of the item in the DB to be deleted.

    Returns
    =======================================================
    On GET - A flask template for delete.html.
    On POST - A flask template for items.html.
    """
    if "username" not in login_session:
        return redirect(url_for("showAuth"))

    categories = session.query(Category).order_by(Category.name).all()
    item = session.query(Item).filter_by(id=item_id).one()
    item_name = item.name
    category = item.category

    # check to see if the current user can delete the item
    creator = getUserInfo(item.user_id)
    if creator.id != login_session["user_id"]:
        logging.debug("{0} does have permission to delete the {1} item".
                      format(login_session["username"], item_name))
        flash("{0} does have permission to delete the {1} item".format(
            login_session["username"], item_name))
        return redirect(url_for("showItems"))

    if request.method == "POST":
        logging.debug("attempting to delete an item")
        try:
            session.delete(item)
            session.commit()
        except:
            logging.debug("Unable to delete {0} from the DB".format(item))
            flash("Failed to delete item {0}".format(item_name))
            pass
        # now check to see if the category needs to be removed
        itemsForCat = session.query(Item.id).join(
            Category).filter_by(name=category.name)
        # count = session.query(func.count(itemsForCat)).scalar()
        count = itemsForCat.count()
        logging.debug("{0} items left in category {1}".format(count, category.name))
        if count == 0:
            try:
                logging.debug("Deleting {0} from the DB".format(category.name))
                session.delete(category)
                session.commit()
            except:
                logging.debug("Unable to delete {0} from the DB".
                              format(category))
                pass

        logging.debug("Item {0} has been deleted".format(item_name))
        flash("Item {0} has been removed".format(item_name))
        return redirect(url_for("showItems"))
    else:
        return render_template("delete.html", item=item, categories=categories)


@app.route('/auth/')
def showAuth():
    """
    Function that handles the routes to '/auth/' and will render a page that
    shows the prompts for signing in/logging in to the site via Facebook or
    Google credentials.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    A flask template for authenticate.html.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session["state"] = state
    logging.debug("Authentication Session {0} started".format(login_session["state"]))
    # return "The current session state is %s" % login_session["state"]
    return render_template("authenticate.html", STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Function that handles the routes to '/gconnect/' and will process the oauth
    session and flow with Google for users attempting to sign in/login to the
    Catalog App using their Google credentials.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    A string output of HTML syntax and text that is used by on the
    authenticate.html page to indicate success or failure.
    """
    # Validate state token
    sessionState = request.args.get('state')
    logging.debug("Google OAuth2 phase started for session {0}".format(sessionState))
    if sessionState != login_session["state"]:
        response = make_response(json.dumps("Invalid state parameter."), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            "google_client_secrets.json", scope='')
        oauth_flow.redirect_uri = "postmessage"
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        logging.debug("Failed to upgrade the auth code")
        response = make_response(json.dumps(
            "Failed to upgrade the authorization code."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ("https://www.googleapis.com/"
           "oauth2/v1/tokeninfo?access_token={0}".format(access_token))

    h = httplib2.Http()

    result = json.loads(h.request(url, "GET")[1].decode('utf-8'))
    # If there was an error in the access token info, abort.
    if result.get("error") is not None:
        logging.debug("Error in the access info token")
        logging.debug(result)
        response = make_response(json.dumps(result.get("error")), 500)
        response.headers["Content-Type"] = "application/json"
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token["sub"]
    if result["user_id"] != gplus_id:
        logging.debug("Access token from Google doesn't match user ID")
        response = make_response(json.dumps(
            "Token's user ID doesn't match given user ID."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Verify that the access token is valid for this app.
    if result["issued_to"] != CLIENT_ID:
        logging.debug("Access token clientID from Google doesn't match app's")
        response = make_response(json.dumps(
            "Token's client ID does not match app's."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    stored_access_token = login_session.get("access_token")
    stored_gplus_id = login_session.get("gplus_id")
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        logging.debug("User has already connected")
        response = make_response(json.dumps(
            "Current user is already connected."), 200)
        response.headers["Content-Type"] = "application/json"
        return response

    # Store the access token in the session for later use.
    login_session["access_token"] = credentials.access_token
    login_session["gplus_id"] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials.access_token, "alt": "json"}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session["provider"] = "google"
    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]
    login_session["email"] = data["email"]

    # check to see if user already exists and add into the User table if not
    user_id = getUserID(login_session["email"])
    if user_id is None:
        user_id = createUser(login_session)
        logging.debug("New user signed up {0}".format(user_id))
    else:
        logging.debug("User {0} has connected".format(user_id))
    login_session["user_id"] = user_id

    output = ''
    output += "<h1>Welcome, "
    output += login_session["username"]
    output += "!</h1>"
    output += '<img src="'
    output += login_session["picture"]
    output += ' " style = "width: 300px; height: 300px;'          \
              'border-radius:150px;-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;"> '
    flash("{0} has the power to create".format(login_session["username"]))
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    Function that handles the routes to '/gdisconect/' and will process the
    disconnection from the Google oauth backend.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    Nothing on success.
    On failure to disconnect returns a response object to redirect the user to
    the items.html page.
    """
    access_token = login_session.get("access_token")
    if access_token is None:
        logging.debug("Access Token is None")
        flash("There was an issue logging out")
        return redirect(url_for("showItems"))
    logging.debug("In gdisconnect access token is {0}".format(access_token))
    logging.debug("User name is: ")
    logging.debug(login_session["username"])
    url = ("https://accounts.google.com/"
           "o/oauth2/revoke?token={0}".format(login_session["access_token"]))
    h = httplib2.Http()
    result = h.request(url, "GET")[0]
    logging.debug("result is {0}".format(result))
    return


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """
    Function that handles the routes to '/fbconnect/' and will process the
    oauth session and flow with Facebook for users attempting to sign in/login
    to the Catalog App using their Facebook credentials.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    A string output of HTML syntax and text that is used by on the
    authenticate.html page to indicate success or failure.
    """
    sessionState = request.args.get('state')
    logging.debug("Facebook OAuth2 phase started for session {0}".format(sessionState))

    if sessionState != login_session["state"]:
        logging.debug("Invalid state parameter")
        response = make_response(json.dumps("Invalid state parameter."), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    access_token = (request.data).decode('utf-8')
    logging.debug("access token received {0} ".format(access_token))

    app_id = json.loads(open("fb_client_secrets.json", "r").read())[
        "web"]["app_id"]
    app_secret = json.loads(open("fb_client_secrets.json", "r").read())[
        "web"]["app_secret"]
    url = ("https://graph.facebook.com/"
           "oauth/access_token?grant_type=fb_exchange_token"
           "&client_id={0}&client_secret={1}&fb_exchange_token={2}".
           format(app_id, app_secret, access_token))

    h = httplib2.Http()
    result = h.request(url, "GET")[1].decode('utf-8')

    # Use token to get user info from API
    # Due to the formatting for the result from the server token exchange we
    # have to split the token first on commas and select the first index which
    # gives us the key : value for the server access token then we split it on
    # colons to pull out the actual token value  and replace the remaining
    # quotes with nothing so that it can be used directly in the graph api
    # calls
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = ("https://graph.facebook.com/"
           "v2.10/me?access_token={0}&fields=name,id,email".format(token))
    h = httplib2.Http()
    result = h.request(url, "GET")[1].decode('utf-8')
    data = json.loads(result)
    logging.debug(data)
    login_session["provider"] = "facebook"
    login_session["username"] = data["name"]
    login_session["email"] = data["email"]
    login_session["facebook_id"] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session["access_token"] = token

    # Get user picture
    url = ("https://graph.facebook.com/"
           "v2.10/me/picture?access_token={0}"
           "&redirect=0&height=200&width=200".format(token))
    h = httplib2.Http()
    result = h.request(url, "GET")[1].decode('utf-8')
    data = json.loads(result)

    login_session["picture"] = data["data"]["url"]

    # check to see if user already exists and add into the User table if not
    user_id = getUserID(login_session["email"])
    if user_id is None:
        user_id = createUser(login_session)
        logging.debug("New user signed up {0}".format(user_id))
    else:
        logging.debug("User {0} has connected".format(user_id))

    login_session["user_id"] = user_id

    output = ""
    output += "<h1>Welcome, "
    output += login_session["username"]

    output += "!</h1>"
    output += '<img src="'
    output += login_session["picture"]
    output += ' " style = "width: 300px; height: 300px;'           \
              'border-radius: 150px;-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;"> '

    flash("{0} has the power to create".format(login_session["username"]))
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    """
    Function that handles the routes to '/fbdisconect/' and will process the
    disconnection from the Facebook oauth backend.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    Nothing on success.
    """
    facebook_id = login_session["facebook_id"]
    # The access token must me included to successfully logout
    access_token = login_session["access_token"]
    url = ("https://graph.facebook.com/"
           "{0}/permissions?access_token={1}".
           format(facebook_id, access_token))
    h = httplib2.Http()
    result = h.request(url, "DELETE")[1]
    logging.debug("result is {0}".format(result))
    return


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    """
    Function that handles the routes to '/disconect/' and will process the
    disconnection from either the Google or Facebook oauth backend depending on
    which is currently in use in the current session.

    Parameters
    =======================================================
    None

    Returns
    =======================================================
    A response object to redirect the user to the items.html page.
    """
    if "provider" in login_session:
        logging.debug("User {0} is logging out".
                      format(login_session["user_id"]))
        if login_session["provider"] == "google":
            gdisconnect()
            del login_session["gplus_id"]
            del login_session["access_token"]
        if login_session["provider"] == "facebook":
            fbdisconnect()
            del login_session["facebook_id"]
        del login_session["username"]
        del login_session["email"]
        del login_session["picture"]
        del login_session["user_id"]
        del login_session["provider"]
        flash("You are a mere mortal")
        return redirect(url_for("showItems"))
    else:
        logging.debug("None auth'd user attempting to logout")
        flash("You were not logged in")
        return redirect(url_for("showItems"))

# User Helper Functions
# Create a new user


def createUser(login_session):
    """
    Function to create a new user in the DB.

    Parameters
    =======================================================
    login_session - flask session object
        The current session for which a user is attempting to sign in/login
        with.

    Returns
    =======================================================
    int -
        The user.id value of the new user object added to the DB
    """
    newUser = User(name=login_session["username"],
                   email=login_session["email"],
                   picture=login_session["picture"])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session["email"]).one()
    return user.id


def getUserInfo(user_id):
    """
    Function to retrieve the User object for a specific user being stored in
    the DB.

    Parameters
    =======================================================
    user_id - int
        The user_id of the User to be retrieved from the DB.

    Returns
    =======================================================
    User Object -
        The User object associated with the specified user_id.
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """
    Function to retrieve the user.id for a specific User being stored in the
    DB based on an email address.

    Parameters
    =======================================================
    email - string
        The email address of the User to be retrieved from the DB.

    Returns
    =======================================================
    int -
        The user.id value of the User object associated with the specified
        email address
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=8088)
