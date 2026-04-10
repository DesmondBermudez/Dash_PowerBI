-- ============================================
-- CREACIÓN DE NUEVA BASE DE DATOS WEATHER_JSON
-- ============================================
CREATE DATABASE WeatherBD
GO

USE WeatherBD
GO

-- ============================================
-- TABLA: COUNTRY
-- ============================================
CREATE TABLE Country (
    CountryID INT IDENTITY(1,1) PRIMARY KEY,
    CountryName NVARCHAR(100) NOT NULL
);

CREATE UNIQUE INDEX IX_Country_CountryName ON Country(CountryName);
GO

-- ============================================
-- TABLA: TIMEZONE
-- ============================================
CREATE TABLE Timezone (
    TimezoneID INT IDENTITY(1,1) PRIMARY KEY,
    TimezoneName NVARCHAR(100) NOT NULL,
    TimezoneAbbreviation NVARCHAR(20) NOT NULL
);

CREATE UNIQUE INDEX IX_Timezone_TimezoneName ON Timezone(TimezoneName);
GO

-- ============================================
-- TABLA: LOCATION (basada en Location.json)
-- ============================================
CREATE TABLE Location (
    LocationID INT IDENTITY(1,1) PRIMARY KEY,
    CityName NVARCHAR(100) NOT NULL,
    CountryID INT NOT NULL,
    TimezoneID INT NOT NULL,
    Latitude DECIMAL(8,5) NOT NULL,
    Longitude DECIMAL(8,5) NOT NULL,
    GenerationTimeMs FLOAT,
    Elevation FLOAT,
    CreatedAt DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_Location_Country FOREIGN KEY (CountryID) REFERENCES Country(CountryID),
    CONSTRAINT FK_Location_Timezone FOREIGN KEY (TimezoneID) REFERENCES Timezone(TimezoneID)
);

CREATE UNIQUE INDEX IX_Location_LatLon ON Location(Latitude, Longitude);
CREATE INDEX IX_Location_CityCountry ON Location(CityName, CountryID);
CREATE INDEX IX_Location_TimezoneID ON Location(TimezoneID);
GO

-- ============================================
-- TABLA: DAILY_UNITS (unidades de medidas diarias)
-- ============================================
CREATE TABLE DailyUnits (
    UnitID INT IDENTITY(1,1) PRIMARY KEY,
    FieldName NVARCHAR(100) NOT NULL,
    UnitSymbol NVARCHAR(20) NOT NULL
);

CREATE UNIQUE INDEX IX_DailyUnits_FieldName ON DailyUnits(FieldName);
GO

-- ============================================
-- TABLA: HOURLY_UNITS (unidades de medidas horarias)
-- ============================================
CREATE TABLE HourlyUnits (
    UnitID INT IDENTITY(1,1) PRIMARY KEY,
    FieldName NVARCHAR(100) NOT NULL,
    UnitSymbol NVARCHAR(20) NOT NULL
);

CREATE UNIQUE INDEX IX_HourlyUnits_FieldName ON HourlyUnits(FieldName);
GO

-- ============================================
-- TABLA: DAILY_WEATHER (datos diarios)
-- ============================================
CREATE TABLE DailyWeather (
    DailyWeatherID BIGINT IDENTITY(1,1) PRIMARY KEY,
    LocationID INT NOT NULL,
    Date DATE NOT NULL,
    uv_index_max FLOAT,
    sunshine_duration INT,
    precipitation_hours FLOAT,
    uv_index_clear_sky_max FLOAT,
    daylight_duration INT,
    sunset DATETIME2,
    sunrise DATETIME2,
    precipitation_probability_max FLOAT,
    precipitation_sum FLOAT,
    snowfall_sum FLOAT,
    showers_sum FLOAT,
    rain_sum FLOAT,
    CONSTRAINT FK_DailyWeather_Location FOREIGN KEY (LocationID) REFERENCES Location(LocationID)
);

CREATE INDEX IX_DailyWeather_LocationDate ON DailyWeather(LocationID, Date);
GO

-- ============================================
-- TABLA: HOURLY_WEATHER (datos horarios)
-- ============================================
CREATE TABLE HourlyWeather (
    HourlyWeatherID BIGINT IDENTITY(1,1),
    LocationID INT NOT NULL,
    Timestamp DATETIME2 NOT NULL,
    temperature_2m FLOAT,
    pressure_msl FLOAT,
    relative_humidity_2m FLOAT,
    soil_temperature_0cm FLOAT,
    soil_temperature_6cm FLOAT,
    soil_temperature_18cm FLOAT,
    rain FLOAT,
    precipitation FLOAT,
    apparent_temperature FLOAT,
    precipitation_probability FLOAT,
    dew_point_2m FLOAT,
    visibility FLOAT,
    showers FLOAT,
    snowfall FLOAT,
    snow_depth FLOAT,
    wind_speed_10m FLOAT,
    wind_speed_80m FLOAT,
    wind_speed_120m FLOAT,
    wind_speed_180m FLOAT,
    wind_direction_10m FLOAT,
    wind_direction_80m FLOAT,
    wind_direction_120m FLOAT,
    wind_direction_180m FLOAT,
    wind_gusts_10m FLOAT,
    temperature_80m FLOAT,
    temperature_120m FLOAT,
    soil_temperature_54cm FLOAT,
    soil_moisture_0_to_1cm FLOAT,
    soil_moisture_1_to_3cm FLOAT,
    soil_moisture_3_to_9cm FLOAT,
    soil_moisture_9_to_27cm FLOAT,
    soil_moisture_27_to_81cm FLOAT,
    temperature_180m FLOAT,
    CONSTRAINT FK_HourlyWeather_Location FOREIGN KEY (LocationID) REFERENCES Location(LocationID)
);

-- Índice clúster columnstore para análisis eficiente
CREATE CLUSTERED COLUMNSTORE INDEX IX_HourlyWeather_ColumnStore ON HourlyWeather;

-- Índice para búsquedas por ubicación y tiempo
CREATE INDEX IX_HourlyWeather_LocationTimestamp ON HourlyWeather(LocationID, Timestamp);
GO
