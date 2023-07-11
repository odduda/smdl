import mimetypes
import sqlite3
import requests
import os.path
from flask import Flask, request, g, render_template
from datetime import datetime
from serialize import BaseSerializer
from db.init_db import initialize_database

DATABASE = "db/database.db3"
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
app = Flask(__name__)

def get_db():
    if not os.path.exists(DATABASE):
        initialize_database()
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


@app.errorhandler(404)
def error_404(error):
    return render_template("404.html"), 404


@app.errorhandler(400)
def error_400(error):
    return ["Bad Request"], 400


@app.errorhandler(500)
def error_500(error):
    return ["Server error"], 500


def server_exist(server_id):
    cur = get_db().cursor()
    sql = f"SELECT 1 FROM server WHERE id = '{server_id}'"
    return cur.execute(sql).fetchone()


def csms_exist(server_id, csms_name):
    cur = get_db().cursor()
    sql = f"SELECT 1 FROM csms WHERE server_id = '{server_id}' AND name = '{csms_name}'"
    return cur.execute(sql).fetchone()


@app.get("/")
def home(server_id=None):
    return render_template("index.html")


@app.get("/server/<int:server_id>")
def server(server_id):
    check = server_exist(server_id)
    if check is None:
        return error_404(404)
    aht = get_server_aht(server_id)
    csms = get_server_csms(server_id)
    settings = get_server_settings(server_id)
    logs = get_server_log(server_id)
    get_interval(server_id)
    return render_template(
        "server.html",
        data={
            "csms": {**csms},
            "logs": logs,
            "server_id": server_id,
            **aht,
            **settings,
        },
    )


@app.get("/server/<int:server_id>/csms/<string:csms>")
def csms(server_id, csms):
    check = csms_exist(server_id, csms)
    if check is None:
        return error_404(404)
    aht = get_server_aht(server_id)
    settings = get_server_settings(server_id)
    return render_template(
        "graph.html",
        data={
            "title": csms,
            "server_id": server_id,
            **aht,
            **settings,
        },
    )


@app.get("/server/<int:server_id>/aht")
def aht(server_id):
    check = server_exist(server_id)
    if check is None:
        return error_404(404)
    aht = get_server_aht(server_id)
    settings = get_server_settings(server_id)
    return render_template(
        "graph.html",
        data={
            "title": "Temperature and Humidity",
            "server_id": server_id,
            **aht,
            **settings,
        },
    )

@app.post("/api/server")
def add_server():
    # Create new server
    con = get_db()
    cur = con.cursor()
    js = request.json
    check = {
        "name": "rq",
        "latitude": "rq:float",
        "longitude": "rq:float",
        "dayInterval": "rq:int",
        "nightInterval": "rq:int",
    }
    serializer = BaseSerializer(check, js)
    if serializer.errors:
        return serializer.errors, 400
    query = cur.execute(
        f"""SELECT id FROM server WHERE name = '{js["name"].upper()}' LIMIT 1"""
    ).fetchone()
    if query:
        return ["Server name id already exist"], 400

    insert_sql = f"""
        INSERT INTO server (
            name,
            calibrate,
            lat,
            lng,
            day_interval,
            night_interval
        )
        VALUES ( 
            '{js["name"].upper()}',
            '0',
            '{js["latitude"]}',
            '{js["longitude"]}',
            '{js["dayInterval"]}',
            '{js["nightInterval"]}'
        );
        """
    try:
        cur.execute(insert_sql)
        con.commit()
    except Exception:
        return [], 500
    return [], 200


@app.get("/api/server")
def get_server_list():
    con = get_db()
    cur = con.cursor()
    query_str = """
        SELECT
        server.id as id,
        server.name as name,
        aht.humidity as hum,
        aht.temperature as tmp
        FROM server
        LEFT JOIN aht
        ON aht.id = (
            SELECT id 
            FROM aht 
            WHERE server_id = server.id 
            ORDER BY aht.created DESC 
            LIMIT 1
            )
        ORDER BY server.id DESC
    """
    query = cur.execute(query_str).fetchall()
    if not query:
        return [], 200
    return [dict(q) for q in query]


@app.get("/api/server/<int:server_id>/latest")
def latest(server_id):
    settings = get_server_settings(server_id)
    csms = (
        get_server_csms_tmp(server_id)
        if settings["calibrate"]
        else get_server_csms(server_id)
    )
    aht = get_server_aht(server_id)
    return {"csms": csms, "aht": aht, "calibrate": settings["calibrate"]}


