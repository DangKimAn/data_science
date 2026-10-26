#!/usr/bin/env python3
"""
build_master_dataset.py
-----------------------
ETL Pipeline for FIFA World Cup Analysis (1930 - 2026).
Solves:
1. Recovers missing Attendance for 1930-2014 (836 matches) from WorldCupMatches.csv.
2. Deduplicates 2014 matches (removes 16 Kaggle duplicate rows).
3. Fills missing attendance for Germany vs Algeria 2014 (43,063).
4. Cleans corrupted team strings ('rn\">', bad encoding).
5. Appends 2018-2026 matches (100% attendance).
6. Performs Feature Engineering:
   - Era_Format (16, 24, 32, 48 Teams)
   - Stage_Group (1. Group Stage, 2. Early Knockout, 3. Deep Knockout)
   - Stage_Detail (First Group Stage, Second Group Stage 1974/78/82, Early Knockout, Deep Knockout)
   - Matchday (Matchday 1, Matchday 2, Matchday 3 for group stages)
   - Total_Goals, Goal_Margin, Margin_Category
   - Match_Resolution, Is_Extra_Time, Is_Penalties, Is_Golden_Goal
   - Home_Confed, Away_Confed
   - Occupancy_Rate
7. Exports:
   - WorldCupMatches_with_HostCountry_1930_2026.csv (Fixed raw dataset)
   - worldcup_master_cleaned.csv (Full master dataset with all features)
   - dim_tournaments.csv
   - dim_stadiums.csv
   - dim_confederations.csv
   - dim_group_standings.csv
   - dim_qualifiers_summary.csv
   - dim_financials.csv
   - dim_dead_rubbers.csv
"""

import os
import re
import pandas as pd
import numpy as np
from dateutil import parser as dt_parser
from functools import cmp_to_key

BASE_DIR = '/home/na/code/fifaWorldCup'
RAW_DIR = os.path.join(BASE_DIR, 'raw')
PROD_DIR = os.path.join(BASE_DIR, 'production')

HOSTS = {
    1930: 'Uruguay', 1934: 'Italy', 1938: 'France', 1950: 'Brazil',
    1954: 'Switzerland', 1958: 'Sweden', 1962: 'Chile', 1966: 'England',
    1970: 'Mexico', 1974: 'West Germany', 1978: 'Argentina', 1982: 'Spain',
    1986: 'Mexico', 1990: 'Italy', 1994: 'USA', 1998: 'France',
    2002: 'Korea/Japan', 2006: 'Germany', 2010: 'South Africa', 2014: 'Brazil',
    2018: 'Russia', 2022: 'Qatar', 2026: 'Canada/USA/Mexico'
}

TEAM_CLEAN_MAP = {
    'rn">Bosnia and Herzegovina': 'Bosnia and Herzegovina',
    'rn">Republic of Ireland': 'Republic of Ireland',
    'rn">Serbia and Montenegro': 'Serbia and Montenegro',
    'rn">Trinidad and Tobago': 'Trinidad and Tobago',
    'rn">United Arab Emirates': 'United Arab Emirates',
    "Cte d'Ivoire": "Côte d'Ivoire",
    "C\ufffdd'Ivoire": "Côte d'Ivoire",
    'IR Iran': 'Iran',
    'China PR': 'China',
    'Korea Republic': 'South Korea',
    'Korea DPR': 'North Korea',
}

CONFED_MAP = {
    # UEFA (Europe)
    'Albania': 'UEFA', 'Austria': 'UEFA', 'Belgium': 'UEFA', 'Bosnia and Herzegovina': 'UEFA',
    'Bulgaria': 'UEFA', 'Croatia': 'UEFA', 'Czech Republic': 'UEFA', 'Czechoslovakia': 'UEFA',
    'Denmark': 'UEFA', 'East Germany': 'UEFA', 'German DR': 'UEFA', 'England': 'UEFA',
    'France': 'UEFA', 'Germany': 'UEFA', 'Germany FR': 'UEFA', 'West Germany': 'UEFA',
    'Greece': 'UEFA', 'Hungary': 'UEFA', 'Iceland': 'UEFA', 'Israel': 'UEFA',
    'Italy': 'UEFA', 'Netherlands': 'UEFA', 'Northern Ireland': 'UEFA', 'Norway': 'UEFA',
    'Poland': 'UEFA', 'Portugal': 'UEFA', 'Republic of Ireland': 'UEFA', 'Romania': 'UEFA',
    'Russia': 'UEFA', 'Soviet Union': 'UEFA', 'Scotland': 'UEFA', 'Serbia': 'UEFA',
    'Serbia and Montenegro': 'UEFA', 'Yugoslavia': 'UEFA', 'Slovakia': 'UEFA', 'Slovenia': 'UEFA',
    'Spain': 'UEFA', 'Sweden': 'UEFA', 'Switzerland': 'UEFA', 'Turkey': 'UEFA',
    'Ukraine': 'UEFA', 'Wales': 'UEFA',
    # CONMEBOL (South America)
    'Argentina': 'CONMEBOL', 'Bolivia': 'CONMEBOL', 'Brazil': 'CONMEBOL', 'Chile': 'CONMEBOL',
    'Colombia': 'CONMEBOL', 'Ecuador': 'CONMEBOL', 'Paraguay': 'CONMEBOL', 'Peru': 'CONMEBOL',
    'Uruguay': 'CONMEBOL', 'Venezuela': 'CONMEBOL',
    # CONCACAF (North, Central America & Caribbean)
    'Canada': 'CONCACAF', 'Costa Rica': 'CONCACAF', 'Cuba': 'CONCACAF', 'Curaçao': 'CONCACAF',
    'El Salvador': 'CONCACAF', 'Haiti': 'CONCACAF', 'Honduras': 'CONCACAF', 'Jamaica': 'CONCACAF',
    'Mexico': 'CONCACAF', 'Panama': 'CONCACAF', 'Trinidad and Tobago': 'CONCACAF', 'USA': 'CONCACAF',
    # CAF (Africa)
    'Algeria': 'CAF', 'Angola': 'CAF', 'Cameroon': 'CAF', 'Cabo Verde': 'CAF', 'Cape Verde': 'CAF',
    'Congo DR': 'CAF', 'DR Congo': 'CAF', 'Zaire': 'CAF', "Côte d'Ivoire": 'CAF', 'Egypt': 'CAF',
    'Ghana': 'CAF', 'Morocco': 'CAF', 'Nigeria': 'CAF', 'Senegal': 'CAF', 'South Africa': 'CAF',
    'Togo': 'CAF', 'Tunisia': 'CAF',
    # AFC (Asia)
    'Australia': 'AFC', 'China': 'AFC', 'China PR': 'AFC', 'Dutch East Indies': 'AFC',
    'Indonesia': 'AFC', 'Iran': 'AFC', 'IR Iran': 'AFC', 'Iraq': 'AFC', 'Japan': 'AFC',
    'Jordan': 'AFC', 'Kuwait': 'AFC', 'North Korea': 'AFC', 'Korea DPR': 'AFC',
    'Qatar': 'AFC', 'Saudi Arabia': 'AFC', 'South Korea': 'AFC', 'Korea Republic': 'AFC',
    'United Arab Emirates': 'AFC', 'UAE': 'AFC', 'Uzbekistan': 'AFC',
    # OFC (Oceania)
    'New Zealand': 'OFC'
}

