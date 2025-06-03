import folium
import requests
from folium.plugins import MarkerCluster, HeatMap, MiniMap, Fullscreen
from datetime import datetime

# ------------------------------
# Helper function to add a layer
# ------------------------------
def add_earthquake_layer(geojson_url, layer_name, map_obj,
                         color_for_mag, radius_factor=2, 
                         heatmap_radius=32, heatmap_blur=15):
    """
    Fetches earthquake data from a USGS GeoJSON URL, then:
      - Creates a MarkerCluster of CircleMarkers
      - Creates a HeatMap of the same points
      - Adds both to a FeatureGroup named `layer_name`

    Arguments:
      geojson_url    : URL to a USGS GeoJSON feed
      layer_name     : str name for the FeatureGroup/layer
      map_obj        : folium.Map object to which layers will be attached
      color_for_mag  : function(magnitude) -> color-string
      radius_factor  : float multiplier for circle radius (default 2)
      heatmap_radius : int for HeatMap point radius (default 32)
      heatmap_blur   : int for HeatMap blur (default 15)
    """
    # Fetch the GeoJSON
    resp = requests.get(geojson_url)
    data = resp.json()

    # Create a FeatureGroup so that we can toggle on/off
    fg = folium.FeatureGroup(name=layer_name)

    # MarkerCluster inside this feature group
    mc = MarkerCluster()
    fg.add_child(mc)

    # Prepare heatmap data list
    heat_data = []

    for feature in data['features']:
        coords = feature['geometry']['coordinates']  # [lon, lat, depth]
        props = feature['properties']

        mag = props.get('mag') or 0.0
        place = props.get('place', 'Unknown')
        timestamp_ms = props.get('time', 0)
        # Convert to UTC string
        time_str = datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
        depth = coords[2]

        # Popup HTML
        popup_html = (
            f"<b>Location:</b> {place}<br>"
            f"<b>Magnitude:</b> {mag}<br>"
            f"<b>Depth:</b> {depth} km<br>"
            f"<b>Time:</b> {time_str}"
        )

        # Decide circle color based on mag
        circle_color = color_for_mag(mag)

        # Add CircleMarker to the MarkerCluster
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=max(mag * radius_factor, 3),
            popup=popup_html,
            color=circle_color,
            fill=True,
            fill_color=circle_color,
            fill_opacity=0.7,
            weight=1
        ).add_to(mc)

        # Append to heat_data: [lat, lon, weight]
        heat_data.append([coords[1], coords[0], mag])

    # Create HeatMap layer and add it to the same FeatureGroup
    hm = HeatMap(
        heat_data,
        radius=heatmap_radius,
        blur=heatmap_blur,
        min_opacity=0.4,
        max_zoom=8
    )
    fg.add_child(hm)

    # Finally add this FeatureGroup to the map
    map_obj.add_child(fg)


# ---------------------------------------
# Main: build map and add “real-time” layer
# plus “historical” (past-30 days) layer
# ---------------------------------------
if __name__ == "__main__":
    # Base map centered on Europe / Slovakia
    m = folium.Map(
        location=[48.291697, 17.755778],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    # Define color‐mapping functions for each layer
    def color_day(mag):
        # Past-day: red/orange/green
        return 'red' if mag >= 5 else 'orange' if mag >= 3 else 'green'

    def color_month(mag):
        # Past-30 days: darker colors, slightly smaller radius etc.
        return 'darkred' if mag >= 6 else 'darkorange' if mag >= 4 else 'darkgreen'

    # 1) Past‐Day Earthquakes (real-time layer)
    url_day = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    add_earthquake_layer(
        geojson_url=url_day,
        layer_name="Past Day Earthquakes",
        map_obj=m,
        color_for_mag=color_day,
        radius_factor=2,         # same as before
        heatmap_radius=32,
        heatmap_blur=15
    )

    # 2) Past‐30 Days Earthquakes (historical layer)
    url_month = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
    add_earthquake_layer(
        geojson_url=url_month,
        layer_name="Past 30 Days (History)",
        map_obj=m,
        color_for_mag=color_month,
        radius_factor=1.5,       # slightly smaller markers
        heatmap_radius=24,       # slightly smaller heatmap radius
        heatmap_blur=12
    )

    # Add MiniMap, Fullscreen, and LayerControl
    m.add_child(MiniMap())
    m.add_child(Fullscreen(
        position="topright",
        title="Enter Fullscreen",
        title_cancel="Exit Fullscreen",
        force_separate_button=True,
    ))
    m.add_child(folium.plugins.LocateControl())
    m.add_child(folium.plugins.Geocoder(position="bottomleft"))

    # This adds checkboxes to toggle “Past Day Earthquakes” vs “Past 30 Days (History)”
    m.add_child(folium.LayerControl())

    # Save to HTML
    m.save("earthquake_map_with_history.html")
    print("Map saved as 'earthquake_map_with_history.html'")
