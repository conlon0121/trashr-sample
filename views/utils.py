def get_layer(dumpsters):
    features = []
    lat = 0
    long = 0
    for dumpster in dumpsters:
        fill = dumpster.percent_fill
        d_lat = float(dumpster.coordinates[0])
        d_long = float(dumpster.coordinates[1])
        lat += d_lat
        long += d_long
        if fill < 30:
            color = "green"
        elif fill > 50:
            color = "red"
        else:
            color = "yellow"
        features.append({
            "type": "Feature",
            "properties": {
                "description": f'{dumpster.address}<br/>'
                               f'<center>{str(fill)}% full</center>',
                "color": color,
                "id": dumpster.id
            },
            "geometry": {
                "type": "Point",
                "coordinates": [d_long, d_lat]
            }
        })
    layer = {
        "id": "dumpsters",
        "type": "symbol",
        "source": {
            "type": "geojson",
            "data": {
                "type": "FeatureCollection",
                "features": features
            }
        },
        "layout": {
            "icon-image": "{color}-waste-basket-15",
            "icon-allow-overlap": True
        }
    }
    try:
        lat = lat / len(features)
        long = long / len(features)
    except ZeroDivisionError:
        pass
    return layer, lat, long