KNOWN_STADIUM_CAPACITIES = {
    # 2026 Stadiums
    'Mexico City Stadium': 87523,
    'New York/New Jersey Stadium': 82500,
    'Dallas Stadium': 80000,
    'Kansas City Stadium': 76416,
    'Houston Stadium': 72220,
    'Atlanta Stadium': 71000,
    'Los Angeles Stadium': 70240,
    'Philadelphia Stadium': 69796,
    'Seattle Stadium': 69000,
    'San Francisco Bay Area Stadium': 68500,
    'Boston Stadium': 65878,
    'Miami Stadium': 64767,
    'BC Place Vancouver': 54500,
    'Monterrey Stadium': 53500,
    'Guadalajara Stadium': 48071,
    'Toronto Stadium': 45000,
    # 2022 Stadiums
    'Lusail Stadium': 88966,
    'Al Bayt Stadium': 68895,
    'Khalifa International Stadium': 45857,
    'Ahmad Bin Ali Stadium': 45032,
    'Education City Stadium': 44667,
    'Al Thumama Stadium': 44400,
    'Al Janoub Stadium': 44325,
    'Stadium 974': 44089,
    # 2018 Stadiums
    'Lenin': 81000,
    'Luzhniki Stadium': 81000,
    'Krestovsky Stadium': 64468,
    'Fisht Olympic Stadium': 48000,
    'Samara Arena': 45000,
    'Ak Bars Arena': 45000,
    'Rostov Arena': 45000,
    'Nizhny Novgorod Stadium': 45000,
    'Central Stadium': 45000,
    'Otkrytiye Arena': 45000,
    'Mordovia Arena': 44000,
    'Kaliningrad Stadium': 35000,
    'Ekaterinburg Arena': 35000,
    # 1994 USA Stadiums
    'Rose Bowl': 94194,
    'Stanford Stadium': 84147,
    'Pontiac Silverdome': 80000,
    'Giants Stadium': 77000,
    'Cotton Bowl': 72000,
    'Citrus Bowl': 70000,
    'Soldier Field': 67000,
    'Foxboro Stadium': 61000,
    'RFK Stadium': 56000,
    # Historic Key Stadiums
    'Maracanã - Estádio Jornalista Mário Filho': 173850,
    'Stade Vélodrome': 67394,
    'Nou Camp - Estadio León': 31297,
    'Estadio José María Minella': 35180,
    'Estadio Olímpico Chateau Carreras': 47851,
    'Estadio Municipal de Balaídos': 31800,
    'Estadio Olímpico Universitario': 72000,
    'Estadio Azteca': 114600,
    'Wembley Stadium': 98270,
    'Estadio Centenario': 80000,
    'Camp Nou': 98000,
    'Santiago Bernabeu': 90000,
    'Stadio Giuseppe Meazza': 85000,
    'Stadio Olimpico': 80000,
    'Stade de France': 80000,
    'Olympiastadion': 72000,
    'Soccer City Stadium': 84490,
    'Estadio do Maracana': 74738,
}

def clean_team_name(name):
    if not isinstance(name, str):
        return name
    name = name.strip()
    name_lower = name.lower()
    if 'ivoire' in name_lower or 'ivory' in name_lower:
        return "Côte d'Ivoire"
    if 'bosnia' in name_lower:
        return 'Bosnia and Herzegovina'
    if 'republic of ireland' in name_lower:
        return 'Republic of Ireland'
    if 'trinidad' in name_lower:
        return 'Trinidad and Tobago'
    if 'united arab emirates' in name_lower:
        return 'United Arab Emirates'
    if 'serbia and montenegro' in name_lower:
        return 'Serbia and Montenegro'
    return TEAM_CLEAN_MAP.get(name, name)

def clean_stadium_name(name):
    if not isinstance(name, str):
        return name
    name = name.strip()
    name = name.replace('Stade V\ufffdlodrome', 'Stade Vélodrome')
    name = name.replace('Stade Vlodrome', 'Stade Vélodrome')
    name = name.replace('Maracan\ufffd - Est\ufffddio Jornalista M\ufffdrio Filho', 'Maracanã - Estádio Jornalista Mário Filho')
    name = name.replace('Maracan - Estdio Jornalista Mrio Filho', 'Maracanã - Estádio Jornalista Mário Filho')
    name = name.replace('Nou Camp - Estadio Le\ufffdn', 'Nou Camp - Estadio León')
    name = name.replace('Nou Camp - Estadio Len', 'Nou Camp - Estadio León')
    name = name.replace('Estadio Jos\ufffd Mar\ufffda Minella', 'Estadio José María Minella')
    name = name.replace('Estadio Jos Mara Minella', 'Estadio José María Minella')
    name = name.replace('Estadio Ol\ufffdmpico Chateau Carreras', 'Estadio Olímpico Chateau Carreras')
    name = name.replace('Estadio Olmpico Chateau Carreras', 'Estadio Olímpico Chateau Carreras')
    name = name.replace('Estadio Municipal de Bala\ufffddos', 'Estadio Municipal de Balaídos')
    name = name.replace('Estadio Municipal de Balados', 'Estadio Municipal de Balaídos')
    name = name.replace('Estadio Ol\ufffdmpico Universitario', 'Estadio Olímpico Universitario')
    name = name.replace('Estadio Olmpico Universitario', 'Estadio Olímpico Universitario')
    return name

def clean_city_name(name):
    if not isinstance(name, str):
        return name
    name = name.strip()
    name = name.replace('Malm\ufffd', 'Malmö')
    name = name.replace('Malm', 'Malmö')
    name = name.replace('Norrk\ufffdPing', 'Norrköping')
    name = name.replace('NorrkPing', 'Norrköping')
    name = name.replace('D\ufffdSseldorf', 'Düsseldorf')
    name = name.replace('DSseldorf', 'Düsseldorf')
    name = name.replace('La Coru\ufffdA', 'La Coruña')
    name = name.replace('La CoruA', 'La Coruña')
    return name

def clean_referee_name(name):
    if not isinstance(name, str):
        return name
    name = name.strip()
    name = name.replace('St\ufffdphane LANNOY (FRA)', 'Stéphane LANNOY (FRA)')
    name = name.replace('Oleg\ufffdrio BENQUEREN\ufffdA (POR)', 'Olegário BENQUERENÇA (POR)')
    name = name.replace('Bj\ufffdrn KUIPERS (NED)', 'Björn KUIPERS (NED)')
    name = name.replace('C\ufffdneyt \ufffdAKIR (TUR)', 'Cüneyt ÇAKIR (TUR)')
    return name

