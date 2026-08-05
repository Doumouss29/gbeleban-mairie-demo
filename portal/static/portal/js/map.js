const DEFAULT_CENTER=[9.5846,-8.1318];
const DEFAULT_ZOOM=14;
const map=L.map('map').setView(DEFAULT_CENTER,DEFAULT_ZOOM);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:20,attribution:'© OpenStreetMap'}).addTo(map);
const loaded={};

function popup(props){
  return Object.entries(props||{}).map(([k,v])=>`<div><b>${k}</b> : ${v??''}</div>`).join('');
}

async function addLayer(cb){
  const id=cb.dataset.id;
  if(loaded[id]){
    if(cb.checked) loaded[id].addTo(map);
    else map.removeLayer(loaded[id]);
    return;
  }
  if(!cb.checked) return;

  const data=await fetch(`/api/couches/${id}.geojson`).then(r=>r.json());
  const color=cb.dataset.color||'#ef7d00';
  loaded[id]=L.geoJSON(data,{
    style:{color,weight:2,fillOpacity:.25},
    pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:8,color,fillColor:color,fillOpacity:.85}),
    onEachFeature:(f,l)=>l.bindPopup(popup(f.properties))
  }).addTo(map);

  try{
    const bounds=loaded[id].getBounds();
    if(bounds.isValid()){
      map.fitBounds(bounds,{padding:[35,35],maxZoom:DEFAULT_ZOOM});
    }
  }catch(e){
    map.setView(DEFAULT_CENTER,DEFAULT_ZOOM);
  }
}

document.querySelectorAll('.layer-toggle').forEach(cb=>{
  cb.addEventListener('change',()=>addLayer(cb));
  if(cb.checked) addLayer(cb);
});