@app.post("/api/server/<int:server_id>/update")
def update_server(server_id):
    con = get_db()
    cur = con.cursor()
    check = {
        "latitude": "rq:float",
        "longitude": "rq:float",
        "dayInterval": "rq:int",
        "nightInterval": "rq:int",
    }
    serializer = BaseSerializer(check, request.json)
    if serializer.errors:
        return serializer.errors, 400
    update_sql = f"""
        UPDATE server
        SET 
            lat = '{request.json["latitude"]}',
            lng = '{request.json["longitude"]}',
            day_interval = '{request.json["dayInterval"]}',
            night_interval = '{request.json["nightInterval"]}'
        WHERE id = '{server_id}';
        """
    cur.execute(update_sql)
    con.commit()
    return [], 200


@app.get("/api/server/<int:server_id>/delete")
def delete_server(server_id):
    con = get_db()
    cur = con.cursor()
    exist = cur.execute(f"SELECT 1 FROM server WHERE id = '{server_id}'").fetchone()
    if exist is None:
        return ["Error"], 400
    csms_query = cur.execute(f"SELECT id FROM csms WHERE server_id = '{server_id}'")
    csms = "".join(f"{csms['id']}," for csms in csms_query)
    cur.executescript(
        f"""
        BEGIN TRANSACTION;
        DELETE FROM aht WHERE server_id = '{server_id}';
        DELETE FROM csms WHERE server_id = '{server_id}';
        DELETE FROM log WHERE server_id = '{server_id}';
        DELETE FROM sas WHERE server_id = '{server_id}';
        DELETE FROM server WHERE id = '{server_id}';
        DELETE FROM csms_calibration WHERE csms_id in ({csms[:-1]});
        DELETE FROM csms_data WHERE csms_id in ({csms[:-1]});
        COMMIT;
        """
    )
    try:
        con.commit()
        return [], 200
    except Exception:
        return [], 500


@app.get("/api/server/<int:server_id>/aht")
def get_server_aht(server_id):
    # Get aht -- humidity, temperature
    con = get_db()
    cur = con.cursor()
    sql = f"""
        SELECT 
            server.name, 
            printf("%.1f", aht.temperature) as temperature,
            printf("%.1f", aht.humidity) as humidity
        FROM server
        LEFT JOIN aht
        ON server.id = aht.server_id
        WHERE server.id = '{server_id}'
        ORDER BY aht.created DESC
        LIMIT 1;
        """
    query = cur.execute(sql).fetchone()
    if query is None:
        return {}
    data = {**query}
    return data


@app.post("/api/server/<int:server_id>/aht")
def post_server_aht(server_id):
    con = get_db()
    cur = con.cursor()
    sql = f"""
        INSERT INTO aht (server_id, temperature, humidity)
        VALUES(
            '{server_id}',
            '{request.json["temperature"]}',
            '{request.json["humidity"]}'
        )
        """
    cur.execute(sql)
    try:
        con.commit()
    except Exception:
        return [], 400
    return [], 200


@app.get("/api/server/<int:server_id>/settings")
def get_server_settings(server_id):
    # Get server settings
    con = get_db()
    cur = con.cursor()
    sql = f"""
        SELECT calibrate, lat, lng, day_interval, night_interval, updated
        FROM server
        WHERE id = '{server_id}';
        """
    settings = cur.execute(sql).fetchone()
    # TODO OVO SREDI
    if not check_sas(server_id):
        sas_api_update(server_id)
    sas = get_sas(server_id)
    sas = {**sas}
    response = {**settings, **sas}
    return response


@app.get("/api/server/name/<string:name>")
def get_server_id_by_name(name):
    # Get Server id by server name
    cur = get_db().cursor()
    sql = f"""
        SELECT id
        FROM server
        WHERE name = '{name.upper()}'
        """
    server_id = cur.execute(sql).fetchone()
    if server_id is None:
        return [], 400
    return [server_id[0]], 200