def standardize_datetime(dt_str):
    if not isinstance(dt_str, str):
        return dt_str
    s = dt_str.strip()
    # Remove day of week at beginning (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
    s_clean = re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+', '', s)
    # Remove UTC offset at end (e.g. UTC+3, UTC-4, UTC+03:00) so it reflects local kickoff time consistently
    s_clean = re.sub(r'\s+UTC[+-]\d+(:\d+)?', '', s_clean)
    # Replace ' - ' with space
    s_clean = s_clean.replace(' - ', ' ')
    try:
        dt = dt_parser.parse(s_clean)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return dt_str

def categorize_era(year):
    y = int(year)
    if y <= 1978:
        return '16 Teams (1930-1978)'
    elif y <= 1994:
        return '24 Teams (1982-1994)'
    elif y <= 2022:
        return '32 Teams (1998-2022)'
    else:
        return '48 Teams (2026)'

def categorize_stage(year, stage):
    s = str(stage).strip().lower()
    y = int(year)
    
    # 1950 Final Round was a 4-team group
    if y == 1950 and 'final round' in s:
        return '1. Group Stage', 'Second Group Stage'
        
    # 1974, 1978 Second Group stage (Group A, B)
    if y in [1974, 1978] and s in ['group a', 'group b']:
        return '1. Group Stage', 'Second Group Stage'
        
    # 1982 Second Group stage (Group A, B, C, D)
    if y == 1982 and s in ['group a', 'group b', 'group c', 'group d']:
        return '1. Group Stage', 'Second Group Stage'
        
    # Regular group stages
    if 'group' in s:
        return '1. Group Stage', 'First Group Stage'
        
    # Early Knockout
    if any(k in s for k in ['round of 32', 'round of 16', '1st round', 'first round', 'preliminary round']):
        return '2. Early Knockout', 'Early Knockout'
        
    # Deep Knockout
    if any(k in s for k in ['quarter', 'semi', 'final', 'third', 'bronze', 'play-off']):
        return '3. Deep Knockout', 'Deep Knockout'
        
    return '1. Group Stage', 'First Group Stage'

def calculate_matchdays(df):
    matchdays = ['Not Group Stage'] * len(df)
    for (year, stage), group_idx in df.groupby(['Year', 'Stage']).groups.items():
        if 'group' not in str(stage).lower():
            continue
            
        # Sort chronologically by Datetime to avoid row-order dependency
        sorted_indices = df.loc[group_idx].sort_values('Datetime').index
        team_games = {}
        for idx in sorted_indices:
            row = df.loc[idx]
            h = row['Home Team Name']
            a = row['Away Team Name']
            g_h = team_games.get(h, 0)
            g_a = team_games.get(a, 0)
            md = max(g_h, g_a) + 1
            if year == 1954 and md == 3 and 'group' in str(stage).lower():
                matchdays[idx] = 'Matchday 3 (Play-off)'
            elif year == 1958 and md == 4:
                matchdays[idx] = 'Matchday 4 (Play-off)'
            else:
                matchdays[idx] = f'Matchday {md}'
            team_games[h] = g_h + 1
            team_games[a] = g_a + 1
            
    return matchdays

def parse_match_resolution(year, stage_group, win_conditions, goal_margin):
    wc = str(win_conditions).lower() if pd.notna(win_conditions) else ''
    if 'pen' in wc:
        return '4. Penalties', True, True
    elif 'extra time' in wc or 'a.e.t.' in wc or 'golden goal' in wc:
        return '3. Extra Time', True, False
    elif goal_margin == 0 and stage_group != '1. Group Stage':
        # Historical replay matches before penalties era (1934 Italy-Spain, 1938 Brazil-Czechoslovakia)
        return '3. Extra Time', True, False
    else:
        if goal_margin >= 2:
            return '1. Normal Time - Blowout (>=2)', False, False
        else:
            return '2. Normal Time - Close (<=1)', False, False

