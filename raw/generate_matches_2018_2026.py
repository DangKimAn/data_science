import os
import re
import glob
import pandas as pd

def parse_matches_2018_2026(base_dir):
    """
    Parses matches from 2018, 2022, 2026 inside base_dir (e.g. 2018-2026/more/ and tournament dirs).
    """
    more_dir = os.path.join(base_dir, 'more')
    target_files = ['2018_full.txt', '2022_full.txt', '2026_full.txt']
    
    matches = []
    
    year_re = re.compile(r'=\s*World\s*Cup\s*(\d{4})', re.IGNORECASE)
    stage_re = re.compile(r'^▪+\s*(.+)$')
    fixture_re = re.compile(
        r'^\s*([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+v\s+([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+(\d+)\s*-\s*(\d+)(?:\s+([a-zA-Z0-9\.\,\s\(\)\-]+))?$'
    )
    refs_re = re.compile(r'^\s*Refs:\s*(.+)$')
    
    for tf in target_files:
        fpath = os.path.join(more_dir, tf)
        if not os.path.exists(fpath):
            continue
            
        m_yr = re.search(r'(\d{4})_full\.txt', tf)
        default_year = int(m_yr.group(1)) if m_yr else None
        
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        year = default_year
        current_stage = 'Group Stage'
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip('\r\n')
            
            m_year = year_re.search(line)
            if m_year:
                year = int(m_year.group(1))
                i += 1
                continue
                
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
                        
                        ht_home, ht_away = None, None
                        win_cond = ""
                        
                        if extra_info:
                            m_ht = re.search(r'\((\d+)\s*-\s*(\d+)\)', extra_info)
                            if m_ht:
                                ht_home = int(m_ht.group(1))
                                ht_away = int(m_ht.group(2))
                            if 'pen' in extra_info or 'a.e.t' in extra_info:
                                win_cond = extra_info
                                
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

def enrich_half_time_scores(df, base_dir):
    """
    Reads cup.txt and cup_finals.txt from tournament directories
    (2018--russia, 2022--qatar, 2026--canada-usa-mexico) to fill in half-time goals.
    """
    cup_match_re = re.compile(
        r'^\s*([0-9]{1,2}:[0-9]{2}(?:\s*UTC[+-]\d+)?)\s+'
        r'([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+'
        r'(?:v\s+)?'
        r'(\d+)\s*-\s*(\d+)'
        r'(?:\s+([a-zA-Z0-9\.\,\s\(\)\-]+?))?'
        r'\s+([A-Za-zÀ-ÿ\s\.\-\'\&]+?)\s+'
        r'@'
    )
    
    ht_data = {}
    target_dirs = [d for d in os.listdir(base_dir) if any(d.startswith(y) for y in ['2018', '2022', '2026'])]
    
    for td in target_dirs:
        m_yr = re.match(r'^(\d{4})--', td)
        if not m_yr: continue
        yr = int(m_yr.group(1))
        
        td_path = os.path.join(base_dir, td)
        for fn in ['cup.txt', 'cup_finals.txt']:
            fp = os.path.join(td_path, fn)
            if not os.path.exists(fp): continue
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    m = cup_match_re.match(line)
                    if m:
                        h_t = re.sub(r'[^a-zA-Z0-9]', '', m.group(2).lower())
                        a_t = re.sub(r'[^a-zA-Z0-9]', '', m.group(6).lower())
                        notes = m.group(5) or ""
                        m_ht = re.search(r'\((\d+)\s*-\s*(\d+)', notes)
                        if m_ht:
                            k = f"{yr}_{h_t}_{a_t}"
                            ht_data[k] = (int(m_ht.group(1)), int(m_ht.group(2)), notes)
                            
    for idx, row in df.iterrows():
        yr = row['Year']
        h_t = re.sub(r'[^a-zA-Z0-9]', '', str(row['Home Team Name']).lower())
        a_t = re.sub(r'[^a-zA-Z0-9]', '', str(row['Away Team Name']).lower())
        k = f"{yr}_{h_t}_{a_t}"
        if k in ht_data:
            ht_h, ht_a, notes = ht_data[k]
            if pd.isna(row['Half-time Home Goals']):
                df.at[idx, 'Half-time Home Goals'] = ht_h
            if pd.isna(row['Half-time Away Goals']):
                df.at[idx, 'Half-time Away Goals'] = ht_a
            if not row['Win conditions'] and ('pen' in notes or 'a.e.t' in notes):
                df.at[idx, 'Win conditions'] = notes
                
    return df

