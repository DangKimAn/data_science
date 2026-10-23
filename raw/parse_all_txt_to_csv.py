import os
import re
import glob
import pandas as pd

def parse_all_matches(base_dir):
    """
    Parses all match files in 2014-2026/more/*_full.txt (1930 to 2026)
    and enriches with cup.txt / cup_finals.txt where available.
    """
    more_dir = os.path.join(base_dir, 'more')
    full_files = sorted(glob.glob(os.path.join(more_dir, '*_full.txt')))
    
    matches = []
    
    year_re = re.compile(r'=\s*World\s*Cup\s*(\d{4})', re.IGNORECASE)
    stage_re = re.compile(r'^▪+\s*(.+)$')
    fixture_re = re.compile(
        r'^\s*([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+v\s+([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+(\d+)\s*-\s*(\d+)(?:\s+([a-zA-Z0-9\.\,\s\(\)\-]+))?$'
    )
    refs_re = re.compile(r'^\s*Refs:\s*(.+)$')
    
    for fpath in full_files:
        fname = os.path.basename(fpath)
        m_yr = re.search(r'(\d{4})_full\.txt', fname)
        if not m_yr:
            continue
        default_year = int(m_yr.group(1))
        
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        year = default_year
        current_stage = 'Group Stage'
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip('\r\n')
            
            # Check year header
            m_year = year_re.search(line)
            if m_year:
                year = int(m_year.group(1))
                i += 1
                continue
                
            # Stage detection
            m_stage = stage_re.match(line.strip())
            if m_stage:
                raw_stage = m_stage.group(1).strip()
                if ',' in raw_stage:
                    parts = [p.strip() for p in raw_stage.split(',')]
                    current_stage = parts[-1] if 'Group' in parts[-1] else raw_stage
                else:
                    current_stage = raw_stage
                i += 1
                continue
                
            # Match header line containing '@' and day of week
            if '@' in line and any(d in line for d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
                parts = line.strip().split('@')
                left = parts[0].strip()
                right = parts[1].strip()
                
                left_tokens = left.split()
                date_str = " ".join(left_tokens[:3]) if len(left_tokens) >= 3 else left
                time_str = " ".join(left_tokens[3:]) if len(left_tokens) >= 4 else ""
                
                attendance = None
                if 'Att:' in right:
                    venue_part, att_part = right.split('Att:')
                    att_digits = re.sub(r'\D', '', att_part)
                    attendance = int(att_digits) if att_digits else None
                else:
                    venue_part = right
                    
                v_parts = [v.strip() for v in venue_part.split(',') if v.strip()]
                stadium = v_parts[0] if len(v_parts) > 0 else ""
                city = v_parts[1] if len(v_parts) > 1 else ""
                
                # Advance to fixture line
                i += 1
                while i < len(lines) and not lines[i].strip():
                    i += 1
                    
                if i < len(lines):
                    m_fix = fixture_re.match(lines[i].rstrip('\r\n'))
                    if m_fix:
                        home_team = m_fix.group(1).strip()
                        away_team = m_fix.group(2).strip()
                        home_goals = int(m_fix.group(3))
                        away_goals = int(m_fix.group(4))
                        extra_info = (m_fix.group(5) or "").strip()
                        
                        ht_home = None
                        ht_away = None
                        win_cond = ""
                        
                        if extra_info:
                            m_ht = re.search(r'\((\d+)\s*-\s*(\d+)\)', extra_info)
                            if m_ht:
                                ht_home = int(m_ht.group(1))
                                ht_away = int(m_ht.group(2))
                            if 'pen' in extra_info or 'a.e.t' in extra_info:
                                win_cond = extra_info
                                
                        # Look ahead for referees
                        referee, asst1, asst2 = "", "", ""
                        for j in range(i + 1, min(i + 25, len(lines))):
                            m_ref = refs_re.match(lines[j].strip())
                            if m_ref:
                                r_tokens = [r.strip() for r in m_ref.group(1).split(',')]
                                if len(r_tokens) > 0: referee = r_tokens[0]
                                if len(r_tokens) > 1: asst1 = r_tokens[1]
                                if len(r_tokens) > 2: asst2 = r_tokens[2]
                                break
                            if '@' in lines[j] and any(d in lines[j] for d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
                                break
                                
                        datetime_val = f"{date_str} {year} - {time_str}".strip()
                        matches.append({
                            'Year': year,
                            'Datetime': datetime_val,
                            'Stage': current_stage,
                            'Stadium': stadium,
                            'City': city,
                            'Home Team Name': home_team,
                            'Home Team Goals': home_goals,
                            'Away Team Goals': away_goals,
                            'Away Team Name': away_team,
                            'Win conditions': win_cond,
                            'Attendance': attendance,
                            'Half-time Home Goals': ht_home,
                            'Half-time Away Goals': ht_away,
                            'Referee': referee,
                            'Assistant 1': asst1,
                            'Assistant 2': asst2
                        })
            i += 1
            
    df_matches = pd.DataFrame(matches)
    return df_matches

def parse_all_squads(base_dir):
    """
    Parses all squad files in 2014-2026/more/*_squads.txt (1930 to 2026)
    Extracts: Year, Country, Shirt Number, Player Name, Position, Birthdate, Role
    """
    more_dir = os.path.join(base_dir, 'more')
    squad_files = sorted(glob.glob(os.path.join(more_dir, '*_squads.txt')))
    
    squads = []
    
    year_re = re.compile(r'=\s*World\s*Cup\s*(\d{4})', re.IGNORECASE)
    country_re = re.compile(r'^==\s*(.+?)(?:\s+#.*)?$')
    
    for fpath in squad_files:
        fname = os.path.basename(fpath)
        m_yr = re.search(r'(\d{4})_squads\.txt', fname)
        default_year = int(m_yr.group(1)) if m_yr else None
        
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        year = default_year
        current_country = ""
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            # Year header
            m_year = year_re.search(line_str)
            if m_year:
                year = int(m_year.group(1))
                continue
                
            # Country header: == Japan # 23 Players
            m_country = country_re.match(line_str)
            if m_country:
                current_country = m_country.group(1).strip()
                continue
                
            # Comment line
            if line_str.startswith('#'):
                continue
                
            # Player line:
            # e.g.: "1, Eiji KAWASHIMA, GK, b. 1983/03/20"
            # or without number: "Jimmy DOUGLAS, GK, b. 1898/01/12"
            # or coach: "-, Akira NISHINO (JPN), MG, b. 1955/04/07"
            parts = [p.strip() for p in line_str.split(',')]
            if len(parts) >= 2:
                shirt_number = ""
                player_name = ""
                position = ""
                birthdate = ""
                
                # Check if first part is a number or "-"
                if parts[0].isdigit() or parts[0] == '-':
                    shirt_number = parts[0] if parts[0].isdigit() else ""
                    player_name = parts[1]
                    if len(parts) >= 3:
                        position = parts[2]
                    if len(parts) >= 4:
                        birthdate = ",".join(parts[3:]).replace('b.', '').strip()
                else:
                    # No shirt number specified
                    player_name = parts[0]
                    if len(parts) >= 2:
                        position = parts[1]
                    if len(parts) >= 3:
                        birthdate = ",".join(parts[2:]).replace('b.', '').strip()
                        
                # Determine role: Player or Manager
                role = "Manager" if position == "MG" else "Player"
                
                squads.append({
                    'Year': year,
                    'Country': current_country,
                    'Shirt Number': shirt_number,
                    'Player Name': player_name,
                    'Position': position,
                    'Birthdate': birthdate,
                    'Role': role
                })
                
    df_squads = pd.DataFrame(squads)
    return df_squads

if __name__ == '__main__':
    base_dir = '/home/na/code/fifaWorldCup/2014-2026'
    
    print("=== 1. PARSING ALL MATCHES (1930 - 2026) ===")
    df_matches = parse_all_matches(base_dir)
    matches_csv = '/home/na/code/fifaWorldCup/WorldCupMatches_1930_2026.csv'
    df_matches.to_csv(matches_csv, index=False, encoding='utf-8')
    print(f"Total matches extracted: {len(df_matches)}")
    print(f"Saved to: {matches_csv}")
    print("Matches by Year:")
    print(df_matches['Year'].value_counts().sort_index())
    
    print("\n=== 2. PARSING ALL SQUADS & PLAYERS (1930 - 2026) ===")
    df_squads = parse_all_squads(base_dir)
    squads_csv = '/home/na/code/fifaWorldCup/WorldCupSquads_1930_2026.csv'
    df_squads.to_csv(squads_csv, index=False, encoding='utf-8')
    print(f"Total players/managers extracted: {len(df_squads)}")
    print(f"Saved to: {squads_csv}")
    print("Squads by Year:")
    print(df_squads['Year'].value_counts().sort_index())