def load_and_merge_datasets():
    print("1. Loading raw files...")
    f_orig = os.path.join(RAW_DIR, 'WorldCupMatches.csv')
    f_2018_2026 = os.path.join(RAW_DIR, 'WorldCupMatches_with_HostCountry_2018_2026.csv')
    
    # 1. Load 1930 - 2014 from WorldCupMatches.csv
    df_1930 = pd.read_csv(f_orig).dropna(how='all')
    df_1930 = df_1930.drop_duplicates(subset=['MatchID']).copy()
    
    # Clean year and assign Country
    df_1930['Year'] = df_1930['Year'].astype(int)
    df_1930['Country'] = df_1930['Year'].map(HOSTS)
    
    # Fill missing attendance for Germany vs Algeria (2014)
    df_1930.loc[df_1930['Attendance'].isna(), 'Attendance'] = 43063.0
    
    # Clean team names
    df_1930['Home Team Name'] = df_1930['Home Team Name'].apply(clean_team_name)
    df_1930['Away Team Name'] = df_1930['Away Team Name'].apply(clean_team_name)
    
    # 2. Load 2018 - 2026
    df_2018 = pd.read_csv(f_2018_2026)
    df_2018['Year'] = df_2018['Year'].astype(int)
    df_2018['Home Team Name'] = df_2018['Home Team Name'].apply(clean_team_name)
    df_2018['Away Team Name'] = df_2018['Away Team Name'].apply(clean_team_name)
    
    # Ensure unique MatchID for 2018-2026 starting after 1930-2014 max MatchID (solves collision)
    max_id_1930 = int(df_1930['MatchID'].max())
    df_2018['MatchID'] = [int(max_id_1930 + 1 + i) for i in range(len(df_2018))]
    
    # Standard columns
    cols = [
        'Year', 'Country', 'Datetime', 'Stage', 'Stadium', 'City',
        'Home Team Name', 'Home Team Goals', 'Away Team Goals', 'Away Team Name',
        'Win conditions', 'Attendance', 'Half-time Home Goals', 'Half-time Away Goals',
        'Referee', 'Assistant 1', 'Assistant 2', 'RoundID', 'MatchID',
        'Home Team Initials', 'Away Team Initials'
    ]
    
    df_master = pd.concat([df_1930[cols], df_2018[cols]], ignore_index=True)
    df_master['Country'] = df_master['Year'].map(HOSTS)
    
    # Standardize 1982 Round 2 stages (RoundID 294) to Group A, B, C, D (FIFA official nomenclature)
    mask_1982_r2 = (df_master['Year'] == 1982) & (df_master['RoundID'] == 294)
    stage_map_1982 = {'Group 1': 'Group A', 'Group 2': 'Group B', 'Group 3': 'Group C', 'Group 4': 'Group D'}
    df_master.loc[mask_1982_r2, 'Stage'] = df_master.loc[mask_1982_r2, 'Stage'].map(stage_map_1982)

    df_master['Attendance'] = df_master['Attendance'].astype(int)
    df_master['Home Team Goals'] = df_master['Home Team Goals'].astype(int)
    df_master['Away Team Goals'] = df_master['Away Team Goals'].astype(int)
    
    # Fill known missing half-time scores to ensure clean int dtype
    ht_fixes = {
        # 2018
        (2018, 'Spain', 'Russia'): (1, 1),
        (2018, 'Croatia', 'Denmark'): (1, 1),
        (2018, 'Colombia', 'England'): (0, 0),
        (2018, 'Russia', 'Croatia'): (1, 1),
        # 2022
        (2022, 'Netherlands', 'Qatar'): (1, 0),
        (2022, 'England', 'USA'): (0, 0),
        (2022, 'Mexico', 'Poland'): (0, 0),
        (2022, 'Denmark', 'Tunisia'): (0, 0),
        (2022, 'Tunisia', 'France'): (0, 0),
        (2022, 'Costa Rica', 'Germany'): (0, 1),
        (2022, 'Morocco', 'Croatia'): (0, 0),
        (2022, 'Croatia', 'Belgium'): (0, 0),
        (2022, 'Uruguay', 'South Korea'): (0, 0),
        (2022, 'Ghana', 'Uruguay'): (0, 2),
        (2022, 'South Korea', 'Portugal'): (1, 1),
        (2022, 'Japan', 'Croatia'): (1, 0),
        (2022, 'Morocco', 'Spain'): (0, 0),
        (2022, 'Croatia', 'Brazil'): (0, 0),
        (2022, 'Netherlands', 'Argentina'): (0, 1),
        (2022, 'Argentina', 'France'): (2, 0),
        # 2026
        (2026, 'Germany', 'Paraguay'): (0, 1),
        (2026, 'Netherlands', 'Morocco'): (0, 0),
        (2026, 'Belgium', 'Senegal'): (0, 1),
        (2026, 'Australia', 'Egypt'): (0, 1),
        (2026, 'Argentina', 'Cabo Verde'): (1, 0),
        (2026, 'Switzerland', 'Colombia'): (0, 0),
        (2026, 'Norway', 'England'): (1, 1),
        (2026, 'Argentina', 'Switzerland'): (1, 0),
        (2026, 'Spain', 'Argentina'): (0, 0),
    }
    for (yr, h, a), (ht_h, ht_a) in ht_fixes.items():
        mask = (df_master['Year'] == yr) & (df_master['Home Team Name'] == h) & (df_master['Away Team Name'] == a)
        if mask.any():
            df_master.loc[mask, 'Half-time Home Goals'] = ht_h
            df_master.loc[mask, 'Half-time Away Goals'] = ht_a

    df_master['Half-time Home Goals'] = df_master['Half-time Home Goals'].fillna(0).astype(int)
    df_master['Half-time Away Goals'] = df_master['Half-time Away Goals'].fillna(0).astype(int)
    df_master['RoundID'] = df_master['RoundID'].astype(int)
    df_master['MatchID'] = df_master['MatchID'].astype(int)
    df_master['Stadium'] = df_master['Stadium'].apply(clean_stadium_name)
    df_master['City'] = df_master['City'].apply(clean_city_name)
    df_master['Referee'] = df_master['Referee'].apply(clean_referee_name)
    df_master['Datetime'] = df_master['Datetime'].apply(standardize_datetime)
    
    print(f"Merged successfully: Total matches = {len(df_master)}")
    print(f"Missing attendance values: {df_master['Attendance'].isna().sum()}")
    
    return df_master