@app.post("/api/server/<int:server_id>/csms")
def csms_add(server_id):
    """
    Add csms data
    :request.json["data"] = ["x48:0", "x48:1", etc]

    """
    con = get_db()
    cur = con.cursor()
    calibrate = cur.execute(
        f"SELECT calibrate FROM server WHERE id = {server_id}"
    ).fetchone()
    if calibrate is None:
        return [], 400
    sql = """
            INSERT INTO csms_data
            (csms_id, csms_calibration_id, value)
            VALUES(
                (
                SELECT id FROM csms WHERE name = '{1}' AND server_id = '{0}'
                ),
                (
                SELECT id FROM csms_calibration WHERE csms_id =
                    (
                    SELECT id FROM csms WHERE name = '{1}' AND server_id = '{0}'
                    )
                ORDER BY created DESC LIMIT 1
                ),
                '{2}'
            )
            """

    sql_tmp = """
                INSERT INTO csms_data_tmp
                (csms_id, value)
                VALUES(
                    (
                    SELECT id FROM csms WHERE name = '{1}' AND server_id = '{0}'
                    ),
                    '{2}'
                )
                """
    for csms_name, value in request.json.items():
        if bool(calibrate[0]):
            cur.execute(sql_tmp.format(server_id, csms_name, value))
        else:
            cur.execute(sql.format(server_id, csms_name, value))
    try:
        con.commit()
    except Exception:
        return [], 400
    return {**get_interval(server_id), "calibrate": bool(calibrate[0])}, 200


@app.get("/api/server/<int:server_id>/csms")
def get_server_csms(server_id):
    # Get csms data
    con = get_db()
    cur = con.cursor()
    csms_query = cur.execute(
        f"""
        SELECT id
        FROM csms
        WHERE server_id = '{server_id}'
        """
    ).fetchall()
    if not csms_query:
        return {}
    tmp = []
    for csms in csms_query:
        data_sql = f"""
            SELECT 
                csms.name,
                csms_data.value as raw_value,
                printf('%,d', (100 - (
                    CAST(csms_data.value - csms_calibration.min AS FLOAT) 
                    / (csms_calibration.max - csms_calibration.min)) * 100) ) as value,
                strftime(
                    '%d/%m/%Y %H:%M:%S',
                    datetime(csms_data.created, 'unixepoch', 'localtime')) 
                    as last_updated,
                csms_calibration.min,
                csms_calibration.max, 
                strftime(
                    '%d/%m/%Y %H:%M:%S',
                    datetime(csms_calibration.created, 'unixepoch', 'localtime')) 
                    as calibration_date
            FROM csms_data
            INNER JOIN csms_calibration ON 
                (csms_calibration.id = csms_data.csms_calibration_id)
            INNER JOIN csms ON (csms.id = csms_data.csms_id)
            WHERE csms_data.csms_id = '{csms["id"]}'
            ORDER BY csms_data.created DESC
            LIMIT 1
            """
        csms_data = cur.execute(data_sql).fetchone()
        if csms_data is not None:
            tmp.append({**csms_data})
    data = {}
    if not tmp:
        return data
    for t in tmp:
        address, channel = t["name"].split(":")
        if address not in data.keys():
            data[address] = {}
        data[address][channel] = t
    return {**data}


@app.get("/api/server/<int:server_id>/csms/tmp")
def get_server_csms_tmp(server_id):
    # Get temporary data when calibration is ON
    con = get_db()
    cur = con.cursor()
    csms_query = cur.execute(
        f"""
        SELECT id
        FROM csms
        WHERE server_id = '{server_id}'
        """
    ).fetchall()
    if not csms_query:
        return {}
    tmp = []
    for csms in csms_query:
        data_sql = f"""
            SELECT
                csms.name,
                csms_data_tmp.value as raw_value,
                strftime('%d/%m/%Y %H:%M:%S', csms_calibration.created) 
                    as calibration_date
            FROM csms_data_tmp
            INNER JOIN csms ON (csms.id = csms_data_tmp.csms_id)
            INNER JOIN csms_calibration ON (csms_calibration.id = 
                (SELECT id 
                FROM csms_calibration WHERE csms_id = '{csms["id"]}'
                ORDER BY created DESC LIMIT 1))
            WHERE csms_data_tmp.csms_id = '{csms["id"]}'
            ORDER BY csms_data_tmp.created DESC
            LIMIT 1
            """
        data_query = cur.execute(data_sql).fetchone()
        if data_query is not None:
            tmp.append({**data_query})
    data = {}
    if not tmp:
        return data
    for t in tmp:
        address, channel = t["name"].split(":")
        if address not in data.keys():
            data[address] = {}
        data[address][channel] = t
    return {**data}


