import requests
import sqlite3
import re
import json
from bs4 import BeautifulSoup

from utils import tinfoil

config = json.load(open("config.json"))
games_source = config['games-source']

def get_dlc_base_tid(game_id, c):
    base_game_start = game_id[:-4]
    base_game_id = c.execute("SELECT id FROM games WHERE id LIKE ? LIMIT 1", (base_game_start + "%",)).fetchone()
    if base_game_id:
        return base_game_id[0]
    else:
        return None
    
    
def update_download_links():
    def get_game_id(game_title):
        # Find all substrings between [ and ]
        substrings = re.findall(r'\[(.*?)\]', game_title)
        
        # If neither found
        game_id = title.replace(']+',']').replace(']]',']').split("[")[1].split("][v")[0][:-1].replace(')','')

        # Search for the first 16-character long substring (game id)
        for substring in substrings:
            if len(substring) == 16:
                game_id = substring
        
        # If no 16-character substring found, search for the first 33-character long substring
        for substring in substrings:
            if len(substring) == 33:
                game_id = substring
        
        if 'DLC' in title.upper():
            if len(game_id) != 16:
                # wrong game_id
                
                game_title = re.split(r"\[", game_title, 1)[0].strip()
                
                c.execute("SELECT id FROM games WHERE name = ?", (game_title,))
                game_ids = c.fetchone()
                if game_ids:
                    game_id = game_ids[0]

        return game_id
    
    def get_update_version(game_title):
        # List of patterns to match the substring
        patterns = [
            re.compile(r'\]\[v(.*?)\]'),
            re.compile(r'\]\[v(.*?)\.'),
            re.compile(r'\+\[v(.*?)\]'),
            re.compile(r'\+\[v(.*?)\.')
        ]
        
        # Iterate over each pattern and return the first match found
        for pattern in patterns:
            match = pattern.search(game_title)
            if match:
                return match.group(1)
        
        # If no pattern matches, return None
        return None
    
    def get_file_format(title):
        # Find the file extension in the title
        return title.split('.')[-1].upper()

    print('Gettings ghost eshop titles, updates and dlcs ...')
    
    url = games_source['url']
    auth = (games_source['user'], games_source['pass'])
    response = requests.get(url, auth=auth)
    soup = BeautifulSoup(response.content, "html.parser")
    
    conn = sqlite3.connect(config['db-name'])
    c = conn.cursor()
    
    for link in soup.find_all("a"):
        href = link.get("href")
        title = link.text.strip()
        if "[" in title:
            game_id = get_game_id(title)
            game_file_format = get_file_format(title)
            
            is_dlc = c.execute("SELECT id FROM dlcs WHERE id = ?", (game_id,)).fetchone() is not None            
            
            # DLCs
            if is_dlc:
                base_game_id = get_dlc_base_tid(game_id, c)
                c.execute(
                    "INSERT OR REPLACE INTO dlcs (id, base_game_id, name, size, format, download_url) VALUES (?, ?, ?, ?, ?, ?)",
                    (game_id, base_game_id, title, None, game_file_format, url + href),
                )
                    
            # base game
            elif '[v0]' in title or '+[v' in title or '[v' not in title or ('v0]' not in title and '.nsp' not in title.lower()):
                if len(game_id) > 16:
                    print(game_id)
                if not c.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone():
                    c.execute(
                        "INSERT INTO games (id, name, version, format, download_url) VALUES (?, ?, ?, ?, ?)",
                        (game_id, title, get_update_version(title), game_file_format, url + href),
                    )
                else:
                    c.execute(
                        "UPDATE games SET download_url = ? WHERE id = ?",
                        (url + href, game_id),
                    )
                    c.execute(
                        "UPDATE games SET format = ? WHERE id = ?",
                        (game_file_format, game_id),
                    )
                    
                # Update game default version
                if '+[v' in title:
                    c.execute(
                        "UPDATE games SET version = ? WHERE id = ?",
                        (get_update_version(title), game_id),
                    )
                    
            # Updates
            else:
                update_version = get_update_version(title)
                    
                if len(game_id) > 16:
                    print(game_id)
                    
                c.execute(
                    "INSERT OR REPLACE INTO updates (id, name, version, size, format, download_url) VALUES (?, ?, ?, ?, ?, ?)",
                    (game_id, title, update_version, None, game_file_format, url + href),
                )
    
    
    conn.commit()
    conn.close()
            
    return



def build_db():
    conn = sqlite3.connect(config['db-name'])
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            name TEXT,
            version TEXT,
            icon_url TEXT,
            release_date TEXT,
            publisher TEXT,
            size TEXT,
            format TEXT,
            is_demo INTEGER,
            user_rating REAL,
            download_url TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS updates (
            id TEXT PRIMARY KEY,
            name TEXT,
            version TEXT,
            release_date TEXT,
            size TEXT,
            format TEXT,
            download_url TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dlcs (
            id TEXT PRIMARY KEY,
            base_game_id TEXT,
            name TEXT,
            release_date TEXT,
            publisher TEXT,
            size TEXT,
            format TEXT,
            download_url TEXT
        )
    ''')
    
    saved_titles_ids = [row[0] for row in c.execute("SELECT id FROM games")]
    new_titles_ids = []
    saved_updates_ids = [row[0] for row in c.execute("SELECT id FROM updates")]
    new_updates_ids = []
    saved_dlcs_ids = [row[0] for row in c.execute("SELECT id FROM dlcs")]
    new_dlcs_ids = []
    
    for game in tinfoil.get_titles():
        id = game['id']
        name = game['name'].replace(f'<a href=\"/Title/{id}\">','').replace('</a>','')
        version = None
        icon_url = game['icon']
        release_date = game['release_date']
        publisher = game['publisher']
        size = game['size']
        format = None
        is_demo = 'DEMO' in name.upper()
        user_rating = game['user_rating']
        download_url = None
        
        if id not in saved_titles_ids and id not in new_titles_ids:
            new_titles_ids.append(id)
            c.execute(
                "INSERT OR REPLACE INTO games (id, name, version, icon_url, release_date, publisher, size, format, is_demo, user_rating, download_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (id, name, version, icon_url, release_date, publisher, size, format, is_demo, user_rating, download_url)
            )
            
    for game in tinfoil.get_updates():
        id = game['id']
        name = game['name']
        version = game['version']
        release_date = game['release_date']
        
        if id not in saved_updates_ids and id not in new_updates_ids:
            new_updates_ids.append(id)
            c.execute(
                "INSERT OR REPLACE INTO updates (id, name, version, release_date) VALUES (?, ?, ?, ?)",
                (id, name, version, release_date)
            )
            
    for game in tinfoil.get_dlcs():
        id = game['id']
        base_game_id = get_dlc_base_tid(id, c)
        # print('dlc to base tid: ', id, '->', base_game_id)
        name = game['name']
        release_date = game['release_date']
        publisher = game['publisher']
        size = game['size']
        
        if id not in saved_dlcs_ids and id not in new_dlcs_ids:
            new_dlcs_ids.append(id)
            c.execute(
                "INSERT OR REPLACE INTO dlcs (id, base_game_id, name, release_date, publisher, size) VALUES (?, ?, ?, ?, ?, ?)",
                (id, base_game_id, name, release_date, publisher, size)
            )
    
    conn.commit()
    conn.close()
    
    update_download_links()


if __name__ == '__main__':
    build_db()