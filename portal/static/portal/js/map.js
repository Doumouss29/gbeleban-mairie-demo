const DEFAULT_CENTER=[-8.1318,9.5846];
const DEFAULT_ZOOM=14;
let is3D=false;
const loadedLayers={};

const map=new maplibregl.Map({
  container:'map',
  center:DEFAULT_CENTER,
  zoom:DEFAULT_ZOOM,
  pitch:0,
  bearing:0,
  attributionControl:true,
  style:{
    version:8,
    sources:{
      osm:{
        type:'raster',
        tiles:['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png','https://b.tile.openstreetmap.org/{z}/{x}/{y}.png','https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize:256,
        attribution:'© OpenStreetMap contributors'
      }
    },
    layers:[{id:'osm',type:'raster',source:'osm'}]
  }
});
map.addControl(new maplibregl.NavigationControl({visualizePitch:true}),'top-right');
map.addControl(new maplibregl.ScaleControl({maxWidth:120,unit:'metric'}));

function escapeHtml(value){
  return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}
function popupHtml(props){
  return Object.entries(props||{}).filter(([k])=>!String(k).startsWith('_')).map(([k,v])=>`<div><b>${escapeHtml(k)}</b> : ${escapeHtml(v)}</div>`).join('');
}
function geometryType(data){
  const f=(data.features||[]).find(x=>x.geometry);
  return f?.geometry?.type||'';
}
function sourceId(id){return `municipal-source-${id}`;}
function layerIds(id){return [`municipal-fill-${id}`,`municipal-line-${id}`,`municipal-point-${id}`];}

function addMunicipalLayer(id,data,color){
  if(map.getSource(sourceId(id))) return;
  map.addSource(sourceId(id),{type:'geojson',data});
  const type=geometryType(data);
  const ids=layerIds(id);

  if(type.includes('Polygon')){
    map.addLayer({
      id:ids[0],type:'fill',source:sourceId(id),
      paint:{'fill-color':color,'fill-opacity':0.30}
    });
    map.addLayer({
      id:ids[1],type:'line',source:sourceId(id),
      paint:{'line-color':color,'line-width':2}
    });
  }else if(type.includes('Line')){
    map.addLayer({
      id:ids[1],type:'line',source:sourceId(id),
      paint:{'line-color':color,'line-width':3}
    });
  }else{
    map.addLayer({
      id:ids[2],type:'circle',source:sourceId(id),
      paint:{'circle-radius':7,'circle-color':color,'circle-stroke-color':'#fff','circle-stroke-width':2}
    });
  }

  ids.filter(x=>map.getLayer(x)).forEach(layerId=>{
    map.on('click',layerId,e=>{
      const f=e.features?.[0];
      if(!f)return;
      new maplibregl.Popup({maxWidth:'340px'}).setLngLat(e.lngLat).setHTML(popupHtml(f.properties)).addTo(map);
    });
    map.on('mouseenter',layerId,()=>map.getCanvas().style.cursor='pointer');
    map.on('mouseleave',layerId,()=>map.getCanvas().style.cursor='');
  });

  loadedLayers[id]=ids;
}

async function toggleMunicipalLayer(cb){
  const id=cb.dataset.id;
  const color=cb.dataset.color||'#ef7d00';
  if(!loadedLayers[id]){
    if(!cb.checked)return;
    const data=await fetch(`/api/couches/${id}.geojson`).then(r=>r.json());
    addMunicipalLayer(id,data,color);
  }
  (loadedLayers[id]||[]).forEach(layerId=>{
    if(map.getLayer(layerId))map.setLayoutProperty(layerId,'visibility',cb.checked?'visible':'none');
  });
}

function estimatedHeight(tags){
  const direct=parseFloat(tags.height);
  if(Number.isFinite(direct))return Math.max(3,direct);
  const levels=parseFloat(tags['building:levels']);
  if(Number.isFinite(levels))return Math.max(3,levels*3.4);
  const kind=(tags.amenity||tags.office||tags.government||'').toLowerCase();
  if(kind.includes('hospital'))return 10;
  if(kind.includes('school'))return 7;
  if(kind.includes('townhall')||kind.includes('government'))return 8;
  if(kind.includes('police'))return 6;
  if(kind.includes('market'))return 5;
  return 6;
}
function adminColor(tags){
  const kind=(tags.amenity||tags.office||tags.government||'').toLowerCase();
  if(kind.includes('school'))return '#ef7d00';
  if(kind.includes('hospital')||kind.includes('clinic'))return '#c63b32';
  if(kind.includes('police'))return '#335f9e';
  if(kind.includes('market'))return '#a16b24';
  return '#056b3c';
}

async function loadAdministrativeBuildings(){
  const query=`[out:json][timeout:25];(
    way(around:3000,9.5846,-8.1318)["building"]["amenity"~"townhall|school|hospital|clinic|police|marketplace"];
    way(around:3000,9.5846,-8.1318)["building"]["office"="government"];
    way(around:3000,9.5846,-8.1318)["building"]["government"];
    way(around:3000,9.5846,-8.1318)["building"]["name"~"Mairie|Sous-préfecture|Préfecture|Gendarmerie|Police|École|Collège|Lycée|Hôpital|Centre de santé|Marché",i];
  );out tags geom;`;
  try{
    const r=await fetch('https://overpass-api.de/api/interpreter',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:'data='+encodeURIComponent(query)});
    if(!r.ok)throw new Error('Overpass indisponible');
    const json=await r.json();
    const features=(json.elements||[]).filter(el=>el.type==='way'&&Array.isArray(el.geometry)&&el.geometry.length>=4).map(el=>{
      const coords=el.geometry.map(p=>[p.lon,p.lat]);
      if(coords.length&&JSON.stringify(coords[0])!==JSON.stringify(coords[coords.length-1]))coords.push(coords[0]);
      const tags=el.tags||{};
      return {type:'Feature',geometry:{type:'Polygon',coordinates:[coords]},properties:{...tags,_height:estimatedHeight(tags),_color:adminColor(tags),nom:tags.name||'Bâtiment public'}};
    });
    const data={type:'FeatureCollection',features};
    map.addSource('admin-buildings',{type:'geojson',data});
    map.addLayer({
      id:'admin-buildings-3d',
      type:'fill-extrusion',
      source:'admin-buildings',
      paint:{
        'fill-extrusion-color':['coalesce',['get','_color'],'#056b3c'],
        'fill-extrusion-height':['coalesce',['to-number',['get','_height']],6],
        'fill-extrusion-base':0,
        'fill-extrusion-opacity':0.88
      }
    });
    map.on('click','admin-buildings-3d',e=>{
      const f=e.features?.[0];if(!f)return;
      const p=f.properties||{};
      const html=`<div class="building-popup"><strong>${escapeHtml(p.name||p.nom||'Bâtiment public')}</strong>${p.amenity?`<div>Type : ${escapeHtml(p.amenity)}</div>`:''}${p.office?`<div>Service : ${escapeHtml(p.office)}</div>`:''}<div>Hauteur 3D : ${escapeHtml(p._height||6)} m <small>(réelle ou estimée)</small></div></div>`;
      new maplibregl.Popup({maxWidth:'320px'}).setLngLat(e.lngLat).setHTML(html).addTo(map);
    });
    map.on('mouseenter','admin-buildings-3d',()=>map.getCanvas().style.cursor='pointer');
    map.on('mouseleave','admin-buildings-3d',()=>map.getCanvas().style.cursor='');
  }catch(err){
    const help=document.querySelector('.websig-3d-help');
    if(help)help.textContent='Les emprises publiques 3D ne sont pas disponibles pour le moment. Les couches municipales restent accessibles.';
  }
}

function set3D(enabled){
  is3D=enabled;
  map.easeTo({pitch:enabled?55:0,bearing:enabled?-18:0,duration:700});
  const btn=document.getElementById('toggle-3d');
  if(btn){btn.classList.toggle('active',enabled);btn.setAttribute('aria-pressed',enabled?'true':'false');}
}

map.on('load',async()=>{
  document.querySelectorAll('.layer-toggle').forEach(cb=>{
    cb.addEventListener('change',()=>toggleMunicipalLayer(cb));
    if(cb.checked)toggleMunicipalLayer(cb);
  });
  await loadAdministrativeBuildings();
  const adminToggle=document.getElementById('admin-buildings-toggle');
  if(adminToggle){
    adminToggle.addEventListener('change',()=>{
      if(map.getLayer('admin-buildings-3d'))map.setLayoutProperty('admin-buildings-3d','visibility',adminToggle.checked?'visible':'none');
    });
  }
  const btn=document.getElementById('toggle-3d');
  if(btn)btn.addEventListener('click',()=>set3D(!is3D));
});