def get_stage_round_id(year, stage):
    st = str(stage).lower()
    if 'final' in st and 'semi' not in st and 'quarter' not in st:
        suffix = '60'
    elif 'third' in st or 'play-off' in st or 'bronze' in st:
        suffix = '50'
    elif 'semi' in st:
        suffix = '40'
    elif 'quarter' in st:
        suffix = '30'
    elif '16' in st or 'second round' in st:
        suffix = '20'
    else:
        suffix = '10'
    return int(f"{year}{suffix}")

def run():
    # Detect base directory (support both 2018-2026 and 2014-2026)
    base_dir = '/home/na/code/fifaWorldCup/2018-2026'
    if not os.path.exists(base_dir):
        base_dir = '/home/na/code/fifaWorldCup/2014-2026'
        
    print(f"Reading from folder: {base_dir}")
    
    # 1. Parse host country from folder names
    host_countries = {}
    for d in os.listdir(base_dir):
        m = re.match(r'^(\d{4})--(.*)$', d)
        if m:
            yr = int(m.group(1))
            raw_host = m.group(2)
            clean_host = raw_host.replace('_', ' ').replace('-', ' ').title()
            # Standard formatting
            if 'Usa' in clean_host: clean_host = clean_host.replace('Usa', 'USA')
            if 'South Korea N Japan' in clean_host: clean_host = 'Korea/Japan'
            if 'Canada Usa Mexico' in clean_host: clean_host = 'Canada/USA/Mexico'
            host_countries[yr] = clean_host

    # Specific hosts for 2018, 2022, 2026
    hosts_map = {
        2018: host_countries.get(2018, 'Russia'),
        2022: host_countries.get(2022, 'Qatar'),
        2026: host_countries.get(2026, 'Canada/USA/Mexico')
    }
    print("Host countries detected from folder names:")
    for y, h in hosts_map.items():
        print(f"  {y}: {h}")

    # 2. Team Initials (FIFA 3-letter codes)
    initials = {
        'Algeria': 'ALG', 'Angola': 'ANG', 'Argentina': 'ARG', 'Australia': 'AUS',
        'Austria': 'AUT', 'Belgium': 'BEL', 'Bolivia': 'BOL', 'Bosnia and Herzegovina': 'BIH',
        'Bosnia-Herzegovina': 'BIH', 'Bosnia & Herzegovina': 'BIH', 'Brazil': 'BRA',
        'Bulgaria': 'BUL', 'Cameroon': 'CMR', 'Canada': 'CAN', 'Cape Verde': 'CPV',
        'Cabo Verde': 'CPV', 'Chile': 'CHI', 'China': 'CHN', 'China PR': 'CHN',
        'Colombia': 'COL', 'Congo DR': 'COD', 'DR Congo': 'COD', 'Costa Rica': 'CRC',
        'Croatia': 'CRO', 'Cuba': 'CUB', 'Curaçao': 'CUW', 'Czech Republic': 'CZE',
        'Czechia': 'CZE', 'Czechoslovakia': 'TCH', "Côte d'Ivoire": 'CIV',
        'Ivory Coast': 'CIV', 'Denmark': 'DEN', 'East Germany': 'GDR', 'German DR': 'GDR',
        'Ecuador': 'ECU', 'Egypt': 'EGY', 'El Salvador': 'SLV', 'England': 'ENG',
        'France': 'FRA', 'Germany': 'GER', 'Germany FR': 'FRG', 'West Germany': 'FRG',
        'Ghana': 'GHA', 'Greece': 'GRE', 'Haiti': 'HAI', 'Honduras': 'HON',
        'Hungary': 'HUN', 'Iceland': 'ISL', 'Iran': 'IRN', 'IR Iran': 'IRN',
        'Iraq': 'IRQ', 'Ireland': 'IRL', 'Republic of Ireland': 'IRL', 'Northern Ireland': 'NIR',
        'Israel': 'ISR', 'Italy': 'ITA', 'Jamaica': 'JAM', 'Japan': 'JPN',
        'Jordan': 'JOR', 'Korea DPR': 'PRK', 'North Korea': 'PRK', 'Korea Republic': 'KOR',
        'South Korea': 'KOR', 'Kuwait': 'KUW', 'Mexico': 'MEX', 'Morocco': 'MAR',
        'Netherlands': 'NED', 'New Zealand': 'NZL', 'Nigeria': 'NGA', 'Norway': 'NOR',
        'Panama': 'PAN', 'Paraguay': 'PAR', 'Peru': 'PER', 'Poland': 'POL',
        'Portugal': 'POR', 'Qatar': 'QAT', 'Romania': 'ROU', 'Russia': 'RUS',
        'Soviet Union': 'URS', 'Saudi Arabia': 'KSA', 'Scotland': 'SCO', 'Senegal': 'SEN',
        'Serbia': 'SRB', 'Serbia and Montenegro': 'SCG', 'Slovakia': 'SVK',
        'Slovenia': 'SVN', 'South Africa': 'RSA', 'Spain': 'ESP', 'Sweden': 'SWE',
        'Switzerland': 'SUI', 'Togo': 'TOG', 'Trinidad and Tobago': 'TRI', 'Tunisia': 'TUN',
        'Turkey': 'TUR', 'Ukraine': 'UKR', 'United Arab Emirates': 'UAE', 'UAE': 'UAE',
        'Uruguay': 'URU', 'USA': 'USA', 'Uzbekistan': 'UZB', 'Wales': 'WAL',
        'Yugoslavia': 'YUG', 'Zaire': 'ZAI'
    }

    # 3. Parse matches
    df = parse_matches_2018_2026(base_dir)
    df = enrich_half_time_scores(df, base_dir)
    
    # 4. Add MatchID, RoundID, Initials, Host Country
    round_ids = []
    match_ids = []
    home_inits = []
    away_inits = []
    hosts_col = []
    
    next_match_id = 300186510
    
    for idx, row in df.iterrows():
        yr = int(row['Year'])
        h_team = str(row['Home Team Name']).strip()
        a_team = str(row['Away Team Name']).strip()
        stage = str(row['Stage']).strip()
        
        hosts_col.append(hosts_map.get(yr, ''))
        round_ids.append(get_stage_round_id(yr, stage))
        match_ids.append(next_match_id)
        next_match_id += 1
        
        home_inits.append(initials.get(h_team, h_team[:3].upper()))
        away_inits.append(initials.get(a_team, a_team[:3].upper()))
        
    df['Country'] = hosts_col
    df['RoundID'] = round_ids
    df['MatchID'] = match_ids
    df['Home Team Initials'] = home_inits
    df['Away Team Initials'] = away_inits
    
    # User's exact 20 columns
    exact_20_cols = [
        'Year', 'Datetime', 'Stage', 'Stadium', 'City',
        'Home Team Name', 'Home Team Goals', 'Away Team Goals', 'Away Team Name',
        'Win conditions', 'Attendance', 'Half-time Home Goals', 'Half-time Away Goals',
        'Referee', 'Assistant 1', 'Assistant 2',
        'RoundID', 'MatchID', 'Home Team Initials', 'Away Team Initials'
    ]
    
    cols_with_country = [
        'Year', 'Country', 'Datetime', 'Stage', 'Stadium', 'City',
        'Home Team Name', 'Home Team Goals', 'Away Team Goals', 'Away Team Name',
        'Win conditions', 'Attendance', 'Half-time Home Goals', 'Half-time Away Goals',
        'Referee', 'Assistant 1', 'Assistant 2',
        'RoundID', 'MatchID', 'Home Team Initials', 'Away Team Initials'
    ]
    
    out_exact = '/home/na/code/fifaWorldCup/WorldCupMatches_2018_2026.csv'
    out_with_host = '/home/na/code/fifaWorldCup/WorldCupMatches_with_HostCountry_2018_2026.csv'
    
    df[exact_20_cols].to_csv(out_exact, index=False, encoding='utf-8')
    df[cols_with_country].to_csv(out_with_host, index=False, encoding='utf-8')
    
    print(f"\nSaved exact 20 columns: {out_exact} ({len(df)} rows)")
    print(f"Saved with Host Country: {out_with_host} ({len(df)} rows)")
    print("\nBreakdown by year:")
    print(df['Year'].value_counts().sort_index())

if __name__ == '__main__':
    run()