def perform_feature_engineering(df):
    print("2. Performing Feature Engineering...")
    
    # Era Format
    df['Era_Format'] = df['Year'].apply(categorize_era)
    
    # Stage grouping
    stage_res = [categorize_stage(row['Year'], row['Stage']) for _, row in df.iterrows()]
    df['Stage_Group'] = [r[0] for r in stage_res]
    df['Stage_Detail'] = [r[1] for r in stage_res]
    
    # Matchday for group stage
    df['Matchday'] = calculate_matchdays(df)
    
    # Goals and margins
    df['Total_Goals'] = df['Home Team Goals'] + df['Away Team Goals']
    df['Goal_Margin'] = (df['Home Team Goals'] - df['Away Team Goals']).abs()
    
    def get_margin_cat(margin):
        if margin <= 1:
            return '1. Sat Nut / Hoa (<=1 ban)'
        elif margin == 2:
            return '2. Cach Biet (2 ban)'
        else:
            return '3. Thang Dam (>=3 ban)'
            
    df['Margin_Category'] = df['Goal_Margin'].apply(get_margin_cat)
    
    # Match resolution and extra time
    res_list = [parse_match_resolution(row['Year'], row['Stage_Group'], row['Win conditions'], row['Goal_Margin']) for _, row in df.iterrows()]
    df['Match_Resolution'] = [r[0] for r in res_list]
    df['Is_Extra_Time'] = [r[1] for r in res_list]
    df['Is_Penalties'] = [r[2] for r in res_list]
    
    # Golden Goal matches
    golden_matches = (
        (df['Year'] == 1998) & (df['Home Team Name'] == 'France') & (df['Away Team Name'] == 'Paraguay') |
        (df['Year'] == 2002) & (df['Home Team Name'] == 'Sweden') & (df['Away Team Name'] == 'Senegal') |
        (df['Year'] == 2002) & (df['Home Team Name'] == 'South Korea') & (df['Away Team Name'] == 'Italy') |
        (df['Year'] == 2002) & (df['Home Team Name'] == 'Senegal') & (df['Away Team Name'] == 'Turkey')
    )
    df['Is_Golden_Goal'] = golden_matches | df['Win conditions'].astype(str).str.contains('Golden Goal', case=False, na=False)
    
    # Winner
    def get_winner(row):
        wc = str(row['Win conditions']).strip() if pd.notna(row['Win conditions']) else ''
        if 'penalties' in wc.lower() or 'pen.' in wc.lower():
            m1 = re.match(r'^(.*?)\s+win on penalties', wc, re.IGNORECASE)
            if m1 and m1.group(1).strip():
                return clean_team_name(m1.group(1).strip())
            m2 = re.search(r'win on penalties\s*\(\s*(\d+)\s*-\s*(\d+)\s*\)', wc, re.IGNORECASE)
            if m2:
                h_pens, a_pens = int(m2.group(1)), int(m2.group(2))
                return row['Home Team Name'] if h_pens > a_pens else row['Away Team Name']
            m3 = re.search(r'(\d+)\s*-\s*(\d+)\s*pen', wc, re.IGNORECASE)
            if m3:
                h_pens, a_pens = int(m3.group(1)), int(m3.group(2))
                return row['Home Team Name'] if h_pens > a_pens else row['Away Team Name']
        if row['Home Team Goals'] > row['Away Team Goals']:
            return row['Home Team Name']
        elif row['Home Team Goals'] < row['Away Team Goals']:
            return row['Away Team Name']
        else:
            return 'Draw'
    df['Winner'] = df.apply(get_winner, axis=1)
    
    # Confederations
    df['Home_Confederation'] = df['Home Team Name'].map(CONFED_MAP).fillna('Other')
    df['Away_Confederation'] = df['Away Team Name'].map(CONFED_MAP).fillna('Other')

    # Unified Team Names (mapping historical entities to modern successor nations)
    unified_map = {
        'Germany FR': 'Germany',
        'German DR': 'East Germany',
        'Soviet Union': 'Russia',
        'Yugoslavia': 'Serbia',
        'Serbia and Montenegro': 'Serbia',
        'Czechoslovakia': 'Czech Republic',
        'Zaire': 'Congo DR',
        'Dutch East Indies': 'Indonesia',
    }
    df['Home_Team_Unified'] = df['Home Team Name'].replace(unified_map)
    df['Away_Team_Unified'] = df['Away Team Name'].replace(unified_map)
    
    # Stadium Capacity & Occupancy Rate
    # Estimate capacity: Known capacity if exists, else max attendance of this stadium + 5% headroom
    max_att_by_stadium = df.groupby('Stadium')['Attendance'].max().to_dict()
    
    def get_stadium_capacity_info(stadium):
        if stadium in KNOWN_STADIUM_CAPACITIES:
            known_cap = KNOWN_STADIUM_CAPACITIES[stadium]
            max_att = max_att_by_stadium.get(stadium, 0)
            return max(known_cap, max_att), 'Official_Or_Historical'
        att = max_att_by_stadium.get(stadium, 40000)
        return int(max(att * 1.05, 30000)), 'Imputed_From_Attendance'
        
    stad_info = [get_stadium_capacity_info(s) for s in df['Stadium']]
    df['Max_Capacity'] = [s[0] for s in stad_info]
    df['Capacity_Source'] = [s[1] for s in stad_info]
    df['Occupancy_Rate'] = (df['Attendance'] / df['Max_Capacity'] * 100).round(2)
    # Clip occupancy at 100%
    df['Occupancy_Rate'] = df['Occupancy_Rate'].clip(upper=100.0)

    # 7. Merge Elo Ratings from dim_team_elo.csv
    dim_elo_file = os.path.join(PROD_DIR, 'dim_team_elo.csv')
    if os.path.exists(dim_elo_file):
        dim_elo = pd.read_csv(dim_elo_file)
        df = df.merge(
            dim_elo[['Year', 'Team_Name', 'Pre_Tournament_Elo', 'World_Rank']],
            left_on=['Year', 'Home Team Name'],
            right_on=['Year', 'Team_Name'],
            how='left'
        )
        df.rename(columns={'Pre_Tournament_Elo': 'Home_Team_Elo', 'World_Rank': 'Home_Team_World_Rank'}, inplace=True)
        df.drop(columns=['Team_Name'], inplace=True)

        df = df.merge(
            dim_elo[['Year', 'Team_Name', 'Pre_Tournament_Elo', 'World_Rank']],
            left_on=['Year', 'Away Team Name'],
            right_on=['Year', 'Team_Name'],
            how='left'
        )
        df.rename(columns={'Pre_Tournament_Elo': 'Away_Team_Elo', 'World_Rank': 'Away_Team_World_Rank'}, inplace=True)
        df.drop(columns=['Team_Name'], inplace=True)

        df['Elo_Diff'] = (df['Home_Team_Elo'] - df['Away_Team_Elo']).abs().astype(int)
        df['Home_Team_Elo'] = df['Home_Team_Elo'].astype(int)
        df['Away_Team_Elo'] = df['Away_Team_Elo'].astype(int)

        def get_underdog(r):
            if r['Home_Team_Elo'] < r['Away_Team_Elo']:
                return r['Home Team Name']
            elif r['Home_Team_Elo'] > r['Away_Team_Elo']:
                return r['Away Team Name']
            return 'Equal'

        def get_favorite(r):
            if r['Home_Team_Elo'] > r['Away_Team_Elo']:
                return r['Home Team Name']
            elif r['Home_Team_Elo'] < r['Away_Team_Elo']:
                return r['Away Team Name']
            return 'Equal'

        df['Underdog_Team'] = df.apply(get_underdog, axis=1)
        df['Favorite_Team'] = df.apply(get_favorite, axis=1)
        df['Is_Upset'] = (df['Underdog_Team'] != 'Equal') & (df['Winner'] == df['Underdog_Team'])

    # 8. Group Standings & Knockout Matchup Classification
    dim_standings = generate_group_standings(df)
    rank_lookup = dim_standings.set_index(['Year', 'Team_Name'])['Group_Rank'].to_dict()

    df['Home_Group_Rank'] = df.apply(lambda r: rank_lookup.get((r['Year'], r['Home Team Name'])), axis=1)
    df['Away_Group_Rank'] = df.apply(lambda r: rank_lookup.get((r['Year'], r['Away Team Name'])), axis=1)

    def get_matchup_type(r):
        if r['Stage_Group'] == '1. Group Stage':
            return 'Group Stage Match'
        if pd.isna(r['Home_Group_Rank']) or pd.isna(r['Away_Group_Rank']):
            return 'Straight Knockout (No Group Stage)'
        
        if r['Stage_Group'] == '2. Early Knockout':
            ranks = sorted([int(r['Home_Group_Rank']), int(r['Away_Group_Rank'])])
            if ranks == [1, 2]:
                return '1. Winner vs Runner-up (1 vs 2)'
            elif ranks == [1, 3]:
                return '2. Winner vs 3rd Place (1 vs 3 Wildcard)'
            elif ranks == [2, 2]:
                return '3. Runner-up vs Runner-up (2 vs 2)'
            elif ranks == [2, 3]:
                return '4. Runner-up vs 3rd Place (2 vs 3 Wildcard)'
            elif ranks == [1, 1]:
                return '5. Winner vs Winner (1 vs 1)'
            else:
                return f'Early Knockout ({ranks[0]} vs {ranks[1]})'
        else:
            return 'Deep Knockout (Quarter/Semi/Final)'

    df['Matchup_Type'] = df.apply(get_matchup_type, axis=1)
    df['Contains_Third_Placed_Team'] = df['Stage_Group'].isin(['2. Early Knockout', '3. Deep Knockout']) & \
                                       ((df['Home_Group_Rank'] == 3) | (df['Away_Group_Rank'] == 3))
    
    # 9. Dead Rubber Classification for Matchday 3
    s_map, d_map, fd_map, hs_map, as_map = classify_dead_rubbers(df)
    
    df['Match_Stakes'] = df['MatchID'].map(s_map).fillna('Not Applicable (Not Matchday 3)')
    df['Is_Dead_Rubber'] = df['MatchID'].map(d_map).fillna(False).astype(bool)
    df['Is_Full_Dead_Rubber'] = df['MatchID'].map(fd_map).fillna(False).astype(bool)
    df['Home_Pre_Match_Status'] = df['MatchID'].map(hs_map).fillna('Not Applicable')
    df['Away_Pre_Match_Status'] = df['MatchID'].map(as_map).fillna('Not Applicable')
    
    return df

