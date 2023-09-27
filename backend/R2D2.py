import json
import pandas as pd 
import sqlite3
import argparse


parser = argparse.ArgumentParser(description='Add the falcon and empire files')

parser.add_argument( '-f', metavar='falcon', type=str)
parser.add_argument( '-e', metavar='empire', type=str)

args = parser.parse_args()
path = args.f.split("/")[0]


# load all usefull data in a pythonic friendly way 
with open(args.f) as mon_fichier:
    millennium_falcon = json.load(mon_fichier)

with open(args.e) as mon_fichier:
    empire = json.load(mon_fichier)

millennium_falcon = pd.DataFrame.from_dict([millennium_falcon], orient='columns')
empire = pd.DataFrame.from_dict(empire, orient='columns')

### create constants
autonomy_super = millennium_falcon.autonomy.iloc[0]
countdown = empire.countdown.iloc[0]

hunters = pd.DataFrame()
for k in range(len(empire.bounty_hunters)):
	hunters = hunters.append(pd.DataFrame([empire.bounty_hunters.iloc[k]]))

# creating file path
dbfile = path+'/universe.db'
# Create a SQL connection to our SQLite database
con = sqlite3.connect(dbfile)
cur = con.cursor()
Universe = pd.read_sql_query('SELECT * FROM routes', con)
con.close()


def compute_proba(n): #number of times crossing the path of a bounty hunters - 1
	if (n==-1): 
		return(0) 
	if (n==0):
		return (1/10)
	else : 
		return(((9**n)/(10**(n+1)))+compute_proba(n-1))


def destinations_from(origin): #get all possible destination from any given origin
	return(Universe.query("origin=='"+str(origin)+"'")[['destination', 'travel_time']])

def get_time(origin, destination): #only_travel_time
	return(Universe.query("origin=='"+str(origin)+"'").query("destination=='"+str(destination)+"'").travel_time.iloc[0])

def routes_calculator(universe=Universe, autonomy_super=autonomy_super):
	routes = [["Tatooine"]]
	i = 0
	 #stops calendar
	arrivals = []
	#stops names
	stops = [] 
	#days of stopping for refuel only
	days_of_stop = [] 
	destinations = destinations_from(routes[i][-1]).destination
	#the most extreme condition (continue untill you can't) to ensure we check any possible course (even with a loop, should it come to that point)
	cond = True
	while cond: 
		try:
			destinations = destinations_from(routes[i][-1]).reset_index().destination
			for k in range (len(destinations)):
				routes = routes + [routes[i] + [destinations[k]]]
			i+=1
		except:
			cond=False
	out = []
	#only keeping endor as final destination
	for c in routes:
		if ('Endor' in c): 
			out = out + [c]
	for p in range(len(out)):
		#time_counter
		time = 0 
		arrivals_loc = [0] 
		autonomy = autonomy_super
		for k in range(len(out[p])-1):
			stops_loc = []
			days_of_stop_loc = []
			t = get_time(out[p][k], out[p][k+1])
			if t > autonomy:
				time+=1
				try: 
					arrivals_loc = arrivals_loc + [arrivals_loc[-1]+t+1]
				except: #first stop
					arrivals_loc = arrivals_loc + [t+1] 
				days_of_stop_loc = [time]
				autonomy = autonomy_super
				stops_loc = stops_loc + [out[p][k]]
			else:
				try: 
					arrivals_loc = arrivals_loc + [arrivals_loc[-1]+t]
				except: #first stop
					arrivals_loc = arrivals_loc + [t] 
			time += t
			autonomy -= t
		arrivals = arrivals + [arrivals_loc]
		stops = stops + [stops_loc] 
		days_of_stop = days_of_stop + [days_of_stop_loc]
	return (out, arrivals, stops, days_of_stop)

def count_crossing_with_hunters(routes, travel_times, stops, days_of_stop, autonomy=autonomy_super, hunters=hunters):
	crossing_with_hunters = []
	for k in range (len(routes)):
		n = 0
		for i in range (len(routes[k])):
			#crossing a planet with bounty hunters
			if (len(hunters.query("planet=='"+str(routes[k][i])+"'").query("day=='"+str(travel_times[k][i])+"'"))>0):
				n+=1
			#staying a day to refuel on a planet  with bounty hunters
			if (len(hunters.query("planet=='"+str(routes[k][i])+"'").query("day=='"+str(travel_times[k][i]+1)+"'"))<len(hunters.query("planet=='"+str(routes[k][i])+"'").query("day=='"+str(travel_times[k][i])+"'")) and ((travel_times[k][-1]+1)<=countdown)):
				n-=1
		for p in range(len(stops[k])): 
			#checking if it is possible to avoid bounty hunters by waiting for a day on a safe planet while staying below the countdown
			if (len(hunters.query("planet=='"+str(stops[k][p])+"'").query("day=='"+str(days_of_stop[k][p])+"'"))>0):
					n+=1
		crossing_with_hunters = crossing_with_hunters+[n]
	return(crossing_with_hunters)

def main():
	routes,travel_times,stops, days_of_stop = routes_calculator()
	crossing_with_hunters = count_crossing_with_hunters(routes, travel_times, stops, days_of_stop)
	out = []
	for p in range(len(crossing_with_hunters)):
		if ((travel_times[p][-1])<=countdown):
			out = out+[compute_proba(crossing_with_hunters[p]-1)]
	if len(out)==0:
		print(0)
	else :
		print((1 - min(out))*100)


main()































