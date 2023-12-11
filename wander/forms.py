from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Email, Length

class RegisterForm(FlaskForm):
    """Register a new user"""

    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    email = StringField("Email", validators=[InputRequired(), Email()])
    first_name = StringField("First Name", validators=[InputRequired()])
    last_name = StringField("Last Name", validators=[InputRequired()])


class LoginForm(FlaskForm):
    """Login an existing user"""

    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])


class TripForm(FlaskForm):
    """Create a new Trip"""

    name = StringField("Trip Name", validators=[InputRequired()])
    description = StringField("Trip Description")

class PackItemForm(FlaskForm):
    """Add a new item to a packing list"""

    item_name = StringField("Item Name", validators=[InputRequired()])