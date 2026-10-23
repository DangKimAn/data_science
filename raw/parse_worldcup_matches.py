import os
import re
import glob
import pandas as pd

def parse_full_txt_files(more_dir, target_years=None):
    """
    Parses *_full.txt files (e.g., 2014_full.txt, 2018_full.txt, 2022_full.txt, 2026_full.txt).
    These contain:
      - Match header: Date, Time, Venue, City, Attendance
      - Match fixture: Home Team, Away Team, Score, Win conditions
      - Match officials: Referee, Assistant 1, Assistant 2
    """
    matches = []
    
    file_pattern = os.path.join(more_dir, "*_full.txt")
    files = sorted(glob.glob(file_pattern))
    
    year_re = re.compile(r'=\s*World\s*Cup\s*(\d{4})', re.IGNORECASE)
    stage_re = re.compile(r'^▪+\s*(.+)$')
    fixture_re = re.compile(
        r'^\s*([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+v\s+([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+(\d+)\s*-\s*(\d+)(?:\s+([a-zA-Z0-9\.\,\s\(\)\-]+))?$'
    )
    refs_re = re.compile(r'^\s*Refs:\s*(.+)$')
    
    for fpath in files:
        fname = os.path.basename(fpath)
        # Extract year from filename if possible
        fn_year_match = re.search(r'(\d{4})_full\.txt', fname)
        if not fn_year_match:
            continue
        f_year = int(fn_year_match.group(1))
        
        if target_years and f_year not in target_years:
            continue
            
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        year = f_year
        current_stage = 'Group Stage'
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip('\r\n')
            
            # Check for header year override
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
            
    return pd.DataFrame(matches)

def parse_tournament_dirs(base_dir, target_years=None):
    """
    Parses standard cup.txt and cup_finals.txt in each tournament folder:
    e.g. 2014--brazil/cup.txt, 2014--brazil/cup_finals.txt, 2018--russia/...
    This extracts half-time score if missing and extra win condition details.
    """
    matches = []
    
    # Tournament dirs: YYYY--country
    dirs = sorted([d for d in os.listdir(base_dir) if re.match(r'^\d{4}--', d)])
    
    stage_re = re.compile(r'^▪+\s*(.+)$')
    date_line_re = re.compile(r'^([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2})')
    
    # Match pattern inside cup.txt / cup_finals.txt:
    # 17:00 UTC-3  Brazil v Croatia   3-1 (1-1)       @ Arena de São Paulo, São Paulo
    # 18:00 UTC+3     Russia       5-0 (2-0)  Saudi Arabia     @ Luzhniki Stadium, Moscow
    # 19:00      Qatar   0-2 (0-2)   Ecuador    @ Al Bayt Stadium, Al Khor
    # 13:00 UTC-3  Brazil 1-1 a.e.t. (1-1, 1-1), 3-2 pen. Chile @ Estádio Mineirão, Belo Horizonte
    match_line_re = re.compile(
        r'^\s*([0-9]{1,2}:[0-9]{2}(?:\s*UTC[+-]\d+)?)\s+'
        r'([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+'
        r'(?:v\s+)?'
        r'(\d+)\s*-\s*(\d+)'
        r'(?:\s+([a-zA-Z0-9\.\,\s\(\)\-]+?))?'
        r'\s+([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+'
        r'@\s*([^,]+),\s*(.+?)(?:\s+#.*)?$'
    )

    for d in dirs:
        m_yr = re.match(r'^(\d{4})--', d)
        if not m_yr: continue
        yr = int(m_yr.group(1))
        if target_years and yr not in target_years: continue
        
        dir_path = os.path.join(base_dir, d)
        txt_files = [os.path.join(dir_path, f) for f in ['cup.txt', 'cup_finals.txt'] if os.path.exists(os.path.join(dir_path, f))]
        
        for fpath in txt_files:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            current_stage = 'Group Stage'
            current_date = ''
            
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith('#') or line_str.startswith('='):
                    continue
                    
                # Check stage
                m_st = stage_re.match(line_str)
                if m_st:
                    current_stage = m_st.group(1).strip()
                    continue
                    
                # Check date
                m_dt = date_line_re.match(line_str)
                if m_dt and '@' not in line_str:
                    current_date = m_dt.group(1).strip()
                    continue
                    
                # Check match
                m_m = match_line_re.match(line)
                if m_m:
                    time_part = m_m.group(1).strip()
                    home_team = m_m.group(2).strip()
                    home_goals = int(m_m.group(3))
                    away_goals = int(m_m.group(4))
                    extra_notes = (m_m.group(5) or "").strip()
                    away_team = m_m.group(6).strip()
                    stadium = m_m.group(7).strip()
                    city = m_m.group(8).strip()
                    
                    ht_home, ht_away = None, None
                    win_cond = ""
                    
                    if extra_notes:
                        m_ht = re.search(r'\((\d+)\s*-\s*(\d+)', extra_notes)
                        if m_ht:
                            ht_home = int(m_ht.group(1))
                            ht_away = int(m_ht.group(2))
                        if 'pen' in extra_notes or 'a.e.t' in extra_notes:
                            win_cond = extra_notes
                            
                    datetime_val = f"{current_date} {yr} - {time_part}".strip()
                    matches.append({
                        'Year': yr,
                        'Datetime': datetime_val,
                        'Stage': current_stage,
                        'Stadium': stadium,
                        'City': city,
                        'Home Team Name': home_team,
                        'Home Team Goals': home_goals,
                        'Away Team Goals': away_goals,
                        'Away Team Name': away_team,
                        'Win conditions': win_cond,
                        'Attendance': None,
                        'Half-time Home Goals': ht_home,
                        'Half-time Away Goals': ht_away,
                        'Referee': '',
                        'Assistant 1': '',
                        'Assistant 2': ''
                    })
                    
    return pd.DataFrame(matches)

