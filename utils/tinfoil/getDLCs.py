import requests
from bs4 import BeautifulSoup

# URL de la page source
url = "https://tinfoil.io/Title/Dlc"

# Fonction pour récupérer le contenu HTML de l'URL
def fetch_html_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Échec de la récupération des données. Code d'état : {response.status_code}")
        return None

# Fonction pour parser le contenu HTML et écrire les ID de titre et les noms dans un fichier texte
def get_dlcs_info(html_content, filename="./db/tinfoilDlcDB.txt"):
    soup = BeautifulSoup(html_content, 'html.parser')
    tbody = soup.find('tbody')
    
    dlcs = []
    
    for row in tbody.find_all('tr'):
        title_link = row.find('a')
        if title_link:
            title_id = title_link['href'].split('/')[-1]
            game_name = title_link.text
            publisher = row.find_all('td')[1].text
            size = row.find_all('td')[2].text
            release_date = row.find_all('td')[3].text
            
            dlcs.append({
                "id": title_id,
                "name": game_name,
                "release_date": release_date,
                "publisher": publisher,
                "size": size,
            })
    
    return dlcs

def get_dlcs():
    print('Gettings tinfoil DLCs ...')
    html_content = fetch_html_content(url)
    if html_content:
        return get_dlcs_info(html_content)
    
    return None
    
# Tests 
if __name__ == "__main__":
    html_content = fetch_html_content(url)
    if html_content:
        print(get_dlcs_info(html_content))