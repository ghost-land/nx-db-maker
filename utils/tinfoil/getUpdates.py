import requests
from bs4 import BeautifulSoup
import os
import tempfile

# URL de la page source
url = "https://tinfoil.io/Title/Updates"

# Fonction pour télécharger le contenu HTML et l'enregistrer dans un fichier temporaire
def download_html(url, temp_dir):
    response = requests.get(url)
    if response.status_code == 200:
        temp_file_path = os.path.join(temp_dir, 'updates.html')
        with open(temp_file_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        return temp_file_path
    else:
        print(f"Échec de la récupération des données. Code d'état : {response.status_code}")
        return None

# Fonction pour lire le fichier HTML et extraire les informations nécessaires
def get_updates_info(temp_file_path, output_filename="./db/tinfoilUpdatesDB.txt"):
    with open(temp_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    tbody = soup.find('tbody')

    updates = []
    
    if not tbody:
        print("Erreur : Le tableau des mises à jour n'a pas été trouvé.")
        return
    
    for row in tbody.find_all('tr'):
        title_link = row.find('a')
        if title_link:
            title_id = title_link['href'].split('/')[-1]
            game_name = title_link.text
            version = row.find_all('td')[2].text
            release_date = row.find_all('td')[3].text
            
            updates.append({
                "id": title_id,
                "name": game_name,
                "version": version,
                "release_date": release_date,
            })
    
    return updates

def get_updates():
    print('Gettings tinfoil updates ...')
    # Créer un dossier temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = download_html(url, temp_dir)
        if temp_file_path:
            return get_updates_info(temp_file_path)
        
    return None
    
# Exécution principale
if __name__ == "__main__":
    # Créer un dossier temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = download_html(url, temp_dir)
        if temp_file_path:
            print(get_updates_info(temp_file_path))
