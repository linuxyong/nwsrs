# Chess Tournament Results System - Technical Requirements

## 1. System Overview

The Chess Tournament Results System is designed to extract chess tournament results from web pages and store them in a structured SQLite database. The system consists of two main components:

1. **Data Extraction Component** - Extracts chess tournament data from HTML pages
2. **Data Storage Component** - Stores the extracted data in a SQLite database

## 2. Data Extraction Requirements

### 2.1 HTML Source Structure

The system must extract data from HTML pages with the following structure:

- Tournament information is contained within `<h3>` tags with class `tournreport`
- Tournament information includes name, date, location address, and TD (Tournament Director)
- Each tournament can have multiple sections
- Section names are contained within `<h4>` tags
- Section results follow the section name and are wrapped with `<pre>` tags
- The first line of section results is the header with format:
  ```
  pos last name first       id numb   start end/#gms  rd1 rd2 rd3 ... tot
  ```
- The number of rounds columns (`rd1`, `rd2`, etc.) varies depending on the number of rounds in the section
- Each subsequent line represents a player's results with the corresponding data

### 2.2 Tournament Information Extraction

The system must extract the following tournament information:
- Tournament name
- Date (format: "Mon DD, YYYY", e.g. "Jul 15, 2025")
- Location address
- Tournament Director (TD)
- Source URL

### 2.3 Section Data Extraction

For each section, the system must extract:
- Section name
- Player results for each player in the section

### 2.4 Player Data Extraction

For each player, the system must extract:
- Position in the standings (`pos`)
- Last name
- First name
- Player ID (e.g. "SHMJ995H")
- Starting rating (`start`)
- Ending rating (`end`)
- Number of games played (`gms`)
- Results for each round (`rd1`, `rd2`, etc.)
- Total score (`tot`)

### 2.5 Round Results Format

Round results follow these formats:
- "W" followed by opponent position number indicates a win (e.g., "W4" means won against player in position 4)
- "L" followed by opponent position number indicates a loss
- "D" followed by opponent position number indicates a draw
- Other codes may exist but only W, L, D results should be processed for game records

### 2.6 Output Format

The extracted data must be output in JSON format with the following structure:
```json
{
  "url": "https://example.com/tournament.html",
  "tournament": "Tournament Name",
  "date": "Mon DD, YYYY",
  "address": "Location Address",
  "TD": "Director Name",
  "sections": [
    {
      "section": "Section Name",
      "results": [
        {
          "id": "PLAYERID",
          "pos": 1,
          "last name": "Last",
          "first name": "First",
          "start": 1500,
          "end": 1550,
          "gms": 100,
          "rds": [
            {
              "round": "rd1",
              "res": "W4"
            },
            {
              "round": "rd2",
              "res": "D2"
            }
          ],
          "tot": 1.5
        }
      ]
    }
  ]
}
```

## 3. Data Storage Requirements

### 3.1 Database Schema

The system must store the extracted data in a SQLite database with the following tables:

#### 3.1.1 Tournament Table
- **Schema**: `id`, `tournament_name`, `date`, `address`, `url`
- **Primary Key**: `id` (auto-incrementing)

#### 3.1.2 Player Table
- **Schema**: `id`, `last_name`, `first_name`
- **Primary Key**: `id`
- **ID Format**: Player ID with the first 4 characters removed

#### 3.1.3 Player Tournament Table
- **Schema**: `player_id`, `tournament_id`, `section`, `start_rating`, `end_rating`, `games`, `score`
- **Primary Key**: (`player_id`, `tournament_id`, `section`)
- **Foreign Keys**:
  - `player_id` references `player.id`
  - `tournament_id` references `tournament.id`

#### 3.1.4 Games Table
- **Schema**: `tournament_id`, `player_id`, `section`, `round`, `opponent_id`, `result`
- **Primary Key**: (`tournament_id`, `player_id`, `section`, `round`)
- **Foreign Keys**:
  - `tournament_id` references `tournament.id`
  - `player_id` references `player.id`
  - `opponent_id` references `player.id`

### 3.2 Data Processing Requirements

#### 3.2.1 Tournament Processing
- Insert tournament data if it doesn't already exist (based on name and date)
- Return the tournament ID for use in related records

#### 3.2.2 Player Processing
- For each player, extract the ID and remove the first 4 characters
- Insert player data if it doesn't already exist (based on ID)
- Return the processed player ID for use in related records

#### 3.2.3 Player Tournament Processing
- Insert a record for each player's participation in a tournament section
- Include start rating, end rating, games played, and total score

#### 3.2.4 Games Processing
- Process only results that start with "W", "L", or "D"
- Extract the opponent position number from the result code
- Find the opponent's ID using their position number in the same section
- Store the game result with player ID, opponent ID, and result code

## 4. System Functionality Requirements

### 4.1 Command-Line Interface

The system must provide command-line interfaces for both components:

#### 4.1.1 Data Extraction Component
- Accept a URL parameter for the tournament page to process
- Default to a predefined URL if no parameter is provided
- Output the extracted data to the console
- Save the extracted data to a JSON file (default: `chess_results.json`)

#### 4.1.2 Data Storage Component
- Accept a JSON file parameter for the input data (default: `chess_results.json`)
- Accept a database file parameter for the output (default: `chess_tournaments.db`)
- Process the JSON data and store it in the database
- Output progress and status messages to the console

### 4.2 Error Handling

The system must handle the following error conditions:
- Failed HTTP requests
- Malformed HTML content
- Missing or incomplete data fields
- Database connection failures
- JSON parsing errors

## 5. Dependencies

The system requires the following dependencies:
- Python 3.x
- requests library (for HTTP requests)
- BeautifulSoup4 library (for HTML parsing)
- sqlite3 module (part of Python standard library)

## 6. Performance Considerations

- The system should handle large tournament pages with multiple sections
- Database operations should use transactions for data integrity
- Player lookups should be optimized to handle large numbers of players