def merge_and_enrich_matches(base_folder, target_years=[2014, 2018, 2022, 2026]):
    """
    Combines matches parsed from more/*_full.txt (with attendance & referees)
    and tournament dirs (with half-time goals & extra time details).
    """
    more_dir = os.path.join(base_folder, 'more')
    df_full = parse_full_txt_files(more_dir, target_years=target_years)
    print(f"Loaded {len(df_full)} matches from more/*_full.txt")
    
    df_cup = parse_tournament_dirs(base_folder, target_years=target_years)
    print(f"Loaded {len(df_cup)} matches from tournament cup.txt / cup_finals.txt")
    
    if df_full.empty:
        return df_cup
    if df_cup.empty:
        return df_full
        
    # Standardize team names for matching
    def norm_team(s):
        return re.sub(r'[^a-zA-Z0-9]', '', str(s).lower())
        
    df_full['key'] = (
        df_full['Year'].astype(str) + '_' + 
        df_full['Home Team Name'].apply(norm_team) + '_' + 
        df_full['Away Team Name'].apply(norm_team)
    )
    df_cup['key'] = (
        df_cup['Year'].astype(str) + '_' + 
        df_cup['Home Team Name'].apply(norm_team) + '_' + 
        df_cup['Away Team Name'].apply(norm_team)
    )
    
    # Fill missing half-time or win conditions from df_cup into df_full
    cup_ht_map = df_cup.set_index('key')
    for idx, row in df_full.iterrows():
        k = row['key']
        if k in cup_ht_map.index:
            cup_row = cup_ht_map.loc[k]
            if isinstance(cup_row, pd.DataFrame):
                cup_row = cup_row.iloc[0]
            if pd.isna(row['Half-time Home Goals']) and pd.notna(cup_row['Half-time Home Goals']):
                df_full.at[idx, 'Half-time Home Goals'] = cup_row['Half-time Home Goals']
            if pd.isna(row['Half-time Away Goals']) and pd.notna(cup_row['Half-time Away Goals']):
                df_full.at[idx, 'Half-time Away Goals'] = cup_row['Half-time Away Goals']
            if (not row['Win conditions']) and cup_row['Win conditions']:
                df_full.at[idx, 'Win conditions'] = cup_row['Win conditions']
                
    df_full.drop(columns=['key'], inplace=True)
    return df_full

if __name__ == '__main__':
    base_dir = '/home/na/code/fifaWorldCup/2014-2026'
    
    # Parse 2014 to 2026 matches
    df_2014_2026 = merge_and_enrich_matches(base_dir, target_years=[2014, 2018, 2022, 2026])
    
    # Export to CSV
    out_file = '/home/na/code/fifaWorldCup/WorldCupMatches_2014_2026.csv'
    df_2014_2026.to_csv(out_file, index=False, encoding='utf-8')
    print(f"\nSuccessfully generated {out_file} with {len(df_2014_2026)} matches!")
    print(df_2014_2026.info())