@app.get("/api/server/<int:server_id>/csms/<string:csms_name>/chart/<int:days>")
def csms_graph(server_id, csms_name, days):
    con = get_db()
    cur = con.cursor()
    sql = f"""
        SELECT
            csms.name,
            printf('%,d', AVG(100 - (
                CAST(csms_data.value - csms_calibration.min AS FLOAT) 
                / (csms_calibration.max - csms_calibration.min)) * 100) ) as value,
            csms_data.created as created
        FROM csms_data
        INNER JOIN csms_calibration 
            ON (csms_calibration.id = csms_data.csms_calibration_id)
        INNER JOIN csms ON (csms.id = csms_data.csms_id)
        WHERE csms_data.csms_id = 
            (SELECT id FROM csms WHERE name = '{csms_name}' LIMIT 1)
        AND datetime(csms_data.created, 'unixepoch') > datetime('now' , '-{days} days')
        GROUP BY csms_data.created / 1800
        ORDER BY created ASC;
        """
    query = cur.execute(sql).fetchall()
    if not query:
        return ["There is no data for the selected period"], 400
    name = query[0]["name"]
    t = []
    v = []
    for q in query:
        t.append(int(q["created"]))
        v.append(int(q["value"]))
    data = {"data": [t, v], "name": name}
    return data


@app.get("/api/server/<int:server_id>/aht/chart/<int:days>")
def aht_graph(server_id, days):
    con = get_db()
    cur = con.cursor()
    sql_string = f"""
        SELECT 
            printf("%.1f", temperature) as temperature,
            printf("%.1f", humidity) as humidity,
            created as created
        FROM aht
        WHERE server_id = '{server_id}'
        AND datetime(created, 'unixepoch') > datetime('now' , '-{days} days')
        GROUP BY created / 1800
        ORDER BY created ASC
        """
    query = cur.execute(sql_string).fetchall()
    if not query:
        return ["There is no data for the selected period"], 400
    timestamp = []
    tmp = []
    hum = []
    for q in query:
        timestamp.append(q["created"])
        tmp.append(q["temperature"])
        hum.append(q["humidity"])
    data = {"data": [timestamp, tmp, hum]}
    return data


@app.post("/api/server/<int:server_id>/calibrate")
def add_calibration_value(server_id):
    con = get_db()
    cur = con.cursor()
    sql = f"""
        INSERT INTO csms_calibration
            (csms_id, min, max)
        VALUES (
            (SELECT id FROM csms WHERE name = '{request.json["name"]}'),
            '{request.json["min"]}',
            '{request.json["max"]}'
        )
        """
    cur.execute(sql)
    try:
        con.commit()
    except Exception:
        return [f'New calibration failed for {request.json["name"]}'], 400
    return [], 200


@app.post("/api/server/<int:server_id>/onboot")
def on_boot(server_id):
    """
    When MCU boots update csms and log it.
    """
    con = get_db()
    cur = con.cursor()
    for csms in request.json:
        sql1 = f"""
            INSERT INTO csms (server_id, name) 
            SELECT '{server_id}', '{csms}' 
            WHERE NOT EXISTS(
                SELECT 1 FROM csms WHERE server_id = '{server_id}' AND name = '{csms}'
                );
            """
        sql2 = f"""
            INSERT INTO csms_calibration (csms_id, min, max)
            SELECT 
                (SELECT id from csms WHERE server_id = '{server_id}' 
                    AND name = '{csms}'),
                '0',
                '65535'
            WHERE NOT EXISTS(
                SELECT 1 FROM csms_calibration WHERE csms_id =
                    (SELECT id from csms WHERE server_id = '{server_id}' 
                        AND name = '{csms}')
            )
            """
        cur.execute(sql1)
        cur.execute(sql2)
    con.commit()
    if not check_sas(server_id):
        log(server_id, "SAS Updated")
        sas_api_update(server_id)
    log(server_id, "Server rebooted")
    return [], 200


@app.post("/api/server/<int:server_id>/log")
def log_from_server(server_id):
    msg = request.json["message"]
    log(server_id, msg)
    return [], 200


