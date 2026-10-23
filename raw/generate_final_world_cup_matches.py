import os
import re
import pandas as pd

def get_host_countries(base_dir):
    """
    Extracts host country from folder names like:
    2018--russia -> Russia
    2022--qatar -> Qatar
    2026--canada-usa-mexico -> Canada, USA & Mexico
    """
    hosts = {
        1930: 'Uruguay', 1934: 'Italy', 1938: 'France', 1950: 'Brazil',
        1954: 'Switzerland', 1958: 'Sweden', 1962: 'Chile', 1966: 'England',
        1970: 'Mexico', 1974: 'West Germany', 1978: 'Argentina', 1982: 'Spain',
        1986: 'Mexico', 1990: 'Italy', 1994: 'USA', 1998: 'France',
        2002: 'Korea/Japan', 2006: 'Germany', 2010: 'South Africa', 2014: 'Brazil',
        2018: 'Russia', 2022: 'Qatar', 2026: 'Canada/USA/Mexico'
    }
    
    dirs = [d for d in os.listdir(base_dir) if re.match(r'^\d{4}--', d)]
    for d in sorted(dirs):
        m = re.match(r'^(\d{4})--(.*)$', d)
        if m:
            yr = int(m.group(1))
            raw_host = m.group(2)
            if yr not in hosts:
                clean_host = raw_host.replace('_', ' ').replace('-', ' ').title()
                hosts[yr] = clean_host
                
    return hosts

def get_team_initials_dict():
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
    return initials

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
        suffix = '10' # Group stage
    return int(f"{year}{suffix}")

def build_2018_2026_dataset():
    base_dir = '/home/na/code/fifaWorldCup/2014-2026'
    input_csv = '/home/na/code/fifaWorldCup/WorldCupMatches_1930_2026.csv'
    
    if not os.path.exists(input_csv):
        from parse_all_txt_to_csv import parse_all_matches
        df = parse_all_matches(base_dir)
    else:
        df = pd.read_csv(input_csv)
        
    hosts = get_host_countries(base_dir)
    team_initials = get_team_initials_dict()
    
    # Filter only 2018 to 2026
    df = df[(df['Year'] >= 2018) & (df['Year'] <= 2026)].copy()
    
    round_ids = []
    match_ids = []
    home_inits = []
    away_inits = []
    host_countries = []
    
    next_match_id = 300186510
    
    for idx, row in df.iterrows():
        yr = int(row['Year'])
        h_team = str(row['Home Team Name']).strip()
        a_team = str(row['Away Team Name']).strip()
        stage = str(row['Stage']).strip()
        
        host_countries.append(hosts.get(yr, ''))
        round_ids.append(get_stage_round_id(yr, stage))
        match_ids.append(next_match_id)
        next_match_id += 1
        
        h_init = team_initials.get(h_team, h_team[:3].upper())
        a_init = team_initials.get(a_team, a_team[:3].upper())
        
        home_inits.append(h_init)
        away_inits.append(a_init)
        
    df['Country'] = host_countries
    df['RoundID'] = round_ids
    df['MatchID'] = match_ids
    df['Home Team Initials'] = home_inits
    df['Away Team Initials'] = away_inits
    
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
    
    print(f"Successfully generated {out_exact} with {len(df)} matches and 20 columns!")
    print(f"Successfully generated {out_with_host} with {len(df)} matches and 21 columns!")

if __name__ == '__main__':
    build_2018_2026_dataset()
