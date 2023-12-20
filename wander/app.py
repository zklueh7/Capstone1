from flask import Flask, render_template, redirect, request, flash, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import User, Trip, PackItem, Stop, ItineraryItem, connect_db, db
from forms import RegisterForm, LoginForm, TripForm, PackItemForm, StopForm, ItineraryItemForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///wander"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config["SECRET_KEY"] = "abc123"
toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

CURR_USER_KEY = "curr_user"


##################################################################
# User signup/login/logout/homepage routes

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.username

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/register', methods=["GET", "POST"])
def register():
    """Handle new user signup. Create new user, add to DB, and redirect to home page
    If form not valid, present form
    If there is already a user with that username, flash error message and
    re-present form"""
    
    form = RegisterForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template("register.html", form=form)

        do_login(user)
        flash(f"Hello {user.username}", "success")
        return redirect("/")

    else:    
        return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle existing user login"""
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        if user:
            do_login(user)
            return redirect("/")
        
        flash("Invalid credentials.", 'danger')

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    """Handle logout of a user"""

    do_logout()
    flash("You have been logged out", "success")
    return redirect('/')

@app.route('/')
def homepage():
    """Homepage"""

    if g.user:
        message = f"Hi {g.user.username}!"
        return render_template("home.html", message=message)
    else:
        return render_template("home-anon.html")


##################################################################
# Trip routes

@app.route('/trips')
def all_trips():
    """Show overview of all trips and link to create new trip"""
    
    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    trips = Trip.query.filter(Trip.username == g.user.username).all()
    return render_template('trips.html', trips=trips)


@app.route('/trips/new', methods=["GET", "POST"])
def new_trip():
    """Create a new trip"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = TripForm()

    if form.validate_on_submit():
        trip = Trip(name=form.name.data, username=g.user.username)
        db.session.add(trip)
        db.session.commit()
        return redirect('/trips')

    return render_template("add_trip.html", form=form)
    
    

@app.route('/trips/<trip_id>')
def trip_detail(trip_id):
    """Show detailed view of a trip"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    trip = Trip.query.get(trip_id)
    if trip:
        stops = Stop.query.filter(Stop.trip_id == trip_id).order_by(Stop.id.asc()).all()
        return render_template('trip_detail.html', trip=trip, stops=stops)
    else:
        flash("Trip id doesn't exist", 'danger')
        return redirect('/trips')

    
@app.route('/trips/<trip_id>/edit', methods=["GET", "POST"])
def edit_trip(trip_id):
    """Edit a trip"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    trip = Trip.query.get(trip_id)
    form = TripForm()
    if trip:
        if form.validate_on_submit():
            trip.name=form.name.data,
            trip.description=form.description.data
            db.session.add(trip)
            db.session.commit()
            flash("Trip edited", 'success')
            return redirect('/trips')
        return render_template('edit_trip.html', form=form, trip=trip)
    else:
        flash("Trip id does not exist", 'danger')
        return redirect('/trips')


@app.route('/trips/<trip_id>/delete')
def delete_trip(trip_id):
    """Delete a trip"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    trip = Trip.query.get(trip_id)
    if trip:
        db.session.delete(trip)
        db.session.commit()
        flash(f"{trip.name} has been deleted", 'success')
    else:
        flash("Trip id does not exist", 'danger')
        return redirect('/trips')
   

##################################################################
# Packing list routes

@app.route('/trips/<trip_id>/packing_list')
def packing_list(trip_id):
    """Show the packing list for the trip"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    trip = Trip.query.get(trip_id)
    if trip:
        packing_list = (PackItem.query.filter(PackItem.trip_id == trip_id).order_by(PackItem.id.asc()).all())
        return render_template("packing_list.html", trip=trip, packing_list=packing_list)
    else:
        flash("Trip id does not exist", 'danger')
        return redirect('/trips')