def classify_dead_rubbers(df):
    """
    Classifies all Matchday 3 group stage matches based on mathematical qualification stakes.
    - 1. Both Qualified (Mutual Qualification): Both teams already guaranteed knockout spots.
    - 2. Both Eliminated (Mutual Elimination): Both teams mathematically eliminated.
    - 3. One-sided Dead Rubber: One team's fate is sealed, the other is still fighting for qualification.
    - 4. Decisive / High Stakes: Both teams are actively contending for qualification.
    """
    stakes_map = {}
    is_dead_map = {}
    is_full_dead_map = {}
    h_status_map = {}
    a_status_map = {}
    
    for year in df['Year'].unique():
        tourn = df[df['Year'] == year]
        grp_m = tourn[(tourn['Stage_Group'] == '1. Group Stage') & (tourn['Stage_Detail'] == 'First Group Stage')]
        if len(grp_m) == 0:
            continue
            
        win_pts = 3 if year >= 1994 else 2
        allows_third_place = year in [1986, 1990, 1994, 2026]
        
        md12 = grp_m[grp_m['Matchday'].isin(['Matchday 1', 'Matchday 2'])]
        md3 = grp_m[grp_m['Matchday'] == 'Matchday 3']
        
        stats = {}
        for _, r in md12.iterrows():
            st = r['Stage']
            h, a = r['Home Team Name'], r['Away Team Name']
            hg, ag = int(r['Home Team Goals']), int(r['Away Team Goals'])
            for t in [h, a]:
                if (st, t) not in stats: stats[(st, t)] = {'Pts': 0, 'GF': 0, 'GA': 0}
            stats[(st, h)]['GF'] += hg; stats[(st, h)]['GA'] += ag
            stats[(st, a)]['GF'] += ag; stats[(st, a)]['GA'] += hg
            if hg > ag: stats[(st, h)]['Pts'] += win_pts
            elif hg < ag: stats[(st, a)]['Pts'] += win_pts
            else: stats[(st, h)]['Pts'] += 1; stats[(st, a)]['Pts'] += 1
            
        status = {}
        for stage, grp in grp_m.groupby('Stage'):
            teams = list(set(grp['Home Team Name']) | set(grp['Away Team Name']))
            if len(teams) != 4:
                continue
            t_pts = [(t, stats.get((stage, t), {}).get('Pts', 0)) for t in teams]
            t_pts.sort(key=lambda x: x[1], reverse=True)
            p1, p2, p3, p4 = t_pts[0][1], t_pts[1][1], t_pts[2][1], t_pts[3][1]
            
            for t, p in t_pts:
                if not allows_third_place:
                    if (p >= 2 * win_pts and p3 <= (1 if win_pts == 3 else 0)) or (p > p3 + win_pts):
                        status[(stage, t)] = 'Qualified'
                    elif (p + win_pts < p2) or (p == 0 and p2 >= (4 if win_pts == 3 else 3)):
                        status[(stage, t)] = 'Eliminated'
                    else:
                        status[(stage, t)] = 'Contending'
                else:
                    if (p >= 2 * win_pts and p3 <= (1 if win_pts == 3 else 0)) or (p > p3 + win_pts):
                        status[(stage, t)] = 'Qualified'
                    elif p + win_pts < p3:
                        status[(stage, t)] = 'Eliminated'
                    else:
                        status[(stage, t)] = 'Contending'
                        
        for _, m in md3.iterrows():
            mid = m['MatchID']
            st = m['Stage']
            ht, at = m['Home Team Name'], m['Away Team Name']
            hs = status.get((st, ht), 'Contending')
            as_ = status.get((st, at), 'Contending')
            
            if hs == 'Qualified' and as_ == 'Qualified':
                cat = '1. Both Qualified'
                is_dead = True
                is_full = True
            elif hs == 'Eliminated' and as_ == 'Eliminated':
                cat = '2. Both Eliminated'
                is_dead = True
                is_full = True
            elif (hs in ['Qualified', 'Eliminated']) or (as_ in ['Qualified', 'Eliminated']):
                cat = '3. One-sided Dead Rubber'
                is_dead = True
                is_full = False
            else:
                cat = '4. Decisive / High Stakes'
                is_dead = False
                is_full = False
                
            stakes_map[mid] = cat
            is_dead_map[mid] = is_dead
            is_full_dead_map[mid] = is_full
            h_status_map[mid] = hs
            a_status_map[mid] = as_
            
    return stakes_map, is_dead_map, is_full_dead_map, h_status_map, a_status_map

def generate_group_standings(df):
    group_df = df[(df['Stage_Group'] == '1. Group Stage') & (df['Stage_Detail'] == 'First Group Stage')].copy()

    advanced_teams = set()
    ko_or_next = df[(df['Stage_Group'].isin(['2. Early Knockout', '3. Deep Knockout'])) | (df['Stage_Detail'] == 'Second Group Stage')]
    for _, r in ko_or_next.iterrows():
        advanced_teams.add((r['Year'], r['Home Team Name']))
        advanced_teams.add((r['Year'], r['Away Team Name']))

    standings = []
    for (year, stage), matches in group_df.groupby(['Year', 'Stage']):
        stats = {}
        for _, r in matches.iterrows():
            h, a = r['Home Team Name'], r['Away Team Name']
            hg, ag = int(r['Home Team Goals']), int(r['Away Team Goals'])
            for t in [h, a]:
                if t not in stats: stats[t] = {'Played': 0, 'Won': 0, 'Drawn': 0, 'Lost': 0, 'GF': 0, 'GA': 0, 'Pts': 0}
            stats[h]['Played'] += 1; stats[a]['Played'] += 1
            stats[h]['GF'] += hg; stats[h]['GA'] += ag
            stats[a]['GF'] += ag; stats[a]['GA'] += hg
            if hg > ag:
                stats[h]['Won'] += 1; stats[h]['Pts'] += 3; stats[a]['Lost'] += 1
            elif hg < ag:
                stats[a]['Won'] += 1; stats[a]['Pts'] += 3; stats[h]['Lost'] += 1
            else:
                stats[h]['Drawn'] += 1; stats[h]['Pts'] += 1; stats[a]['Drawn'] += 1; stats[a]['Pts'] += 1
                
        # Official historical tie-breaks for identical H2H & (Pts, GD, GF)
        # 1990 Group F: FIFA Drawing of lots gave Ireland 2nd, Netherlands 3rd
        # 2018 Group H: FIFA Fair Play conduct cards gave Japan 2nd (-4 pts), Senegal 3rd (-6 pts)
        manual_tiebreaks = {
            (1990, 'Group F'): {'Republic of Ireland': 1, 'Netherlands': 0},
            (2018, 'Group H'): {'Japan': 1, 'Senegal': 0}
        }

        def compare_teams(t1, t2):
            s1, s2 = stats[t1], stats[t2]
            # 1. Points
            if s1['Pts'] != s2['Pts']:
                return 1 if s1['Pts'] > s2['Pts'] else -1
            # 2. Goal Difference
            gd1, gd2 = s1['GF'] - s1['GA'], s2['GF'] - s2['GA']
            if gd1 != gd2:
                return 1 if gd1 > gd2 else -1
            # 3. Goals Scored
            if s1['GF'] != s2['GF']:
                return 1 if s1['GF'] > s2['GF'] else -1
                
            # 4. Head-to-Head match between t1 and t2
            m = matches[((matches['Home Team Name'] == t1) & (matches['Away Team Name'] == t2)) |
                        ((matches['Home Team Name'] == t2) & (matches['Away Team Name'] == t1))]
            if len(m) > 0:
                row = m.iloc[0]
                g1 = int(row['Home Team Goals']) if row['Home Team Name'] == t1 else int(row['Away Team Goals'])
                g2 = int(row['Away Team Goals']) if row['Home Team Name'] == t1 else int(row['Home Team Goals'])
                if g1 != g2:
                    return 1 if g1 > g2 else -1
                    
            # 5. Fair Play or Drawing of Lots fallback
            tb = manual_tiebreaks.get((year, stage), {})
            if t1 in tb and t2 in tb:
                return 1 if tb[t1] > tb[t2] else -1
                
            return 0

        sorted_team_names = sorted(stats.keys(), key=cmp_to_key(compare_teams), reverse=True)
        for rank, team in enumerate(sorted_team_names, 1):
            s = stats[team]
            advanced = (year, team) in advanced_teams
            standings.append({
                'Year': year,
                'Stage': stage,
                'Team_Name': team,
                'Played': s['Played'],
                'Won': s['Won'],
                'Drawn': s['Drawn'],
                'Lost': s['Lost'],
                'GF': s['GF'],
                'GA': s['GA'],
                'GD': s['GF'] - s['GA'],
                'Points': s['Pts'],
                'Group_Rank': rank,
                'Advanced_Next_Round': advanced
            })

    return pd.DataFrame(standings)

