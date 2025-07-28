#!/usr/bin/env python3
import requests
import re
import json
from bs4 import BeautifulSoup
import sys

def extract_tournament_info(soup):
    """Extract tournament information from h3 tag with class tournreport"""
    tournament_info = {}
    
    # Find the tournament heading
    tourney_heading = soup.find('h3', class_='tournreport')
    if tourney_heading:
        tourney_text = tourney_heading.get_text().strip()
        
        # Split into lines and clean them
        lines = [line.strip() for line in tourney_text.split('\n') if line.strip()]
        
        if lines:
            # Tournament name is the first line without the date
            first_line = lines[0]
            date_pattern = r'(\w{3}\s+\d{1,2},\s+\d{4})'
            date_match = re.search(date_pattern, first_line)
            
            if date_match:
                # If date is in first line, extract it and clean the name
                tournament_info["date"] = date_match.group(0)
                tournament_name = first_line.split(date_match.group(0))[0].strip()
                tournament_info["tournament"] = tournament_name
                
                # Address may be after the date in the first line
                if len(first_line.split(date_match.group(0))) > 1:
                    address_part = first_line.split(date_match.group(0))[1].strip()
                    if address_part:
                        tournament_info["address"] = address_part
            else:
                # No date in first line, just use it as tournament name
                tournament_info["tournament"] = first_line
                
                # Look for date in other lines
                for line in lines[1:]:
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        tournament_info["date"] = date_match.group(0)
                        
                        # Address might be in the same line as the date
                        parts = line.split(date_match.group(0))
                        if len(parts) > 1 and parts[1].strip():
                            tournament_info["address"] = parts[1].strip()
                        break
            
            # If we still don't have an address, look for it in remaining lines
            if "address" not in tournament_info and len(lines) > 1:
                for line in lines[1:]:
                    # Skip lines with date or TD info
                    if ("date" in tournament_info and tournament_info["date"] in line) or "TD:" in line:
                        continue
                    tournament_info["address"] = line.strip()
                    break
            
            # Extract TD name if available
            td_pattern = r'TD:?\s+([A-Za-z]+)'
            for line in lines:
                td_match = re.search(td_pattern, line)
                if td_match:
                    tournament_info["TD"] = td_match.group(1)
                    break
    
    return tournament_info

def parse_section_results(pre_text):
    """Parse the results from a pre tag containing player results"""
    lines = pre_text.strip().split('\n')
    results = []
    
    if not lines:
        return results
    
    # First line is the header, which indicates number of rounds
    header = lines[0].strip()
    
    # Determine how many rounds based on header
    round_columns = []
    header_parts = header.split()
    for i, part in enumerate(header_parts):
        if part.startswith('rd') and part[2:].isdigit():
            round_columns.append((i, part))
    
    # Process each player line
    for line in lines[1:]:
        if not line.strip():
            continue
            
        parts = line.split()
        if len(parts) < 10:  # Need at least position through total columns
            continue
            
        player = {}
        
        # Extract position
        try:
            player["pos"] = int(parts[0])
        except ValueError:
            continue  # Skip if position is not a number
            
        # Extract name (tricky because names can have spaces)
        name_end = None
        for i, part in enumerate(parts):
            if re.match(r'^[A-Z0-9]{8}$', part):  # ID format like SHMJ995H
                player["id"] = part
                name_end = i
                break
                
        if name_end is None or name_end < 2:
            continue  # Couldn't find ID or name is too short
            
        # Fix last name (removing comma)
        player["last name"] = parts[1].rstrip(',')
        player["first name"] = " ".join(parts[2:name_end])
        
        # Extract ratings and games
        idx = name_end + 1
        if idx < len(parts):
            try:
                player["start"] = int(parts[idx])
                idx += 1
            except ValueError:
                pass
                
        # Extract end rating and games
        if idx < len(parts):
            end_games = parts[idx]
            
            # Check if the format is "rating/games" (no space)
            if '/' in end_games and ' ' not in end_games:
                end, games = end_games.split('/')
                try:
                    player["end"] = int(end.strip())
                    player["gms"] = int(games.strip())
                except ValueError:
                    pass
                idx += 1
            
            # Check if the format is "rating/ games" (with space)
            elif '/' in end_games and end_games.endswith('/'):
                # The rating is in this part, games in next part
                try:
                    end = end_games.rstrip('/')
                    player["end"] = int(end.strip())
                    
                    # Games should be in next part
                    if idx + 1 < len(parts):
                        try:
                            games_part = parts[idx + 1]
                            player["gms"] = int(games_part.strip())
                            idx += 2  # Skip both parts
                        except ValueError:
                            idx += 1  # Just skip the rating part
                    else:
                        idx += 1
                except ValueError:
                    idx += 1
                    
            # Just a rating, no games specified
            else:
                try:
                    player["end"] = int(end_games.strip())
                    idx += 1
                except ValueError:
                    idx += 1
                
        # Extract games value for entries like player #3 with id CIAFK82Z
        # Check if there might be a games value that's a number without a slash
        if "end" in player and "gms" not in player:
            if idx < len(parts) and parts[idx].isdigit():
                try:
                    player["gms"] = int(parts[idx])
                    idx += 1
                except ValueError:
                    pass
        
        # Extract round results
        player["rds"] = []
        
        # Calculate position of first round result
        first_round_idx = idx
        
        # Process each round
        for i, (_, round_name) in enumerate(round_columns):
            result_idx = first_round_idx + i
            if result_idx < len(parts):
                result = parts[result_idx]
                player["rds"].append({
                    "round": round_name,
                    "res": result
                })
                
        # Extract total score (usually the last column)
        total_idx = first_round_idx + len(round_columns)
        if total_idx < len(parts) and parts[total_idx]:
            try:
                player["tot"] = float(parts[total_idx])
            except ValueError:
                pass
                
        results.append(player)
        
    return results

def extract_chess_results(url):
    """Main function to extract chess tournament results from a URL"""
    # Fetch the webpage
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch webpage: {response.status_code}")
        return None
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract tournament info
    result = extract_tournament_info(soup)
    result["url"] = url
    
    # Extract sections
    sections = []
    section_headers = soup.find_all('h4')
    
    for header in section_headers:
        section_data = {"section": header.get_text().strip()}
        
        # Find the pre tag that follows this section header
        pre_tag = header.find_next('pre')
        if pre_tag:
            section_data["results"] = parse_section_results(pre_tag.get_text())
            sections.append(section_data)
    
    result["sections"] = sections
    return result

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://ratingsnw.com/report24-25/HotSummerChess-IV.html"
        
    results = extract_chess_results(url)
    if results:
        print(json.dumps(results, indent=2))
        
        # Save to file
        output_file = "chess_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
