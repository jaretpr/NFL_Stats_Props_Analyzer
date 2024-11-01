import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import requests
import pandas as pd
import datetime
import threading

# Set the appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Initialize the main window
app = ctk.CTk()
app.title("NFL Stats and Props Downloader")
app.geometry("600x680")  # Increased height to accommodate notes

# Variables for week and year
week_var = tk.StringVar()
year_var = tk.StringVar()

# Set default values for week and year
current_year = datetime.datetime.now().year
year_var.set(str(current_year))
week_var.set('1')  # Default to week 1

# Week input
week_label = ctk.CTkLabel(app, text="Week:")
week_label.pack(pady=(20, 0))
week_entry = ctk.CTkEntry(app, textvariable=week_var)
week_entry.pack(pady=(0, 20))

# Year input
year_label = ctk.CTkLabel(app, text="Year:")
year_label.pack()
year_entry = ctk.CTkEntry(app, textvariable=year_var)
year_entry.pack(pady=(0, 20))

# Function to display player stats (from your original code)
def display_player_stats(category, athlete_name, stats):
    # Define labels for each category
    labels = {
        "passing": ["Completions/Attempts", "Passing Yards", "Yards per Attempt", "Passing TDs", "Interceptions", "Sacks-Yards Lost", "QBR", "Passer Rating"],
        "rushing": ["Attempts", "Rushing Yards", "Yards per Carry", "Rushing TDs", "Longest Run"],
        "receiving": ["Receptions", "Receiving Yards", "Yards per Reception", "Receiving TDs", "Longest Reception", "Targets"],
        "fumbles": ["Fumbles", "Fumbles Lost", "Fumbles Recovered"],
        "defensive": ["Total Tackles", "Solo Tackles", "Sacks", "Tackles for Loss", "Passes Defended", "Interceptions", "Defensive TDs"],
        "interceptions": ["Interceptions", "Return Yards", "Return TDs"],
        "kickReturns": ["Returns", "Yards", "Avg Yards/Return", "Longest Return", "Return TDs"],
        "puntReturns": ["Returns", "Yards", "Avg Yards/Return", "Longest Return", "Return TDs"],
        "kicking": ["FG Made/Attempted", "FG%", "Longest FG", "XP Made/Attempted", "Total Points"],
        "punting": ["Punts", "Yards", "Avg Yards/Punt", "Inside 20", "Longest Punt"],
    }

    # Zip labels with stats to create a dictionary
    return {label: stat for label, stat in zip(labels.get(category, []), stats)}

