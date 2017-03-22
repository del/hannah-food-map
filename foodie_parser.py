import configparser
import jinja2
import json
import os.path
import re
import urllib.parse
import urllib.request

### CONFIG SECTION ###

# Input and output filenames
ifname   = 'foodie_scraped.json'
ofname   = 'foodie_parsed.json'
tmplname = 'map_template.html'
htmlname = 'map.html'

# Google Maps API config, key is read from config file
config   = configparser.ConfigParser()
config.read('foodie.ini')
api_key  = config["google"]["api_key"]
goog_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='



### SCRIPT ###

# trim away entries and section headers
def row_filter(row):
    section_headers = set([
        'Breakfast / Brunch',
        'Breakfast/Brunch',
        'Lunch / Dinner',
        'Lunch/Dinner',
        'Mexican / South american / Middle eastern',
        'Mexican/South american/Middle eastern',
        'Guide Michelin',
        'Sushi',
        'Asian',
        'Hamburgers',
        'Pizza',
        'Indian',
        'Italian',
        'Raw food / healthy',
        'Raw food/healthy',
        'Coffee / ice cream places',
        'Coffee/ice cream places',
        'Bars'
    ])
    if row['venue'] == '':
        return False
    elif row['comment'] == '' and row['venue'] in section_headers:
        return False
    else:
        return True


# read output data if it already exists
if os.path.exists(ofname):
    with open(ofname) as outfile:
        oldrows = json.load(outfile)
else:
    oldrows = []

# read data from web crawler
with open(ifname) as infile:
    inrows = [r for r in json.load(infile) if row_filter(r)]

# find new rows and update descriptions/visited status
existing_venues = {}
for i, r in enumerate(oldrows):
    existing_venues[r['venue']] = i

rows = []
for row in inrows:
    if row['venue'] not in existing_venues:
        rows.append(row)
    else:
        # Updating is a little tricky, some venues occur multiple
        # times in the list, with different comments. We pick the last
        # non-empty comment, and we also pick visited: true if it is anywhere.
        updrow = oldrows[existing_venues[row['venue']]]
        if row['comment'] != "":
            updrow['comment'] = row['comment']
        if not updrow['visited']:
            updrow['visited'] = row['visited']
        rows.append(updrow)


# download addresses from google maps
it = 0
for row in rows:
    it += 1
    if it % 15 == 0:
        with open(ofname, 'wt') as outfile:
            json.dump(rows, outfile, indent=2)

    if 'google' in row and row['google']: # already done
        continue

    if 'goog_venue' in row:
        address = row['goog_venue']
    else:
        address = row['venue']
    address = "{}, Stockholm, Sweden".format(address)

    print("Fetching address for {}".format(address))

    url_data = urllib.parse.urlencode({'address': address, "key": api_key})
    req_url = "{}{}".format(goog_url, url_data)
    with urllib.request.urlopen(req_url) as res:
        goog_res = json.load(res)
        if goog_res['status'] == 'OK':
            row['google'] = goog_res['results'][0]
        else:
            row['google'] = {}
            print("ERROR: No address for {}, {}".format(row['venue'], row['comment']))


# Write parsed rows to file
with open(ofname, 'wt') as outfile:
    json.dump(rows, outfile, indent=2)


# Also create HTML page
env = jinja2.Environment(
    loader     = jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))),
    autoescape = False
)

# We don't want all the google data in the HTML, only the coordinates and formatted address
maprows = []
for row in rows:
    if 'google' in row and 'formatted_address' in row['google'] and 'geometry' in row['google']:
        newgoogle = {
            'formatted_address': row['google']['formatted_address'],
            'geometry': {
                'location': row['google']['geometry']['location']
               }
           }
        row['google'] = newgoogle


with open(htmlname, 'wt') as outfile:
    template = env.get_template(tmplname)
    outfile.write(template.render(
        venues  = json.dumps(rows),
        api_key = api_key
    ))
