# Dependencies
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///./Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

def latestDate():
     # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a dictionary of date and precipitation data for the last 12 months"""
    # Find the most recent date in the data set.
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date
    # Transform string into datetime object
    datetime_object = datetime.strptime(most_recent_date[0], '%Y-%m-%d')
    # Get the date from one year from the last date 
    query_date = datetime_object - relativedelta(years=1)
    
    query_date_string = query_date.strftime('%Y-%m-%d')
    session.close()
    return query_date_string

def mostActiveStations():
    session = Session(engine)

    """Return a list of all stations"""
    # Query the most active station
    most_active_stations = session.query(Measurement.station, func.count(Measurement.tobs)).group_by(Measurement.station).\
    order_by(func.count(Measurement.tobs).desc()).all()
    session.close()
    return most_active_stations

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/mostactivestations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_dateend_date<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
     # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a dictionary of date and precipitation data for the last 12 months"""
    query_date_string = latestDate()
    # Perform a query to retrieve the data and precipitation scores
    last_year_prcp_scores = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= query_date_string).order_by(Measurement.date).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_passengers
    precipitation = []
    for date, prcp in last_year_prcp_scores:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["precipitation"] = prcp
        
        precipitation.append(prcp_dict)

    return jsonify(precipitation)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    stations = {}

    # Query all stations
    results = session.query(Station.station, Station.name).all()
    for s,name in results:
        stations[s] = name

    session.close()

    return jsonify(stations)

@app.route("/api/v1.0/mostactivestations")
def mostactivestations():
    # Create our session (link) from Python to the DB

    """Return a list of all stations"""
    # Query the most active station
    most_active_stations = mostActiveStations()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(most_active_stations))

    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    most_active_stations = mostActiveStations()
    query_date_string = latestDate()

    tobs_most_active_station_prev_year = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_stations[0][0],\
                                                                            Measurement.station == Station.station, \
                                                                            Measurement.date >= query_date_string).all()
    session.close()
    # Convert to list of dictionaries to jsonify
    tobs_previous_year = []

    for date, tobs in tobs_most_active_station_prev_year:
        new_dict = {}
        new_dict[date] = tobs
        tobs_previous_year.append(new_dict)

    return jsonify(tobs_previous_year)


@app.route("/api/v1.0/<start>")
def analysis(start):
    """TMIN, TAVG, and TMAX per date starting from a starting date.
    
    Args:
        start (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """

     # Create our session (link) from Python to the DB
    session = Session(engine)
    
    sel = [func.min(Measurement.tobs), \
            func.avg(Measurement.tobs), \
            func.max(Measurement.tobs)] 
    results = session.query(*sel).filter(Measurement.date >= start).all()
    
    session.close()
    analysis_from_start_date = []
    for min, avg, max in results:
        new_dict = {}
        new_dict["TMIN"] = min
        new_dict["TAVG"] = avg
        new_dict["TMAX"] = max
        analysis_from_start_date.append(new_dict)
    return jsonify(analysis_from_start_date)

@app.route("/api/v1.0/<start>/<end>")
def startend(start, end):
    """TMIN, TAVG, and TMAX per date for a date range.
    
    Args:
        start (string): A date string in the format %Y-%m-%d
        end (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """

    # Create our session (link) from Python to the DB
    session = Session(engine)
    sel = [func.min(Measurement.tobs), \
            func.avg(Measurement.tobs), \
            func.max(Measurement.tobs)] 
    results = session.query(*sel).filter(Measurement.date >= start, Measurement.date <= end).all()
    
    session.close()

    analysis_from_start_date_to_end_date = []
    for min, avg, max in results:
        new_dict = {}
        new_dict["TMIN"] = min
        new_dict["TAVG"] = avg
        new_dict["TMAX"] = max
        analysis_from_start_date_to_end_date.append(new_dict)
    return jsonify(analysis_from_start_date_to_end_date)

if __name__ == "__main__":
    app.run(debug=True)
