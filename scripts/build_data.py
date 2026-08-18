import json, math

CENTER_LAT, CENTER_LON, ZOOM, IMG = 40.7425, -74.0025, 13, 1400

def lonToX(lon, zoom):
    return (lon + 180) / 360 * 256 * (2 ** zoom)

def latToY(lat, zoom):
    s = math.sin(lat * math.pi / 180)
    return (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * 256 * (2 ** zoom)

CX, CY = lonToX(CENTER_LON, ZOOM), latToY(CENTER_LAT, ZOOM)

def pct(lat, lon):
    x = IMG / 2 + (lonToX(lon, ZOOM) - CX)
    y = IMG / 2 + (latToY(lat, ZOOM) - CY)
    return round(x / IMG * 100, 3), round(y / IMG * 100, 3)

# (day 'YYYY-MM-DD' or 'tbd', zone, category, name, cost or None, schedule, lat, lon or None, notes or None)
RAW = [
("2026-09-16","Midtown","landmark","Times Square",0,"Horario libre",40.7580,-73.9855,None),
("2026-09-16","Midtown","bakery","Carlo's Bakery",7,"6am–10pm",40.7577,-73.9822,None),
("2026-09-16","Midtown","streetfood","Shake Shack (Times Square)",15,"Horario libre",40.7580,-73.9880,"Comida cercana a Times Square"),
("2026-09-16","Midtown","shopping","Fifth Avenue",0,"Horario libre",40.7549,-73.9840,None),
("2026-09-16","Midtown","museum","NY Public Library",0,"10am–6pm",40.7532,-73.9822,None),
("2026-09-16","Midtown","landmark","St. Patrick's Cathedral",0,"7am–8pm",40.7585,-73.9760,None),
("2026-09-16","Midtown","landmark","Rockefeller Center",0,"Consulta horario",40.7587,-73.9787,None),
("2026-09-16","Midtown","landmark","Trump Tower",0,"Acceso público limitado",40.7625,-73.9739,None),
("2026-09-16","Midtown","landmark","Grand Central Terminal",0,"Consulta horario",40.7527,-73.9772,None),
("2026-09-16","Midtown","landmark","Madison Square Garden",0,"Consulta horario",40.7505,-73.9934,None),

("2026-09-17","Central Park & UES","park","Central Park – Sheep Meadow",0,"6am–1am",40.7712,-73.9739,None),
("2026-09-17","Central Park & UES","park","Central Park – The Great Lawn",0,"6am–1am",40.7813,-73.9646,None),
("2026-09-17","Central Park & UES","park","Central Park – Strawberry Fields",0,"6am–1am",40.7756,-73.9756,None),
("2026-09-17","Central Park & UES","streetfood","The Halal Guys",12,"Horario libre",40.7620,-73.9793,None),
("2026-09-17","Central Park & UES","museum","The MET",30,"10am–5pm",40.7794,-73.9632,None),

("2026-09-18","Midtown","museum","MoMA",30,"10:30am–5:30pm",40.7614,-73.9776,"Estudiante $17"),
("2026-09-18","Midtown","restaurant","Pret A Manger",12,"Horario libre",40.7608,-73.9765,None),
("2026-09-18","Midtown","landmark","Empire State Building",0,"10am–11pm","","", None),

("2026-09-19","Upper West Side","museum","American Museum of Natural History",37,"10am–5:30pm",40.7813,-73.9740,"Estudiante $30"),
("2026-09-19","Upper West Side","streetfood","Shake Shack (UWS)",15,"Horario libre",40.7797,-73.9754,None),

("2026-09-20","Financial District","landmark","Wall Street / NYSE",0,"Horario libre",40.7069,-74.0113,None),
("2026-09-20","Financial District","restaurant","Eataly Downtown",18,"Horario libre",40.7127,-74.0134,None),
("2026-09-20","Financial District","landmark","Charging Bull",0,"Horario libre",40.7056,-74.0134,None),
("2026-09-20","Financial District","landmark","Federal Hall",0,"Horario libre",40.7071,-74.0104,None),
("2026-09-20","Financial District","landmark","Federal Reserve Bank",0,"Horario libre",40.7079,-74.0092,None),
("2026-09-20","Financial District","landmark","Stone Street",0,"Horario libre",40.7038,-74.0106,None),
("2026-09-20","Financial District","landmark","Ground Zero / 9-11 Memorial",0,"Horario libre",40.7115,-74.0134,None),
("2026-09-20","Harbor","landmark","Statue of Liberty",0,"8:30am–4pm","","", None),
("2026-09-20","Financial District","transit","Staten Island Ferry (opción gratis)",0,"Consulta horario",40.7013,-74.0136,"Barco naranja, gratis"),
("2026-09-20","Financial District","transit","Castle Clinton (opción 2)",25,"Consulta horario",40.7033,-74.0170,"Alternativa pagada a la Estatua"),

("2026-09-21","Brooklyn","landmark","Brooklyn Bridge",0,"Horario libre",40.7061,-73.9969,None),
("2026-09-21","Brooklyn","restaurant","Juliana's Pizza",20,"Horario libre",40.7028,-73.9932,None),
("2026-09-21","Brooklyn","landmark","DUMBO",0,"Horario libre",40.7033,-73.9903,None),
("2026-09-21","Chelsea & Hudson Yards","landmark","The Vessel",0,"11am–7pm",40.7538,-74.0022,None),
("2026-09-21","Chelsea & Hudson Yards","park","Little Island",0,"6am–12am",40.7420,-74.0106,None),
("2026-09-21","Chelsea & Hudson Yards","park","High Line Park",0,"7am–10pm",40.7473,-74.0034,None),
("2026-09-21","Chelsea & Hudson Yards","park","Pier 57 Rooftop Park",0,"6am–1am",40.7440,-74.0090,"Vista a NY"),
("2026-09-21","Lower East Side","park","Pier 35",0,"6am–12am",40.7115,-73.9873,"Vista a NY"),

("2026-09-22","Lower East Side","landmark","Chinatown",0,"Horario libre",40.7158,-73.9970,None),
("2026-09-22","Lower East Side","restaurant","Joe's Shanghai",15,"Horario libre",40.7147,-73.9986,None),
("2026-09-22","Fuera de NYC","shopping","Woodbury Common Outlet",0,"10am–9pm","","", "A ~1h de NYC, fuera del mapa"),
("2026-09-22","Fuera de NYC","streetfood","Food court del Outlet",12,"Horario libre","","", None),
("2026-09-22","Midtown","show","Evento deportivo (MSG)",25,"10am–4pm",40.7505,-73.9934,None),
("2026-09-22","Midtown","show","Broadway: Aladdin",30,"7:00pm",40.7563,-73.9877,"New Amsterdam Theatre"),

("2026-09-23","—","landmark","Salida / regreso",0,"Consulta horario","","", None),

("tbd","Roosevelt Island","transit","Roosevelt Island Tramway",None,"Consulta horario",40.7576,-73.9627,"Sin confirmar en el itinerario original"),
]

rows = []
for i,(day,zone,cat,name,cost,sched,lat,lon,notes) in enumerate(RAW):
    has_geo = lat != "" and lon != ""
    x = y = None
    if has_geo:
        x,y = pct(float(lat), float(lon))
    rows.append({
        "order_index": i,
        "day": day,
        "zone": zone,
        "category": cat,
        "name": name,
        "cost": cost,
        "schedule": sched,
        "lat": float(lat) if has_geo else None,
        "lon": float(lon) if has_geo else None,
        "x_pct": x,
        "y_pct": y,
        "notes": notes,
    })

with open("pois_seed.json","w") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

print(f"{len(rows)} POIs procesados")
print(f"Sin coordenadas (fuera de mapa): {sum(1 for r in rows if r['x_pct'] is None)}")
