import folium
import requests
from folium.plugins import MarkerCluster
from datetime import datetime

# Get real-time earthquake data from USGS (past day)
url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

response = requests.get(url)
data = response.json()
#print(data)

# create map centered on the world 
map = folium.Map(location=[48.291697, 17.755778], zoom_start=5, tiles="CartoDB positron")


# adding marker cluster
marker_cluster = MarkerCluster().add_to(map)
# looping trough earthquakes
for feature in data['features']:
    cords = feature['geometry']['coordinates'] #[long, lat, depth]
    props = feature['properties']

    magnitude = props['mag']
    place = props['place']
    time = datetime.utcfromtimestamp(props['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
    depth = cords[2]

    popup_text = f"""
    <b>Location:</b> {place}<br>
    <b>Magnitude:</b> {magnitude}<br>
    <b>Depth:</b> {depth} km<br>
    <b>Time:</b> {time}
    """
    color = 'red' if magnitude >= 5 else 'orange' if magnitude >= 3 else 'green'

    folium.CircleMarker(
        location=[cords[1], cords[0]],
        radius=max(magnitude * 2, 3),
        popup=popup_text,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7
    ).add_to(marker_cluster)

# Save to HTML
map.save("earthquake_map.html")
print("Map saved as 'earthquake_map.html'")