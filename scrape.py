import re
import requests
from bs4 import BeautifulSoup
from urlparse import urljoin
from urlparse import urlparse
from urlparse import parse_qs
import os.path
import pandas as pd
import argparse

base_url = "https://chicagoelections.com/en/"

def check_if_path_exists(path):
  try:
    os.makedirs(path)
  except OSError:
    if not os.path.isdir(path):
      raise

def write_raw_data(data, out_fn):
  check_if_path_exists(os.path.dirname(out_fn))
  with open(out_fn, 'wb') as f:
    f.write(data)

def scrape_elections(link, data_directory):
  full_url = urljoin(base_url, link['href'])
  r = requests.get(full_url)
  soup = BeautifulSoup(r.text, 'html.parser')
  
  election_id = parse_qs(urlparse(link['href']).query)['election'][0]
  election_year = link.text.split()[0]
  election_name = ''.join(link.text.split()[1:3]).strip('-')
  
  races = [(option['value'], option.text.strip()) for option in soup.find(id='race').find_all("option")]
  for race_id, race_name in races:
    payload = {'election': election_id, 'race': race_id, 'ward': None, 'precinct': None}
    race_url = urljoin(base_url, "data-export.asp")
    results = requests.get(race_url, params=payload)

    basename = "{}_{}_{}.xls".format(election_year, election_name, race_name)
    basename = re.sub(r'[\\\/*?:"<>|]', "", basename)  
    out_fn = os.path.join(data_directory, "raw", election_year, basename)
  
    write_raw_data(results.content, out_fn)
    clean_data(out_fn, data_directory)

def clean_data(fn, data_directory):
  dfs = pd.read_html(fn)
  
  processed_dfs = []
  for df in dfs[1:]:
    ward = int(re.search('Ward ([0-9]+)', df.iloc[0,0], flags=re.IGNORECASE).group(1))
    
    cols = df.iloc[1]
    cols = [c.encode('Windows-1252').decode('utf-8').title() for c in cols]
    new_cols = list(cols)
    for i, c in enumerate(cols):
      if c == '%':
        new_cols[i-1] = "votes|" + cols[i-1]
        new_cols[i] = "pct|" + cols[i-1]
    df.columns = new_cols
    
    df.drop(list(df.index[:2]) + [df.index[-1]], inplace=True)

    df = df.applymap(lambda x: x.strip('%'))
    df.Precinct = '{:02}'.format(ward) + df.Precinct.map(lambda x: '{:03}'.format(int(x)))
    processed_dfs.append(df)
  
  basename = os.path.splitext(os.path.basename(fn))[0] + ".tsv"
  election_year = basename.split("_")[0]
  
  out_fn = os.path.join(data_directory, "clean", election_year, basename)
  check_if_path_exists(os.path.dirname(out_fn))
  pd.concat(processed_dfs, ignore_index=True).to_csv(out_fn, sep='\t', index=False, encoding='utf-8')

def main(directory, primaries, generals, runoffs, years):
  election_types = []
  if primaries:
    election_types.append("Primary")
  if generals:
    election_types.extend(["General Election", "Municipal General", "Geeral"])
  if runoffs:
    election_types.append("Municipal Runoffs")
      
  if not years:
    txt_filter = lambda txt: any(e in txt for e in election_types)
  else:
    txt_filter = lambda txt: any(y in txt for y in years) and any(e in txt for e in election_types)

  results_url = urljoin(base_url, "election-results.html")
  r = requests.get(results_url)
  soup = BeautifulSoup(r.text, 'html.parser')
  links = soup.find_all("a", href=re.compile("\?election=[0-9]+"), text=txt_filter)
  
  for link in links:
    data = scrape_elections(link, directory)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-d', '--directory', help="Directory to write data to.")
  parser.add_argument('-p', '--primaries', action='store_true', help="Scrape primary election data.")
  parser.add_argument('-g', '--generals', action='store_true', help="Scrape general election data.")
  parser.add_argument('-r', '--runoffs', action='store_true', help="Scrape runoff election data.")
  parser.add_argument('-y', '--years', nargs='+', help="Scrape data for given years. If none given, scrapes data for all available years.")
  args = parser.parse_args()
  if not (args.primaries or args.generals or args.runoffs):
    parser.error('At least one election type --primaries, --generals --runoffs must be given.')

  main(args.directory, args.primaries, args.generals, args.runoffs, args.years) 