# VNWSRS: Chess Tournament Results System - Requirements Document

## Table of Contents
1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Core Requirements](#core-requirements)
   - [Data Extraction](#data-extraction)
   - [Data Storage](#data-storage)
   - [System Functionality](#system-functionality)
4. [Detailed Technical Specifications](#detailed-technical-specifications)
   - [HTML Source Structure](#html-source-structure)
   - [Data Extraction Process](#data-extraction-process)
   - [Database Schema](#database-schema)
   - [Data Processing Rules](#data-processing-rules)
5. [Future Enhancements](#future-enhancements)
6. [Appendix](#appendix)
   - [Dependencies](#dependencies)
   - [Sample Data](#sample-data)

## Introduction

The VNWSRS (Chess Tournament Results System) is a specialized application designed to extract chess tournament results from web pages and store them in a structured database. This document outlines the requirements and specifications for the system to ensure accurate extraction and storage of chess tournament data.

## System Overview

The system consists of two primary components:

1. **Data Extraction Component** - Responsible for scraping tournament data from HTML pages
2. **Data Storage Component** - Responsible for storing extracted data in a SQLite database

The system operates in a two-step process:
1. Extract data from specified tournament URLs and save to JSON files
2. Process the JSON files and load the data into a structured database

## Core Requirements

### Data Extraction

1. The system must accurately extract tournament information including name, date, location, and TD
2. The system must parse section information including section names and player results
3. The system must extract complete player information including position, name, ID, ratings, games, round results, and total score
4. The system must correctly interpret round result codes to identify wins, losses, and draws
5. The system must output extracted data in a standardized JSON format
6. The system must handle variations in HTML formatting and structure
7. The system must provide appropriate error handling for missing or malformed data

### Data Storage

1. The system must maintain a normalized database schema to store tournament data
2. The system must enforce relationships between tournament, player, section table, and game data
3. The system must handle player IDs according to specified rules (removing first 4 characters)
4. The system must avoid duplicate data entry for tournaments and players
5. The system must correctly link games with both player and opponent information
6. The system must maintain data integrity through appropriate constraints and transactions

### System Functionality

1. The system must provide command-line interfaces for both extraction and storage components
2. The system must allow specification of input/output files and locations
3. The system must provide clear status and error messages during operation
4. The system must handle exceptions gracefully without crashing

## Detailed Technical Specifications

### HTML Source Structure

The system extracts data from HTML pages with the following structure:

- **Tournament Information**: Contained within `<h3>` tags with class `tournreport`
  - Format includes tournament name, date (Mon DD, YYYY), location, and optional TD
- **Section Information**: Section names contained within `<h4>` tags
- **Results Data**: Section results follow section headers within `<pre>` tags
  - First line contains column headers indicating format and number of rounds
  - Subsequent lines contain player data with position, name, ID, ratings, and round results
  - Round results use codes like W4 (win against player 4), L7 (loss against player 7), etc.

### Data Extraction Process

1. **Tournament Information Extraction**
   - Parse the tournament name from the first line of tournament heading
   - Extract date using pattern matching (format: "Mon DD, YYYY")
   - Identify location information following the date
   - Extract TD name if available using pattern matching

2. **Section Information Extraction**
   - Identify section names from `<h4>` tags
   - Associate each section with its corresponding results block

3. **Player Results Extraction**
   - Parse header line to identify column positions and number of rounds
   - Extract player information from each line including:
     - Position (numerical ranking)
     - Last name
     - First name
     - ID (format like "SHMJ995H")
     - Starting rating (numerical)
     - Ending rating (numerical)
     - Games played (numerical)
     - Round results (format varies by tournament)
     - Total score (numerical with decimals possible)

4. **Round Results Processing**
   - Identify result code format (e.g., "W4", "L7", "D2")
   - Extract result type (W=win, L=loss, D=draw) and opponent position

### Database Schema

#### Tournament Table
```sql
CREATE TABLE tournament (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_name TEXT NOT NULL,
    date TEXT,
    address TEXT,
    url TEXT
)
```

#### Player Table
```sql
CREATE TABLE player (
    id TEXT PRIMARY KEY,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL
)
```

#### Section Table
```sql
CREATE TABLE section (
    tournament_id INTEGER,
    section_id INTEGER,
    section_name TEXT NOT NULL,
    PRIMARY KEY (tournament_id, section_id),
    FOREIGN KEY (tournament_id) REFERENCES tournament (id)
)
```

#### Player Tournament Table
```sql
CREATE TABLE player_tournament (
    player_id TEXT,
    tournament_id INTEGER,
    section_id INTEGER,
    start_rating INTEGER,
    end_rating INTEGER,
    games INTEGER,
    score REAL,
    PRIMARY KEY (player_id, tournament_id, section_id),
    FOREIGN KEY (player_id) REFERENCES player (id),
    FOREIGN KEY (tournament_id, section_id) REFERENCES section (tournament_id, section_id)
)
```

#### Games Table
```sql
CREATE TABLE games (
    tournament_id INTEGER,
    player_id TEXT,
    section_id INTEGER,
    round TEXT,
    opponent_id TEXT,
    result TEXT,
    PRIMARY KEY (tournament_id, player_id, section_id, round),
    FOREIGN KEY (tournament_id, section_id) REFERENCES section (tournament_id, section_id),
    FOREIGN KEY (player_id) REFERENCES player (id),
    FOREIGN KEY (opponent_id) REFERENCES player (id)
)
```

### Data Processing Rules

1. **Tournament Processing**
   - Check if tournament exists by name and date before insertion
   - Generate unique ID for new tournaments

2. **Player Processing**
   - Player IDs are processed by removing the first 4 characters
   - Check if player exists by processed ID before insertion

3. **Section Processing**
   - For each section in the tournament, insert a record in the section table
   - Generate section_id starting from 1 for each tournament
   - Store section name for reference

4. **Player Tournament Processing**
   - Create records linking players to tournaments with section_id
   - Include rating and performance data

5. **Games Processing**
   - Only process results starting with W, L, or D
   - Extract opponent position from result code
   - Lookup opponent ID using their position in the same section
   - Store player-opponent game record with section_id and result code

## Future Enhancements

The system could be extended with the following enhancements:

1. **Data Extraction Improvements**
   - Support for additional date formats and multi-day tournaments
   - Enhanced name parsing for titles, suffixes, and special characters
   - Support for additional result codes and annotations

2. **Database Enhancements**
   - Additional tables for more detailed tournament and section information
   - Optimized indices for common queries
   - Version control for database schema

3. **Additional Features**
   - Data analysis and statistics generation
   - Export capabilities to various formats
   - Basic web interface for data browsing
   - Player rating progression tracking

4. **System Improvements**
   - Comprehensive logging
   - External configuration
   - Test suite for validation
   - Detailed documentation

## Appendix

### Dependencies

- Python 3.x
- requests library
- BeautifulSoup4 library
- sqlite3 module (standard library)

### Sample Data

#### Sample JSON Output Format
```json
{
  "url": "https://example.com/tournament.html",
  "tournament": "Sample Chess Tournament",
  "date": "Jul 15, 2025",
  "address": "Seattle, WA",
  "TD": "Smith",
  "sections": [
    {
      "section": "Open Section",
      "results": [
        {
          "id": "SHMJ995H",
          "pos": 1,
          "last name": "Player",
          "first name": "Top",
          "start": 2000,
          "end": 2025,
          "gms": 150,
          "rds": [
            {
              "round": "rd1",
              "res": "W4"
            },
            {
              "round": "rd2",
              "res": "D2"
            },
            {
              "round": "rd3",
              "res": "W3"
            }
          ],
          "tot": 2.5
        }
      ]
    }
  ]
}