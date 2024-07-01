from functools import cache
import requests

# Function to fetch JSON data from the URL
def fetch_json_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

regions = [
    'br', 'mx', 'us', 'pl', 'cz', 'au', 'se', 'nz', 'no', 'at',
    'be', 'bg', 'cy', 'de', 'ee', 'es', 'fi', 'fr', 'gr', 'hr',
    'hu', 'ie', 'it', 'lt', 'lu', 'lv', 'mt', 'nl', 'pt', 'ro',
    'si', 'sk', 'dk', 'ca', 'za', 'gb', 'jp', 'kr', 'ch', ''
]

@cache
def get_exclusives():
    global regions
    
    regions = ['?region=' + region for region in regions]
    regions.append('')

    results = {}
    all_titles = []
    ids_list = []

    for region in regions:
        url = f"https://tinfoil.media/Title/ApiJson/{region}"
        result = fetch_json_data(url)
        if result:
            results[region.replace('?region=', '')] = result['data']
            ids_list.append([])
            print(region.replace('?region=', ''), len(result['data']))
            for game in result['data']:
                ids_list[-1].append(game['id'])

    exclusive_counts = []
    for i in range(len(ids_list)):
        exclusive_count = len(set(ids_list[i]) - set().union(*[ids for j, ids in enumerate(ids_list) if j != i]))
        exclusive_counts.append(exclusive_count)
        print(f"Exclusive games count for {regions[i]}: {exclusive_count}")

    exclusives = [region.replace('?region=', '') for region, count in zip(regions, exclusive_counts) if count > 0]

    ids_list = []
    for region in exclusives:
        print(f"Getting {region} titles ...")
        for game in results[region]:
            if game['id'] not in ids_list:
                ids_list.append(game['id'])
                all_titles.append(game)
    
    print("done")
    
    return exclusives, all_titles

def get_titles():
    print('Gettings tinfoil titles ...')
    return get_exclusives()[1]


# Tests
if __name__ == '__main__':
    print(get_exclusives())