@app.route('/trips/<trip_id>/packing_list/add', methods=["GET", "POST"])
def packing_list_form(trip_id):
    """Add item to packing list"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    trip = Trip.query.get(trip_id)
    form = PackItemForm()
    if trip:
        if form.validate_on_submit():
            item = PackItem(trip_id=trip_id, item_name=form.item_name.data, pack_status=False)
            db.session.add(item)
            db.session.commit()
            return redirect(f'/trips/{trip_id}/packing_list')
        return render_template("packing_list_form.html", trip=trip, packing_list=packing_list, form=form)
    else:
        flash("Trip id does not exist", 'danger')
        return redirect('/trips')


@app.route('/packing_list/<item_id>/delete')
def delete_pack_item(item_id):
    """Delete an item from the packing list"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    item = PackItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return redirect(f"/trips/{item.trip_id}/packing_list")
    else:
        flash("Item id does not exist", 'danger')
        return redirect('/trips')


@app.route('/packing_list/<item_id>/update', methods=["GET", "POST"])
def update_pack_item(item_id):
    """Update the packed status of an item"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    item = PackItem.query.get(item_id)
    if item.pack_status == True:
        item.pack_status = False
    else:
        item.pack_status = True
    db.session.add(item)
    db.session.commit()
    return ("Success", 200)


##################################################################
# Stop routes

@app.route('/trips/<trip_id>/stops')
def get_stops(trip_id):
    """Return stops for trip"""

    stops = [stop.serialize() for stop in Stop.query.filter(Stop.trip_id == trip_id).order_by(Stop.id.asc()).all()]
    return jsonify(stops=stops)


@app.route('/trips/<trip_id>/stops/new', methods=["GET", "POST"])
def new_stop(trip_id):
    """Create a new stop"""

    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    stop_name = request.args.get('stop_name')
    stop = Stop(latitude=latitude, longitude=longitude, stop_name=stop_name, trip_id=trip_id)
    db.session.add(stop)
    db.session.commit()
    return jsonify(stop_id=stop.id)


@app.route('/stops/<stop_id>/edit', methods=["GET", "POST"])
def edit_stop(stop_id):
    """Edit a stop"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = StopForm()
    stop = Stop.query.get(stop_id)
    trip_id = stop.trip_id
    if form.validate_on_submit():
        stop.stop_name=form.stop_name.data
        db.session.add(stop)
        db.session.commit()
        return redirect(f'/trips/{trip_id}')
    return render_template('edit_stop.html', form=form, stop=stop)


@app.route('/stops/<stop_id>/delete', methods=["DELETE"])
def delete_stop(stop_id):
    """Delete a stop"""

    stop = Stop.query.get(stop_id)
    db.session.delete(stop)
    db.session.commit()
    return ("Success", 200)

##################################################################
# Itinerary Routes

@app.route('/stops/<stop_id>/itinerary')
def itinerary(stop_id):
    """Show the itinerary for a stop"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    stop = Stop.query.get(stop_id)

    if stop:
        itinerary = (ItineraryItem.query.filter(ItineraryItem.stop_id == stop_id).order_by(ItineraryItem.id.asc()).all())
        return render_template("itinerary.html", stop=stop, itinerary=itinerary)
    else:
        flash("Stop id does not exist", 'danger')
        return redirect('/trips')
    

@app.route('/stops/<stop_id>/itinerary/add', methods=["GET", "POST"])
def itinerary_form(stop_id):
    """Add item to the itinerary"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    stop = Stop.query.get(stop_id)
    form = ItineraryItemForm()
    if stop:
        if form.validate_on_submit():
            item = ItineraryItem(stop_id=stop_id, item_name=form.item_name.data)
            db.session.add(item)
            db.session.commit()
            return redirect(f'/stops/{stop_id}/itinerary')
        return render_template("itinerary_form.html", stop=stop, form=form)
    else:
        flash("Stop id does not exist", 'danger')
        return redirect('/trips')
    

@app.route('/itinerary/<item_id>/delete')
def delete_itinerary_item(item_id):
    """Delete an item from an itinerary"""

    if not g.user: 
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    item = ItineraryItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return redirect(f"/stops/{item.stop_id}/itinerary")
    else:
        flash("Item id does not exist", 'danger')
        return redirect('/trips')