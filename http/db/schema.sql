DROP TABLE IF EXISTS server;
DROP TABLE IF EXISTS csms;
DROP TABLE IF EXISTS csms_data;
DROP TABLE IF EXISTS csms_data_tmp;
DROP TABLE IF EXISTS csms_calibration;
DROP TABLE IF EXISTS sas;
DROP TABLE IF EXISTS aht;
DROP TABLE IF EXISTS log;


CREATE TABLE server (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    calibrate BOOLEAN NOT NULL,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    day_interval INTEGER NOT NULL,
    night_interval INTEGER NOT NULL,
    updated TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- INSERT INTO server (name, calibrate, lat, lng, day_interval, night_interval) VALUES ('Z1', 0, 24.00, 20.00, 20, 40);
-- INSERT INTO server (name, calibrate, lat, lng, day_interval, night_interval) VALUES ('Z2', 0, 24.00, 20.00, 20, 40);

CREATE TABLE csms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT  NUll,
    name TEXT NOT NULL,
    created DATE NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE TABLE csms_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csms_id INTEGER NOT NULL,
    csms_calibration_id INTEGER NOT NULL,
    value INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE TABLE csms_data_tmp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csms_id INTEGER NOT NULL,
    value INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE TABLE csms_calibration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csms_id INTEGER NOT NULL,
    min INTEGER NOT NULL,
    max INTEGER NOT NUll,
    created TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE TABLE sas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    sunrise TIMESTAMP NOT NULL,
    sunset TIMESTAMP NOT NULL,
    created DATE NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE aht (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE TABLE log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    msg TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
);
--  lat 44.78673851424391, lng 20.45180536731959