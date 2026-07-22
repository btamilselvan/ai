from datetime import date, timedelta
import random
from models import PokerTournament

# Mock Location list to keep casino names realistic
casinos = [
    "The Horshoe, Las Vegas, NV",
    "Wynn Las Vegas, Las Vegas, NV",
    "Seminole Hard Rock, Hollywood, FL",
    "Commerce Casino, Los Angeles, CA",
    "Borgata Hotel & Casino, Atlantic City, NJ",
    "Choctaw Casino Resort, Durant, OK",
    "King's Room at Prime Social, Houston, TX",
    "Live! Casino & Hotel, Philadelphia, PA"
]

# Base structures to randomly generate realistic poker event names
game_types = ["NLH Monster Stack", "NLH Deepstack", "NLH Freezeout", "Pot Limit Omaha", "NLH High Roller", "NLH Mystery Bounty", "Ladies Event", "Seniors Championship", "NLH Main Event"]
series_names = ["WSOP Circuit", "WPT DeepStacks", "Summer Poker Classic", "Lone Star Poker Series", "Signature Series", "Daily Deepstack"]

def generate_mock_tournaments(num_events=100):
    mock_tournaments = []

    # Seed the random number generator so your mock data remains consistent across runs
    random.seed(42)

    # Start generating from May 2026 through August 2026
    base_date = date.today()

    while len(mock_tournaments) < num_events:
        # Distribute events over a 90-day window
        event_date = base_date + timedelta(days=random.randint(0, 90))
        date_str = event_date.strftime("%Y-%m-%d")
        
        # Establish realistic buy-ins and prize pools
        buy_in_val = random.choice([100, 150, 250, 400, 600, 1100, 3500, 10000])
        buy_in = f"${buy_in_val:,}"
        
        # Multipliers for realistic prize pools based on buy-in size
        if buy_in_val <= 250:
            prize_pool = f"${random.choice([10, 15, 25, 50])},000"
        elif buy_in_val <= 1100:
            prize_pool = f"${random.choice([100, 250, 500])},000"
        else:
            prize_pool = f"${random.choice([1, 2, 5, 10])},000,000"
            
        location = random.choice(casinos)
        
        # Generate realistic names
        if buy_in_val >= 3500:
            name = f"🏆 {random.choice(['WPT', 'WSOP'])} Main Event Championship"
        else:
            name = f"{random.choice(series_names)}: {buy_in} {random.choice(game_types)}"
            
        # Standard 1-day events, but championships span 3-5 days
        end_date_obj = event_date + timedelta(days=4 if buy_in_val >= 3500 else 0)
        end_date_str = end_date_obj.strftime("%Y-%m-%d")

        # Appending to array using your exact schema
        mock_tournaments.append(
            PokerTournament(
                name=name,
                start_date=date_str,
                end_date=end_date_str,
                location=location,
                prize_pool=prize_pool,
                buy_in=buy_in
            )
        )

    return mock_tournaments

# mock_tournaments = []

# # Seed the random number generator so your mock data remains consistent across runs
# random.seed(42)

# # Start generating from May 2026 through August 2026
# base_date = datetime(2026, 5, 15)

# for i in range(1, 101):
#     # Distribute events over a 90-day window
#     event_date = base_date + timedelta(days=random.randint(0, 90))
#     date_str = event_date.strftime("%Y-%m-%d")
    
#     # Establish realistic buy-ins and prize pools
#     buy_in_val = random.choice([100, 150, 250, 400, 600, 1100, 3500, 10000])
#     buy_in = f"${buy_in_val:,}"
    
#     # Multipliers for realistic prize pools based on buy-in size
#     if buy_in_val <= 250:
#         prize_pool = f"${random.choice([10, 15, 25, 50])},000"
#     elif buy_in_val <= 1100:
#         prize_pool = f"${random.choice([100, 250, 500])},000"
#     else:
#         prize_pool = f"${random.choice([1, 2, 5, 10])},000,000"
        
#     location = random.choice(casinos)
    
#     # Generate realistic names
#     if buy_in_val >= 3500:
#         name = f"🏆 {random.choice(['WPT', 'WSOP'])} Main Event Championship"
#     else:
#         name = f"{random.choice(series_names)}: {buy_in} {random.choice(game_types)}"
        
#     # Standard 1-day events, but championships span 3-5 days
#     end_date_obj = event_date + timedelta(days=4 if buy_in_val >= 3500 else 0)
#     end_date_str = end_date_obj.strftime("%Y-%m-%d")

#     # Appending to array using your exact schema
#     mock_tournaments.append(
#         PokerTournament(
#             name=name,
#             start_date=date_str,
#             end_date=end_date_str,
#             location=location,
#             prize_pool=prize_pool,
#             buy_in=buy_in
#         )
#     )

# # --- Verification Check ---
# # Print the first 5 generated tournaments to verify structure
# for tournament in mock_tournaments[:5]:
#     print(f"Name: {tournament.name}")
#     print(f"Dates: {tournament.start_date} to {tournament.end_date}")
#     print(f"Location: {tournament.location} | Buy-in: {tournament.buy_in} | Pool: {tournament.prize_pool}")
#     print("-" * 50)

# print(f"Total tournaments successfully generated: {len(mock_tournaments)}")