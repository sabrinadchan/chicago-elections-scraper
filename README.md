# chicago-elections-scraper
Python2 script scrapes election results from the [Chicago Board of Elections Results Page](https://chicagoelections.com/en/election-results.html) and processes into a convenient format for analysis.

## Requirements
* Python 2.7
* pandas `pip install pandas`
* Beautiful Soup 4 `pip install BeautifulSoup4`

## Example Use
Scrape results for every race in every election since 2000 (warning: this could take a while)
`python scraper.py -d election_data -p -g -r`

Scrape results for all 2019 municipal runoff races
`python scraper.py -d election_data -r -y 2019`

Scrape results for all races during presidential general elections
`python scraper.py -d election_data -g -y 2000 2004 2008 2012 2016`

## Issues and Caveats
* The BoE only has election results for races as far back as the 2000 presidential primaries.
* Right now, the script can only narrow down election results based on their year and election type (primary, general, or runoff election), so you could possibly end up downloading a lot of data for races you aren't interested in. 

## Future Work
* Allow users to further refine which races they wish to scrape, e.g. by office or by individual race.