# Function to download NFL stats
def download_nfl_stats():
    try:
        week = int(week_var.get())
        year = int(year_var.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Week and Year must be integers.")
        return

    # Start a new thread for the long-running task
    threading.Thread(target=download_nfl_stats_thread, args=(year, week), daemon=True).start()

def download_nfl_stats_thread(year, week):
    seasontype = 2  # Regular season
    try:
        # Call the function to get NFL stats
        get_nfl_week_stats(year, week, seasontype)
        # Since we are in a thread, we need to use app.after() to update the GUI
        app.after(0, lambda: messagebox.showinfo("Success", f"NFL Week {week} Stats downloaded successfully."))
    except Exception as e:
        app.after(0, lambda: messagebox.showerror("Error", f"An error occurred while downloading NFL stats: {e}"))

def get_nfl_week_stats(year, week, seasontype=2):
    import requests
    import pandas as pd

    # Initialize list to hold all player data
    all_player_stats = []

    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&seasontype={seasontype}&week={week}"
    response = requests.get(url)

    if response.status_code == 200:
        games = response.json().get('events', [])
        
        for game in games:
            game_id = game['id']
            competitors = game['competitions'][0]['competitors']
            home_team_info = [team for team in competitors if team['homeAway'] == 'home'][0]
            away_team_info = [team for team in competitors if team['homeAway'] == 'away'][0]
            home_team = home_team_info['team']['shortDisplayName']
            away_team = away_team_info['team']['shortDisplayName']
            home_score = home_team_info.get('score', 0)
            away_score = away_team_info.get('score', 0)
            
            # Retrieve detailed summary for each game
            summary_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
            summary_response = requests.get(summary_url)
            
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                
                # Process each team in the game
                for team in summary_data.get('boxscore', {}).get('players', []):
                    team_name = team['team']['displayName']
                    
                    # Iterate over each player
                    for player in team.get('statistics', []):
                        category_name = player['name']
                        
                        for athlete in player.get('athletes', []):
                            athlete_name = athlete['athlete']['displayName']
                            stats = athlete.get('stats', [])
                            stats_data = display_player_stats(category_name, athlete_name, stats)

                            # Append player data to the list
                            player_data = {
                                "Game": f"{home_team} vs {away_team}",
                                "Team": team_name,
                                "Category": category_name,
                                "Player": athlete_name,
                                "Home Team Score": home_score,
                                "Away Team Score": away_score,
                            }
                            player_data.update(stats_data)  # Add stats
                            all_player_stats.append(player_data)

            else:
                print(f"Failed to retrieve summary for game ID {game_id}")
    
    else:
        print("Failed to retrieve data:", response.status_code)
        raise Exception(f"Failed to retrieve data: {response.status_code}")

    # Convert the list of dictionaries to a DataFrame and save to Excel
    df = pd.DataFrame(all_player_stats)
    filename = f"NFL_Week_{week}_Player_Stats.xlsx"
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Player Stats", index=False)

        # Format Excel columns and header
        workbook = writer.book
        worksheet = writer.sheets["Player Stats"]
        worksheet.set_column("A:A", 20)  # Game column
        worksheet.set_column("B:B", 15)  # Team column
        worksheet.set_column("C:C", 15)  # Category column
        worksheet.set_column("D:D", 20)  # Player column
        worksheet.set_column("E:E", 18)  # Home Team Score column
        worksheet.set_column("F:F", 18)  # Away Team Score column
        worksheet.set_column("G:Z", 15)  # Stat columns

        # Define header format with light green color
        header_format = workbook.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "top",
            "fg_color": "#D7E4BC",
            "border": 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

    print(f"Data saved to {filename}")

# Function to download NFL player props
def download_nfl_props():
    try:
        week = int(week_var.get())
        year = int(year_var.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Week and Year must be integers.")
        return

    threading.Thread(target=download_nfl_props_thread, args=(week, year), daemon=True).start()

def download_nfl_props_thread(week, year):
    try:
        api_key = "YOUR_API_KEY_HERE"  # Replace with your actual API key
        events = get_nfl_events(api_key)
        if events:
            all_props = []
            for event in events:
                event_id = event['id']
                event_props = get_nfl_player_props(api_key, event_id)
                if event_props:
                    all_props.extend(event_props)
            if all_props:
                save_props_to_excel(all_props)
                app.after(0, lambda: messagebox.showinfo("Success", "NFL Player Props downloaded successfully."))
            else:
                app.after(0, lambda: messagebox.showwarning("No Data", "No player props data available."))
        else:
            app.after(0, lambda: messagebox.showwarning("No Data", "No events data available."))
    except Exception as e:
        app.after(0, lambda: messagebox.showerror("Error", f"An error occurred while downloading NFL player props: {e}"))

def get_nfl_events(api_key):
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events/"
    params = {"apiKey": api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch events: {response.status_code}, {response.text}")
        return None

def get_nfl_player_props(api_key, event_id):
    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events/{event_id}/odds/"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "player_pass_tds,player_rush_yds,player_receptions,player_reception_yds,player_reception_longest,player_pass_attempts,player_pass_completions,player_pass_interceptions,player_rush_attempts,player_rush_longest",  # Updated market names
        "oddsFormat": "american"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        odds_data = response.json()
        all_props = []
        for bookmaker in odds_data.get('bookmakers', []):
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    player_name = outcome.get('description', 'N/A')
                    prop_name = outcome['name']
                    line = outcome.get('point', 'N/A')
                    odds = outcome['price']
                    all_props.append({
                        "Event": f"{odds_data.get('home_team', 'N/A')} vs {odds_data.get('away_team', 'N/A')}",
                        "Bookmaker": bookmaker['title'],
                        "Market": market['key'],
                        "Player": player_name,
                        "Prop": prop_name,
                        "Line": line,
                        "Odds": odds
                    })
        return all_props
    else:
        print(f"Failed to fetch player props: {response.status_code}, {response.text}")
        return None

def save_props_to_excel(data, filename="NFL_Player_Props.xlsx"):
    df = pd.DataFrame(data)
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Player Props", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Player Props"]

        # Set column widths and formatting
        worksheet.set_column("A:A", 30)  # Event column
        worksheet.set_column("B:B", 20)  # Bookmaker column
        worksheet.set_column("C:C", 20)  # Market column
        worksheet.set_column("D:D", 30)  # Player column
        worksheet.set_column("E:E", 15)  # Prop column
        worksheet.set_column("F:F", 10)  # Line column
        worksheet.set_column("G:G", 10)  # Odds column
        
        # Header format
        header_format = workbook.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "top",
            "fg_color": "#D7E4BC",
            "border": 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

    print(f"Data saved to {filename}")

# Function to compare stats and props
def compare_stats_and_props():
    try:
        week = int(week_var.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Week must be an integer.")
        return

    threading.Thread(target=compare_stats_and_props_thread, args=(week,), daemon=True).start()

def compare_stats_and_props_thread(week):
    stats_file = f"NFL_Week_{week}_Player_Stats.xlsx"
    props_file = "NFL_Player_Props.xlsx"
    try:
        compare_props_and_stats(props_file, stats_file)
        app.after(0, lambda: messagebox.showinfo("Success", "Comparison completed successfully."))
    except Exception as e:
        app.after(0, lambda: messagebox.showerror("Error", f"An error occurred during comparison: {e}"))

def compare_props_and_stats(props_file, stats_file):
    # Load the player props and player stats data
    props_data = pd.read_excel(props_file)
    stats_data = pd.read_excel(stats_file)

    # Updated mapping with alternative terms for each prop type
    stat_mapping = {
        "player_pass_tds": "Passing TDs",
        "player_pass_attempts": "Passing Attempts",
        "player_pass_completions": "Passing Completions",
        "player_pass_interceptions": "Interceptions",
        "player_rush_yds": "Rushing Yards",
        "player_rush_attempts": "Rushing Attempts",
        "player_rush_longest": "Longest Rush",
        "player_receptions": "Receptions",
        "player_reception_yds": "Receiving Yards",
        "player_reception_longest": "Longest Reception"
    }

    comparison_results = []

    for _, prop_row in props_data.iterrows():
        event = prop_row['Event']
        player = prop_row['Player']
        market = prop_row['Market']
        prop_type = market  # Using the market as the prop type
        line = prop_row['Line']
        odds = prop_row['Odds']

        # Check if the prop type exists in the mapping
        stat_column = stat_mapping.get(prop_type)
        if not stat_column:
            print(f"No matching stat type for prop: {prop_type}")
            continue

        # Find matching player in the stats data
        player_stats = stats_data[stats_data['Player'] == player]

        # Skip if no matching player found
        if player_stats.empty:
            print(f"No matching stats found for player: {player}")
            continue

        # Retrieve the actual stat for the player based on the mapped column
        actual_stat = player_stats[stat_column].values[0] if stat_column in player_stats.columns else None

        # Compare stats and determine if over/under hit
        if actual_stat is not None and pd.notnull(actual_stat) and pd.notnull(line):
            try:
                actual_stat_value = float(actual_stat)
                line_value = float(line)
            except ValueError:
                actual_stat_value = None
                line_value = None

            if actual_stat_value is not None and line_value is not None:
                if actual_stat_value > line_value:
                    result = 'Over'
                elif actual_stat_value < line_value:
                    result = 'Under'
                else:
                    result = 'Push'

                comparison_results.append({
                    'Event': event,
                    'Player': player,
                    'Prop Type': prop_type,
                    'Line': line_value,
                    'Actual Stat': actual_stat_value,
                    'Result': result,
                    'Odds': odds
                })
            else:
                comparison_results.append({
                    'Event': event,
                    'Player': player,
                    'Prop Type': prop_type,
                    'Line': line,
                    'Actual Stat': actual_stat,
                    'Result': 'No Data',
                    'Odds': odds
                })
        else:
            # For missing stats, assume 'No Data'
            comparison_results.append({
                'Event': event,
                'Player': player,
                'Prop Type': prop_type,
                'Line': line,
                'Actual Stat': actual_stat,
                'Result': 'No Data',
                'Odds': odds
            })
    
    # Create DataFrame for the comparison results
    comparison_df = pd.DataFrame(comparison_results)

    # Calculate totals for 'Over' and 'Under'
    total_over = comparison_df['Result'].value_counts().get('Over', 0)
    total_under = comparison_df['Result'].value_counts().get('Under', 0)
    total_results = total_over + total_under

    # Calculate percentages
    if total_results > 0:
        over_percentage = total_over / total_results
        under_percentage = total_under / total_results
    else:
        over_percentage = 0
        under_percentage = 0

    # Create totals rows
    totals_over_row = {
        'Event': 'Totals',
        'Player': '',
        'Prop Type': '',
        'Line': '',
        'Actual Stat': '',
        'Result': f'{total_over}/{total_results}, {over_percentage:.2%} Over',
        'Odds': ''
    }
    totals_under_row = {
        'Event': 'Totals',
        'Player': '',
        'Prop Type': '',
        'Line': '',
        'Actual Stat': '',
        'Result': f'{total_under}/{total_results}, {under_percentage:.2%} Under',
        'Odds': ''
    }

    # Append totals rows to the dataframe
    comparison_df = pd.concat([comparison_df, pd.DataFrame([totals_over_row, totals_under_row])], ignore_index=True)

    # Save to Excel
    filename = f"Player_Props_Comparison_Week_{week_var.get()}.xlsx"
    save_comparison_to_excel(comparison_df, filename)
    print(f"Comparison saved to {filename}")

def save_comparison_to_excel(dataframe, filename):
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Comparison")
        workbook = writer.book
        worksheet = writer.sheets["Comparison"]

        # Formatting for headers
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        for col_num, value in enumerate(dataframe.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Adjust column widths
        for i, col in enumerate(dataframe.columns):
            column_len = max(dataframe[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)

        # Apply conditional formatting to 'Result' column
        over_format = workbook.add_format({'bg_color': '#C6EFCE'})  # Light green
        under_format = workbook.add_format({'bg_color': '#FFC7CE'})  # Light red

        # Find the index of the 'Result' column
        result_col_index = dataframe.columns.get_loc('Result')

        # Apply conditional formatting
        worksheet.conditional_format(1, result_col_index, len(dataframe), result_col_index, {
            'type': 'text',
            'criteria': 'containing',
            'value': 'Over',
            'format': over_format
        })
        worksheet.conditional_format(1, result_col_index, len(dataframe), result_col_index, {
            'type': 'text',
            'criteria': 'containing',
            'value': 'Under',
            'format': under_format
        })

        # Add a blank row before totals
        blank_row_index = len(dataframe) + 1
        worksheet.write_blank(blank_row_index, 0, None)

        # Format the totals rows specifically
        totals_row_format = workbook.add_format({'bold': True})
        worksheet.set_row(blank_row_index + 1, None, totals_row_format)
        worksheet.set_row(blank_row_index + 2, None, totals_row_format)

    print(f"Data saved to {filename}")

# Buttons and their notes
# Download NFL Stats Excel Button and Note
stats_button = ctk.CTkButton(app, text="Download NFL Stats Excel", command=download_nfl_stats)
stats_button.pack(pady=(20, 5))
stats_note = ctk.CTkLabel(app, text="Consists of last played week back multiple years.")
stats_note.pack(pady=(0, 10))

# Download NFL Player Props Excel Button and Note
props_button = ctk.CTkButton(app, text="Download NFL Player Props Excel", command=download_nfl_props)
props_button.pack(pady=(10, 5))
props_note = ctk.CTkLabel(app, text="Only able to download the current week's available props.")
props_note.pack(pady=(0, 10))

# Compare Stats and Props Button and Note
compare_button = ctk.CTkButton(app, text="Compare Stats and Props", command=compare_stats_and_props)
compare_button.pack(pady=(10, 5))
compare_note = ctk.CTkLabel(app, text="Some overs/unders may state no data.")
compare_note.pack(pady=(0, 10))

# Instructions for using the app
how_to_use_text = """\
How to Use:

1. Download Player Props: Before the game starts, download the NFL Player Props Excel file for the matchup you want to analyze. Note: If you can match the layout of the Excel sheet and have past NFL player prop lines, you can import those to compare stats for any previous week.

2. Download Player Stats: After the games have ended, enter the relevant week number and year, then click "Download NFL Stats Excel." This will pull in the statistics for players from that week.

3. Compare Stats and Props: Once both files are downloaded, select "Compare Stats and Props" to view how player performances aligned with the props.
"""

how_to_use_label = ctk.CTkLabel(app, text=how_to_use_text, justify="left", wraplength=500)
how_to_use_label.pack(pady=(20, 10), side="bottom")

# Start the main event loop
app.mainloop()