@app.get("/api/server/<int:server_id>/update-calibration/<int:value>")
def update_calibration(server_id, value):
    """
    Update calibration by server id
    :value 0 or 1
    return {**settings , **aht}
    """
    con = get_db()
    cur = con.cursor()
    sql = f"""
        UPDATE server
        SET calibrate = '{value}'
        WHERE id = '{server_id}'
        AND EXISTS(
            SELECT 1 FROM csms WHERE server_id = '{server_id}'
        )
        """
    cur.execute(sql)
    try:
        con.commit()
    except Exception:
        return ["Calibration update failed"], 400
    if not bool(value):
        delete_csms_data_tmp(server_id)
    return [], 200


def sas_api_update(server_id):
    # TODO : Add fail back when request fails
    con = get_db()
    cur = con.cursor()
    lng, lat = cur.execute(
        f"SELECT lng, lat FROM server WHERE id = '{server_id}'"
    ).fetchone()
    response = requests.get(
        f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&formatted=0"
    )
    data = response.json()
    sunrise = datetime.fromisoformat(data["results"]["sunrise"])
    sunrise = sunrise.astimezone().replace(tzinfo=None)
    sunset = datetime.fromisoformat(data["results"]["sunset"])
    sunset = sunset.astimezone().replace(tzinfo=None)
    sql = f"""
        INSERT INTO sas (sunrise, sunset, server_id) 
        VALUES ('{sunrise}', '{sunset}', '{server_id}');
        """
    cur.execute(sql)
    try:
        con.commit()
    except Exception:
        pass


def check_sas(server_id):
    cur = get_db().cursor()
    sql = f"""
        SELECT 1
        FROM sas
        WHERE server_id = '{server_id}'
        AND DATE(created) = DATE('now', 'localtime');
        """
    sas = cur.execute(sql).fetchone()
    return sas


def get_sas(server_id):
    cur = get_db().cursor()
    sql = f"""
        SELECT 
            strftime('%H:%M:%S', sunrise) as sunrise, 
            strftime('%H:%M:%S', sunset) as sunset
        FROM sas
        WHERE server_id = '{server_id}'
        AND DATE(created) = DATE('now', 'localtime');
        """
    sas = cur.execute(sql).fetchone()
    return sas


def log(server_id, msg):
    con = get_db()
    cur = con.cursor()
    sql = f"""
        INSERT INTO log
            (server_id, msg)
        VALUES
            (
                '{server_id}',
                '{msg}'
            )
        """
    cur.execute(sql)
    try:
        con.commit()
    except Exception:
        pass


def get_interval(server_id):
    cur = get_db().cursor()
    data = {"interval": 10}
    sql1 = f"""
        SELECT sunset, sunrise FROM sas
        WHERE DATE(created) = DATE('now', 'localtime')
        AND server_id = '{server_id}';
        """
    sas = cur.execute(sql1).fetchone()
    if sas is None:
        sas_api_update(server_id)
        return data
    sql2 = f"""
        SELECT day_interval as day, night_interval as night
        FROM server
        WHERE id = '{server_id}';
        """
    interval = cur.execute(sql2).fetchone()
    if interval is None:
        return data
    sr = datetime.fromisoformat(sas["sunrise"])
    ss = datetime.fromisoformat(sas["sunset"])
    if sr < datetime.now() < ss:
        data["interval"] = interval["day"]
        return data
    data["interval"] = interval["night"]
    return data


def delete_csms_data_tmp(server_id):
    con = get_db()
    cur = con.cursor()
    sql = f"SELECT id FROM csms WHERE server_id = '{server_id}'"
    csms = cur.execute(sql).fetchall()
    data = "".join(f"{c[0]}," for c in csms)
    delete_sql = f"""
        DELETE FROM csms_data_tmp
        WHERE csms_id IN ({data[:-1]})
        """
    cur.execute(delete_sql)
    try:
        con.commit()
    except Exception:
        pass
    return [], 200


def get_server_log(server_id):
    cur = get_db().cursor()
    sql = f"""
        SELECT
            msg,
            strftime(
                '%d/%m/%Y %H:%M',
                datetime(created, 'unixepoch', 'localtime')) as created
        FROM log
        WHERE server_id = '{server_id}'
        ORDER BY id DESC
        LIMIT 10;
        """
    query = cur.execute(sql).fetchall()
    if not query:
        return {}
    return query


@app.route("/api/<path:path>")
def api_404(path):
    return ["Not Found"], 404
