#!/usr/bin/env python3
import json
import sqlite3
import os
import sys

def create_database_schema(conn):
    """Create the database schema for chess tournament data"""
    cursor = conn.cursor()
    
    # Create tournament table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tournament (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_name TEXT NOT NULL,
        date TEXT,
        address TEXT,
        url TEXT
    )
    ''')
    
    # Create player table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player (
        id TEXT PRIMARY KEY,
        last_name TEXT NOT NULL,
        first_name TEXT NOT NULL
    )
    ''')
    
    # Create section table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS section (
        tournament_id INTEGER,
        section_id INTEGER,
        section_name TEXT NOT NULL,
        PRIMARY KEY (tournament_id, section_id),
        FOREIGN KEY (tournament_id) REFERENCES tournament (id)
    )
    ''')
    
    # Create player_tournament table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_tournament (
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
    ''')
    
    # Create games table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
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
    ''')
    
    conn.commit()

def insert_tournament(conn, tournament_data):
    """Insert tournament data if it doesn't exist already"""
    cursor = conn.cursor()
    
    # Check if tournament with same name and date exists
    cursor.execute(
        "SELECT id FROM tournament WHERE tournament_name = ? AND date = ?",
        (tournament_data["tournament"], tournament_data["date"])
    )
    existing = cursor.fetchone()
    
    if existing:
        print(f"Tournament '{tournament_data['tournament']}' already exists with ID {existing[0]}")
        return existing[0]
    
    # Insert new tournament
    cursor.execute(
        "INSERT INTO tournament (tournament_name, date, address, url) VALUES (?, ?, ?, ?)",
        (
            tournament_data["tournament"], 
            tournament_data.get("date", ""),
            tournament_data.get("address", ""),
            tournament_data.get("url", "")
        )
    )
    tournament_id = cursor.lastrowid
    conn.commit()
    
    print(f"Inserted tournament '{tournament_data['tournament']}' with ID {tournament_id}")
    return tournament_id

def insert_player(conn, player_data):
    """Insert player data if it doesn't exist already"""
    cursor = conn.cursor()
    
    # Player ID is shortened according to requirement (remove first 4 characters)
    player_id = player_data["id"][4:] if len(player_data["id"]) > 4 else player_data["id"]
    
    # Check if player exists
    cursor.execute("SELECT id FROM player WHERE id = ?", (player_id,))
    existing = cursor.fetchone()
    
    if existing:
        return player_id
    
    # Insert new player
    cursor.execute(
        "INSERT INTO player (id, last_name, first_name) VALUES (?, ?, ?)",
        (
            player_id,
            player_data["last name"],
            player_data["first name"]
        )
    )
    conn.commit()
    
    return player_id

def insert_section(conn, tournament_id, section_name):
    """Insert section data and return section_id"""
    cursor = conn.cursor()
    
    # Check for the next available section_id for this tournament
    cursor.execute(
        "SELECT MAX(section_id) FROM section WHERE tournament_id = ?",
        (tournament_id,)
    )
    result = cursor.fetchone()
    
    # Start section_id from 1 if this is the first section
    section_id = (result[0] or 0) + 1
    
    # Insert section
    cursor.execute(
        "INSERT INTO section (tournament_id, section_id, section_name) VALUES (?, ?, ?)",
        (tournament_id, section_id, section_name)
    )
    conn.commit()
    
    print(f"Inserted section '{section_name}' with ID {section_id} for tournament {tournament_id}")
    return section_id

def insert_player_tournament(conn, player_id, tournament_id, section_id, player_data):
    """Insert player tournament participation data"""
    cursor = conn.cursor()
    
    # Insert player tournament record
    cursor.execute(
        """
        INSERT OR REPLACE INTO player_tournament 
        (player_id, tournament_id, section_id, start_rating, end_rating, games, score) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            player_id,
            tournament_id,
            section_id,
            player_data.get("start"),
            player_data.get("end"),
            player_data.get("gms"),
            player_data.get("tot")
        )
    )
    conn.commit()

def get_opponent_id_by_position(players_in_section, opponent_pos):
    """Get opponent ID by their position number in the section"""
    for player in players_in_section:
        if player["pos"] == opponent_pos:
            return player["id"][4:] if len(player["id"]) > 4 else player["id"]
    return None

def insert_games(conn, tournament_id, section_id, players_in_section):
    """Insert games data for all players in a section"""
    cursor = conn.cursor()
    
    for player in players_in_section:
        player_id = player["id"][4:] if len(player["id"]) > 4 else player["id"]
        
        if "rds" not in player:
            continue
        
        for round_data in player["rds"]:
            round_name = round_data["round"]
            result_code = round_data["res"]
            
            # Process only results that start with W, L or D
            if not result_code or len(result_code) < 2:
                continue
                
            result = result_code[0]
            if result not in ["W", "L", "D"]:
                continue
            
            # Get opponent position from result code
            try:
                opponent_pos = int(result_code[1:])
            except ValueError:
                continue
            
            # Find opponent ID
            opponent_id = get_opponent_id_by_position(players_in_section, opponent_pos)
            if not opponent_id:
                continue
            
            # Insert game record
            cursor.execute(
                """
                INSERT OR REPLACE INTO games 
                (tournament_id, player_id, section_id, round, opponent_id, result) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    tournament_id,
                    player_id,
                    section_id,
                    round_name,
                    opponent_id,
                    result
                )
            )
    
    conn.commit()

def process_chess_data(json_file, db_file):
    """Process chess data from JSON and store in SQLite database"""
    # Load JSON data
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")
        return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_file)
        create_database_schema(conn)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    
    try:
        # Insert tournament data
        tournament_id = insert_tournament(conn, data)
        
        # Process sections
        for section in data.get("sections", []):
            section_name = section.get("section", "")
            players = section.get("results", [])
            
            # Insert section and get section_id
            section_id = insert_section(conn, tournament_id, section_name)
            
            # First pass: insert all players
            for player in players:
                player_id = insert_player(conn, player)
                insert_player_tournament(conn, player_id, tournament_id, section_id, player)
            
            # Second pass: insert games with opponent IDs
            insert_games(conn, tournament_id, section_id, players)
        
        print(f"Successfully processed tournament data into {db_file}")
        return True
    
    except Exception as e:
        print(f"Error processing data: {e}")
        return False
    
    finally:
        conn.close()

def main():
    json_file = "chess_results.json"
    db_file = "chess_tournaments.db"
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        
    if len(sys.argv) > 2:
        db_file = sys.argv[2]
    
    process_chess_data(json_file, db_file)

if __name__ == "__main__":
    main()