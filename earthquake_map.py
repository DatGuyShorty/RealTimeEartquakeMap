import folium
import requests
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from folium.plugins import MiniMap
from folium.plugins import Fullscreen
from datetime import datetime

# Get real-time earthquake data from USGS (past day)
url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"

response = requests.get(url)
data = response.json()
#print(data)

# create map
map = folium.Map(location=[48.291697, 17.755778], zoom_start=5, tiles="CartoDB positron")

# adding marker cluster
marker_cluster = MarkerCluster(name="Earthquake Marker Cluster")
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

# Prepare the heatmap data: [lat, lon, weight (magnitude)]
heat_data = []

for feature in data["features"]:
    coords = feature["geometry"]["coordinates"]  # [lon, lat, depth]
    magnitude = feature["properties"]["mag"] or 0
    lat, lon = coords[1], coords[0]
    
    # Add point: stronger quakes have more "heat"
    heat_data.append([lat, lon, magnitude])
#Create heatmap layer
heat_map = HeatMap(heat_data, radius=32, blur=15, min_opacity=0.4, max_zoom=8, name="Earthquake Heatmap")
# Add the marker cluster layer
map.add_child(marker_cluster)
# Add the heatmap layer
map.add_child(heat_map)

map.add_child(MiniMap())
map.add_child(folium.LayerControl()) 
map.add_child(Fullscreen(
    position="topright",
    title="Enter Fullscreen",
    title_cancel="Exit Fullscreen",
    force_separate_button=True,
))
# Save to HTML
map.save("earthquake_map.html")
print("Map saved as 'earthquake_map.html'")