def generate_dimension_tables(df_master):
    print("3. Generating Dimension Tables...")
    
    # 1. Dim_Tournaments
    tourn_summary = df_master.groupby('Year').agg(
        Host_Country=('Country', 'first'),
        Era_Format=('Era_Format', 'first'),
        MatchesPlayed=('MatchID', 'count'),
        Total_Goals=('Total_Goals', 'sum'),
        Total_Attendance=('Attendance', 'sum'),
        Mean_Attendance=('Attendance', 'mean'),
        Mean_Occupancy_Rate=('Occupancy_Rate', 'mean')
    ).reset_index()
    
    # Add QualifiedTeams
    qual_teams_map = {
        1930: 13, 1934: 16, 1938: 15, 1950: 13, 1954: 16, 1958: 16, 1962: 16,
        1966: 16, 1970: 16, 1974: 16, 1978: 16, 1982: 24, 1986: 24, 1990: 24,
        1994: 24, 1998: 32, 2002: 32, 2006: 32, 2010: 32, 2014: 32, 2018: 32,
        2022: 32, 2026: 48
    }
    tourn_summary['QualifiedTeams'] = tourn_summary['Year'].map(qual_teams_map)
    tourn_summary['Total_Attendance'] = tourn_summary['Total_Attendance'].astype(int)
    tourn_summary['Mean_Attendance'] = tourn_summary['Mean_Attendance'].round(1)
    tourn_summary['Mean_Occupancy_Rate'] = tourn_summary['Mean_Occupancy_Rate'].round(1)
    
    # 2. Dim_Stadiums
    stadiums_df = df_master.groupby('Stadium').agg(
        City=('City', 'first'),
        Host_Country=('Country', 'first'),
        Max_Capacity=('Max_Capacity', 'first'),
        Capacity_Source=('Capacity_Source', 'first'),
        Matches_Hosted=('MatchID', 'count'),
        Record_Attendance=('Attendance', 'max')
    ).reset_index()
    
    # 3. Dim_Confederations
    all_teams = sorted(list(set(df_master['Home Team Name'].unique()) | set(df_master['Away Team Name'].unique())))
    unified_map = {
        'Germany FR': 'Germany',
        'German DR': 'East Germany',
        'Soviet Union': 'Russia',
        'Yugoslavia': 'Serbia',
        'Serbia and Montenegro': 'Serbia',
        'Czechoslovakia': 'Czech Republic',
        'Zaire': 'Congo DR',
        'Dutch East Indies': 'Indonesia',
    }
    confed_df = pd.DataFrame({
        'Team_Name': all_teams,
        'Unified_Team_Name': [unified_map.get(t, t) for t in all_teams],
        'Confederation': [CONFED_MAP.get(t, 'Other') for t in all_teams]
    })
    
    # 4. Dim_Group_Standings
    dim_standings = generate_group_standings(df_master)
    
    # 5. Dim_Qualifiers_Summary
    dim_qualifiers = generate_qualifiers_summary(tourn_summary)
    
    # 6. Dim_Financials
    dim_financials = generate_financials(tourn_summary)
    
    # 7. Dim_Dead_Rubbers (Detail of Matchday 3 matches)
    md3_matches = df_master[df_master['Matchday'] == 'Matchday 3'].copy()
    dim_dead_rubbers = md3_matches[[
        'MatchID', 'Year', 'Era_Format', 'Stage', 'Datetime',
        'Home Team Name', 'Away Team Name',
        'Home_Pre_Match_Status', 'Away_Pre_Match_Status',
        'Match_Stakes', 'Is_Dead_Rubber', 'Is_Full_Dead_Rubber',
        'Home Team Goals', 'Away Team Goals', 'Total_Goals', 'Goal_Margin'
    ]].sort_values(['Year', 'Datetime', 'Stage'])
    
    return tourn_summary, stadiums_df, confed_df, dim_standings, dim_qualifiers, dim_financials, dim_dead_rubbers

def generate_qualifiers_summary(tourn_summary):
    """
    Generates summary of World Cup qualifiers scale (1930 - 2026).
    Source: FIFA Historical Preliminary Competition Archives & Official Tournament Reports.
    """
    qual_data = {
        1930: (13, 0),
        1934: (32, 27),
        1938: (37, 22),
        1950: (34, 26),
        1954: (39, 57),
        1958: (55, 89),
        1962: (56, 92),
        1966: (74, 127),
        1970: (75, 172),
        1974: (99, 226),
        1978: (107, 252),
        1982: (109, 306),
        1986: (121, 308),
        1990: (116, 314),
        1994: (147, 497),
        1998: (174, 643),
        2002: (199, 777),
        2006: (198, 847),
        2010: (204, 853),
        2014: (203, 820),
        2018: (210, 872),
        2022: (206, 865),
        2026: (211, 920),
    }
    
    rows = []
    for _, r in tourn_summary.iterrows():
        y = int(r['Year'])
        teams_qual, matches_qual = qual_data.get(y, (int(r['QualifiedTeams']), 0))
        finals = int(r['QualifiedTeams'])
        rate = round((finals / teams_qual) * 100, 2)
        rows.append({
            'Year': y,
            'Host_Country': r['Host_Country'],
            'Era_Format': r['Era_Format'],
            'Teams_In_Qualifiers': teams_qual,
            'Teams_In_Finals': finals,
            'Matches_In_Qualifiers': matches_qual,
            'Qualification_Rate': rate
        })
    return pd.DataFrame(rows)

