import os
import requests
import numpy as np
import plotly.graph_objects as go
from skyfield.api import load, EarthSatellite
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("N2YO_API_KEY") 

if not API_KEY:
    raise ValueError("🚨 ERROR: No se ha encontrado la API Key. Comprueba tu archivo .env")

SATELITES = {
    "ISS (Estación Espacial)": {"id": 25544, "color": "#00ffcc"},
    "Telescopio Hubble": {"id": 20580, "color": "#ff3366"},
    "NOAA-18 (Clima)": {"id": 28654, "color": "#ffcc00"},
    "Envisat (Obs. ESA)": {"id": 27386, "color": "#cc33ff"},
    "CryoSat-2 (Hielos)": {"id": 36508, "color": "#ffffff"},
    "Starlink-77 (Internet)": {"id": 45719, "color": "#3399ff"},
    "Landsat 8 (Superficie)": {"id": 39084, "color": "#00ff66"},
    "Galileo PRN 1 (GPS EU)": {"id": 37846, "color": "#ff9933"},
    "Suomi NPP (Clima US)": {"id": 37849, "color": "#ff66b2"}
}

print("inicializando")
ts = load.timescale()
t_ahora = ts.now()

# calculo 90 minutos hacia el futuro -> (una orbita baja estándar)
minutos_futuros = np.arange(0, 90, 1) 
tiempos_proyectados = ts.utc(
    t_ahora.utc.year, t_ahora.utc.month, t_ahora.utc.day, 
    t_ahora.utc.hour, t_ahora.utc.minute + minutos_futuros
)

fig = go.Figure()


for nombre, info in SATELITES.items():
    url = f"https://api.n2yo.com/rest/v1/satellite/tle/{info['id']}&apiKey={API_KEY}"
    
    try:
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            
            tle_raw = datos['tle']
            if '\r\n' in tle_raw:
                tle_lines = tle_raw.split('\r\n')
            else:
                tle_lines = tle_raw.split('\n')
                
            sat_fisico = EarthSatellite(tle_lines[0], tle_lines[1], nombre, ts)
            
            geocentrico = sat_fisico.at(tiempos_proyectados)
            subpunto = geocentrico.subpoint()
            
            lats = subpunto.latitude.degrees
            lons = subpunto.longitude.degrees
            altitud_actual = sat_fisico.at(t_ahora).subpoint().elevation.km
            
            print(f"telemetría asegurada: {nombre}")
            

            # orbitas
            fig.add_trace(go.Scattergeo(
                name=nombre,
                lat=lats,
                lon=lons,
                mode='lines',
                line=dict(width=1.5, color=info['color']),
                opacity=0.25, 
                legendgroup=nombre, 
                showlegend=False,
                hoverinfo='skip'
            ))

            # B) posición actual
            fig.add_trace(go.Scattergeo(
                name=nombre,
                lat=[lats[0]], 
                lon=[lons[0]],
                mode='markers',
                marker=dict(size=8, color=info['color'], symbol='circle',
                            line=dict(width=1.5, color='#050505')),
                legendgroup=nombre,
                hovertemplate=f"<span style='font-family:Courier New;'><b>{nombre}</b><br>Altitud: {altitud_actual:.1f} km<br>Lat: {lats[0]:.2f} / Lon: {lons[0]:.2f}</span><extra></extra>"
            ))
            
        else:
            print(f"Error servidor N2YO con {nombre}.")
    except Exception as e:
        print(f"Fallo de cálculo con {nombre}: {e}")


fig.update_geos(
    projection_type="orthographic",
    showcoastlines=True, coastlinecolor="#2E3440", 
    showland=True, landcolor="#1B222C",          
    showocean=True, oceancolor="#0B101E", 
    showlakes=False,
    showcountries=True, countrycolor="#262E3B",  
    lataxis_showgrid=True, lataxis_gridcolor="#161C28", 
    lonaxis_showgrid=True, lonaxis_gridcolor="#161C28",
    bgcolor="#07090F"                        
)

fig.update_layout(
    title_text="<br><b>Cartografia Orbital</b>",
    title_font=dict(size=22, color="#E5E9F0", family="Trebuchet MS, Arial, sans-serif"), 
    title_x=0.02, 
    paper_bgcolor="#07090F", 
    font=dict(family="Trebuchet MS, Arial, sans-serif", color="#A3ADC2"), 
    margin=dict(l=0, r=0, t=50, b=0),
    legend=dict(
        title="<b>  FLOTA AEROESPACIAL</b>",
        yanchor="middle", y=0.5,
        xanchor="right", x=0.98,
        bgcolor="rgba(18, 24, 38, 0.7)", 
        bordercolor="#3B4252", borderwidth=1,
        font=dict(size=12, color="#D8DEE9")
    )
)

fig.show()