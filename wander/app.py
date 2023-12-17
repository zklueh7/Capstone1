from flask import Flask, render_template, redirect, request, flash, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import User, Trip, PackItem, Stop, connect_db, db
from forms import RegisterForm, LoginForm, TripForm, PackItemForm

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///wander"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config["SECRET_KEY"] = "abc123"
toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

CURR_USER_KEY = "curr_user"


##################################################################
# User signup/login/logout

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
    """Show form to register a new user"""
    
    form = RegisterForm()

    if form.validate_on_submit():
        user = User.register(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        db.session.add(user)
        db.session.commit()

        if user:
            do_login(user)
            flash(f"Hello {user.username}", "success")
            return redirect("/")
        
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Show login for existing user and link to new user register page"""
    
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
    """Logout a user"""
    do_logout()
    flash("You have been logged out", "success")
    return redirect('/')


##################################################################
# Trip routes

@app.route('/trips')
def all_trips():
    """Show overview of all trips and link to create new trip"""
    if g.user: 
        trips = Trip.query.all()
    else: 
        flash("Login to view your trips", 'danger')
        return redirect('/login')
    return render_template('trips.html', trips=trips)


@app.route('/trips/new', methods=["GET", "POST"])
def new_trip():
    """Create a new trip"""
    if g.user:
        form = TripForm()

        if form.validate_on_submit():
            trip = Trip(name=form.name.data)
            db.session.add(trip)
            db.session.commit()
            return redirect('/trips')

        return render_template("add_trip.html", form=form)
    
    else:
        flash("Login to create a new trip", 'danger')
        return redirect('/login')
    

@app.route('/trips/<trip_id>')
def trip_detail(trip_id):
    """Show detailed view of a trip"""
    if g.user:
        trip = Trip.query.get(trip_id)
        if trip:
            stops = Stop.query.filter(Stop.trip_id == trip_id).all()
            return render_template('trip_detail.html', trip=trip, stops=stops)
        else:
            flash("Trip id doesn't exist", 'danger')
            return redirect('/trips')
    else:
        flash("Login to view your trips", 'danger')
        return redirect('/login')
    
@app.route('/trips/<trip_id>/edit', methods=["GET", "POST"])
def edit_trip(trip_id):
    """Edit a trip"""
    if g.user:
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
    else:
        flash("Login to edit your trips", 'danger')
        return redirect('/login')


@app.route('/trips/<trip_id>/delete')
def delete_trip(trip_id):
    """Delete a trip"""
    if g.user:
        trip = Trip.query.get(trip_id)
        if trip:
            db.session.delete(trip)
            db.session.commit()
            flash(f"{trip.name} has been deleted", 'success')
        else:
            flash("Trip id does not exist", 'danger')
     
        return redirect('/trips')
   
    else:    
        flash("Log in to delete trips", 'danger')
        return redirect('/login')
    

@app.route('/trips/<trip_id>/packing_list')
def packing_list(trip_id):
    """Show the packing list for the trip"""
    if g.user:
        trip = Trip.query.get(trip_id)
        form = PackItemForm()
        if trip:
            packing_list = (PackItem.query.filter(PackItem.trip_id == trip_id).order_by(PackItem.id.asc()).all())
            return render_template("packing_list.html", trip=trip, packing_list=packing_list, form=form)
        else:
            flash("Trip id does not exist", 'danger')
            return redirect('/trips')
    else:
        flash("Login to view packing lists", 'danger')
        return redirect('/login')

@app.route('/trips/<trip_id>/packing_list/add', methods=["GET", "POST"])
def packing_list_form(trip_id):
    """Add item to packing list"""
    if g.user:
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
    else:
        flash("Login to view packing lists", 'danger')
        return redirect('/login')


@app.route('/packing_list/<item_id>/delete')
def delete_pack_item(item_id):
    """Delete an item from the packing list"""
    if g.user:
        item = PackItem.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return redirect(f"/trips/{item.trip_id}/packing_list")
        else:
            flash("Item id does not exist", 'danger')
            return redirect('/trips')
    else:
        flash("Login to delete items", 'danger')
        return redirect('/login')


@app.route('/packing_list/<item_id>/update', methods=["GET", "POST"])
def update_pack_item(item_id):
    """Update the packed status of an item"""
    if g.user:
        item = PackItem.query.get(item_id)
        if item.pack_status == True:
            item.pack_status = False
        else:
            item.pack_status = True
        db.session.add(item)
        db.session.commit()
        return ("Success", 200)
    else:
        flash("Login to view packing lists", 'danger')
        return redirect('/login')

##################################################################
# Stops

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
    stop = Stop(latitude=latitude, longitude=longitude, trip_id=trip_id)
    db.session.add(stop)
    db.session.commit()
    print("hi")
    return ("Success", 200)


@app.route('/trips/<trip_id>/stops/<stop_id>/edit')
def edit_stop():
    """Edit a stop"""
    return render_template('trip_detail.html')


@app.route('/stops/<stop_id>/delete', methods=["DELETE"])
def delete_stop(stop_id):
    """Delete a stop"""
    stop = Stop.query.get(stop_id)
    db.session.delete(stop)
    db.session.commit()
    return ("Success", 200)

##################################################################
# Homepage

@app.route('/')
def homepage():
    """Homepage"""
    if g.user:
        message = f"Hi {g.user.username}!"
        return render_template("home.html", message=message)
    else:
        return render_template("home-anon.html")