def generate_financials(tourn_summary):
    """
    Generates quadrennial FIFA financial cycles, prize money pools, and payouts (1930 - 2026).
    Source: FIFA Financial Reports (1998-2022), FIFA Congress Historical Reports & Archives.
    """
    fin_map = {
        1930: (0.25, 0.0, 0.0, 0.0, 0.0),
        1934: (0.45, 0.0, 0.0, 0.0, 0.0),
        1938: (0.50, 0.0, 0.0, 0.0, 0.0),
        1950: (1.20, 0.0, 0.0, 0.0, 0.0),
        1954: (2.10, 0.0, 0.0, 0.0, 8.5),
        1958: (3.20, 0.0, 0.0, 0.0, 12.0),
        1962: (4.50, 0.0, 0.0, 0.0, 15.0),
        1966: (7.20, 0.0, 0.0, 0.0, 25.0),
        1970: (15.50, 0.0, 0.0, 0.0, 35.0),
        1974: (32.00, 0.0, 0.0, 0.0, 40.0),
        1978: (55.00, 0.0, 0.0, 0.0, 45.0),
        1982: (100.00, 20.0, 1.4, 0.9, 48.0),
        1986: (210.00, 26.0, 2.2, 1.6, 50.0),
        1990: (1050.00, 54.0, 3.5, 2.5, 52.0),
        1994: (1300.00, 71.0, 4.5, 3.0, 54.0),
        1998: (1900.00, 103.0, 6.5, 4.5, 56.0),
        2002: (2300.00, 156.6, 8.5, 6.3, 58.0),
        2006: (3230.00, 266.0, 18.0, 12.0, 60.0),
        2010: (4190.00, 348.0, 30.0, 20.0, 58.0),
        2014: (5720.00, 358.0, 35.0, 24.0, 43.0),
        2018: (6420.00, 400.0, 38.0, 29.0, 48.7),
        2022: (7570.00, 440.0, 42.0, 30.0, 45.3),
        2026: (11000.00, 652.0, 50.0, 35.0, 42.0),
    }
    
    rows = []
    base_1998_rev = 1900.00
    for _, r in tourn_summary.iterrows():
        y = int(r['Year'])
        tot_rev, prize, champ, runner, tv_share = fin_map.get(y, (0.0, 0.0, 0.0, 0.0, 0.0))
        prize_share = round((prize / tot_rev * 100), 2) if tot_rev > 0 and prize > 0 else 0.0
        idx_1998 = round((tot_rev / base_1998_rev * 100), 1)
        rows.append({
            'Year': y,
            'Host_Country': r['Host_Country'],
            'Era_Format': r['Era_Format'],
            'Total_Revenue_USD_M': tot_rev,
            'Prize_Money_USD_M': prize,
            'Champion_Payout_USD_M': champ,
            'Runner_Up_Payout_USD_M': runner,
            'TV_Rights_Share_Pct': tv_share,
            'Prize_Share_Of_Revenue_Pct': prize_share,
            'Revenue_Growth_Index_1998_Base': idx_1998
        })
    return pd.DataFrame(rows)

def main():
    print("=== STARTING ETL PIPELINE ===")
    df_master = load_and_merge_datasets()
    
    # Save the repaired base file
    repaired_path = os.path.join(RAW_DIR, 'WorldCupMatches_with_HostCountry_1930_2026.csv')
    df_master.to_csv(repaired_path, index=False, encoding='utf-8')
    print(f"-> Repaired base CSV saved to: {repaired_path}")
    
    # Feature engineering
    df_engineered = perform_feature_engineering(df_master)
    
    # Save master cleaned dataset
    master_path = os.path.join(PROD_DIR, 'worldcup_master_cleaned.csv')
    df_engineered.to_csv(master_path, index=False, encoding='utf-8')
    print(f"-> Master cleaned dataset saved to: {master_path}")
    
    # Generate Dimension tables
    dim_tourn, dim_stadiums, dim_confed, dim_standings, dim_qualifiers, dim_financials, dim_dead_rubbers = generate_dimension_tables(df_engineered)
    
    dim_tourn_path = os.path.join(PROD_DIR, 'dim_tournaments.csv')
    dim_stadiums_path = os.path.join(PROD_DIR, 'dim_stadiums.csv')
    dim_confed_path = os.path.join(PROD_DIR, 'dim_confederations.csv')
    dim_standings_path = os.path.join(PROD_DIR, 'dim_group_standings.csv')
    dim_qualifiers_path = os.path.join(PROD_DIR, 'dim_qualifiers_summary.csv')
    dim_financials_path = os.path.join(PROD_DIR, 'dim_financials.csv')
    dim_dead_rubbers_path = os.path.join(PROD_DIR, 'dim_dead_rubbers.csv')
    
    dim_tourn.to_csv(dim_tourn_path, index=False, encoding='utf-8')
    dim_stadiums.to_csv(dim_stadiums_path, index=False, encoding='utf-8')
    dim_confed.to_csv(dim_confed_path, index=False, encoding='utf-8')
    dim_standings.to_csv(dim_standings_path, index=False, encoding='utf-8')
    dim_qualifiers.to_csv(dim_qualifiers_path, index=False, encoding='utf-8')
    dim_financials.to_csv(dim_financials_path, index=False, encoding='utf-8')
    dim_dead_rubbers.to_csv(dim_dead_rubbers_path, index=False, encoding='utf-8')
    
    print(f"-> Dim Tournaments saved to: {dim_tourn_path}")
    print(f"-> Dim Stadiums saved to: {dim_stadiums_path}")
    print(f"-> Dim Confederations saved to: {dim_confed_path}")
    print(f"-> Dim Group Standings saved to: {dim_standings_path}")
    print(f"-> Dim Qualifiers Summary saved to: {dim_qualifiers_path}")
    print(f"-> Dim Financials saved to: {dim_financials_path}")
    print(f"-> Dim Dead Rubbers saved to: {dim_dead_rubbers_path}")
    
    print("\n=== ETL PIPELINE COMPLETED SUCCESSFULLY ===")
    print("Summary of Master Cleaned Dataset:")
    print(f"Shape: {df_engineered.shape}")
    print(f"Total Matches: {len(df_engineered)}")
    print(f"Null Attendances: {df_engineered['Attendance'].isna().sum()}")
    print("\nMatches by Era:")
    print(df_engineered['Era_Format'].value_counts())
    print("\nMatches by Stage Group:")
    print(df_engineered['Stage_Group'].value_counts())
    print("\nMatches by Matchday:")
    print(df_engineered['Matchday'].value_counts())

if __name__ == '__main__':
    main()
