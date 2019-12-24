#!/usr/bin/python2

from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   make_response,
                   flash)
from flask import session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import func
from database_setup import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import httplib2
import json
import requests


app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Connect to Database and create database session
engine = create_engine('postgres://osema:RanDom_123@localhost:5432/catalog')
Base.metadata.bind = engine

# create scoped session to allow multi-threads
session_factory = sessionmaker(bind=engine)
session = scoped_session(session_factory)

# Login page
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, client_id=CLIENT_ID)


# Create a new user and store it in database.
def create_user(login_session):
    """Create and store a new user."""
    new_user = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture']
    )
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Check if user exist and return his ID.
def get_user_id(email):
    """Get user ID or None"""

    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Connect to Google sign-in.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # Get user info.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # Assing Email as name if User does not have Google+
    login_session['username'] = data.get('name', 'No Name')
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if the user exists. If it doesn't, make a new one.
    user_id = get_user_id(data["email"])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    # Show a welcome screen upon successful login.
    output = ''
    output += '<h2>Welcome, '
    output += login_session['username']
    output += '!</h2>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; '
    output += 'border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("You are now logged in as %s!" % login_session['username'])
    return output


# Disconnect from Google.
def gdisconnect():
    """Disconnect the Google account of the current logged-in user."""

    # Only disconnect the connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Route to disconnect from Google.
@app.route('/logout')
def logout():
    """Log out the currently connected user."""

    if 'username' in login_session:
        gdisconnect()
        del login_session['google_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        flash("You have been successfully logged out!")
        return redirect(url_for('showIndex'))
    else:
        flash("You were not logged in!")
        return redirect(url_for('showIndex'))


# Home page to view all categories and last items.
@app.route('/')
def showIndex():
    """Show home page."""
    categories = session.query(Category).all()
    last_items = session.query(Item).order_by(
        desc(Item.creation_time)).limit(10)
    return render_template('index.html',
                           categories=categories, last_items=last_items)


# Show an item of given category.
@app.route('/catalog/<string:cat_name>/items')
def showCatalog(cat_name):
    """show informations items of given category"""
    category = session.query(Category).filter(
        Category.name == cat_name).first()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('catalog_list.html', category=category, items=items)


# API to get all items of category cat_name.
@app.route('/catalog/<string:cat_name>/items/json')
def showCatalogJson(cat_name):
    """this api shows all items of specific category"""
    category = session.query(Category).filter(
        Category.name == cat_name).first()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return jsonify(items=[i.serialize for i in items])


# Show specific catalog item.
@app.route('/catalog/<string:cat_name>/<string:item_name>')
def showItem(cat_name, item_name):
    """Show information of item of given category."""
    category = session.query(Category).filter(
        Category.name == cat_name).first()
    item = session.query(Item).filter(
        Item.category_id == category.id).filter(
            Item.name == item_name).one_or_none()
    return render_template('item.html', category=category, item=item)


# API to get a specific item.
@app.route('/catalog/<string:cat_name>/<string:item_name>/json')
def showItemJson(cat_name, item_name):
    """get information of item of given category."""
    category = session.query(Category).filter(
        Category.name == cat_name).first()
    item = session.query(Item).filter(
        Item.category_id == category.id).filter(
            Item.name == item_name).one_or_none()
    return jsonify(item=item.serialize)


# Delete catalogue item having id of item_id.
@app.route('/catalog/delete/<int:item_id>', methods=['GET', 'POST'])
def deleteItem(item_id):
    """Delete item having id == item_id."""

    if 'username' not in login_session:
        flash("Non loged in users can't delete items, login to continue.")
        return redirect(url_for('showIndex'))

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.user_id:
        flash("You are not the author of this item, you can't delete it.")
        return redirect(url_for('showIndex'))

    item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(item)
        flash('%s Successfully Deleted' % item.name)
        session.commit()
        return redirect(url_for('showIndex'))
    else:
        return render_template('delete_item.html', item=item)


# Edit specific item.
@app.route('/catalog/<string:item_name>/<int:item_id>',
           methods=['GET', 'POST'])
def editItem(item_id, item_name):

    if 'username' not in login_session:
        flash("Non loged in users can't edit items, login to continue.")
        return redirect(url_for('showIndex'))

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.user_id:
        flash("You are not the author of this item, you can't edit it.")
        return redirect(url_for('showIndex'))

    categories = session.query(Category).all()
    try:
        item = session.query(Item).filter(Item.id == item_id).one()
    except:
        flash("This item does not exist..." +
              "you can't modify non existing item!")
        return redirect(url_for('showIndex'))

    if request.method == 'POST':
        category = session.query(Category).filter(
            Category.name == request.form["category"]).first()
        if (not category):
            flash('this category doesn\'t exist, try choosing from the list')
            return render_template('edit_item.html', categories)
        try:
            editedItem = session.query(Item).filter_by(id=item_id).one()
        except:
            flash("This item does not exist..." +
                  "you can't modify non existing item!")
            return render_template("edit_item.html")

        editedItem.name = request.form['name']
        editedItem.description = request.form['description']
        editedItem.category_id = category.id
        editedItem.creation_time = func.now()
        session.add(editedItem)
        session.commit()
        flash('New Item Successfully Created')
        return redirect(url_for('showIndex'))
    else:
        return render_template('edit_item.html',
                               categories=categories, item=item)


# Add item.
@app.route('/catalog/addItem', methods=['GET', 'POST'])
def addItem():

    if 'username' not in login_session:
        flash("Non loged in users can't add items, login to continue.")
        return redirect(url_for('showIndex'))

    if request.method == 'POST':
        category = session.query(Category).filter(
            Category.name == request.form["category"]).first()
        if (not category):
            flash('this category doesn\'t exist, try choosing from the list')
            categories = session.query(Category).all()
            return render_template('add_item.html', categories)

        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=category.id,
                       user_id=login_session['user_id']
                       )
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showIndex'))
    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories)


# API showing all categories in DB with their items.
@app.route("/catalog.json")
def allCatalog():
    categories = session.query(Category).all()
    for category in categories:
        items = session.query(Item).filter(
            Item.category_id == category.id).all()
        serialized_items = [i.serialize for i in items]
        category.items = serialized_items
    return jsonify(Category=[i.serialize for i in categories])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000, debug=True)
