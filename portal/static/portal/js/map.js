const DEFAULT_CENTER=[-8.1318,9.5846];
const DEFAULT_ZOOM=15;
let is3D=true;
const loadedLayers={};

const map=new maplibregl.Map({
  container:'map',
  center:DEFAULT_CENTER,
  zoom:DEFAULT_ZOOM,
  pitch:52,
  bearing:-18,
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
    map.addLayer({id:ids[0],type:'fill',source:sourceId(id),paint:{'fill-color':color,'fill-opacity':0.30}});
    map.addLayer({id:ids[1],type:'line',source:sourceId(id),paint:{'line-color':color,'line-width':2}});
  }else if(type.includes('Line')){
    map.addLayer({id:ids[1],type:'line',source:sourceId(id),paint:{'line-color':color,'line-width':3}});
  }else{
    map.addLayer({id:ids[2],type:'circle',source:sourceId(id),paint:{'circle-radius':7,'circle-color':color,'circle-stroke-color':'#fff','circle-stroke-width':2}});
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
  const kind=(tags.amenity||tags.office||tags.government||tags.type_bat||'').toLowerCase();
  if(kind.includes('school')||kind.includes('education'))return '#ef7d00';
  if(kind.includes('hospital')||kind.includes('clinic')||kind.includes('health'))return '#c63b32';
  if(kind.includes('police')||kind.includes('security'))return '#335f9e';
  if(kind.includes('market'))return '#a16b24';
  return '#056b3c';
}

function rectangleFeature(name,type,lon,lat,widthDeg,heightDeg,heightM){
  const x=widthDeg/2,y=heightDeg/2;
  return {
    type:'Feature',
    geometry:{type:'Polygon',coordinates:[[[lon-x,lat-y],[lon+x,lat-y],[lon+x,lat+y],[lon-x,lat+y],[lon-x,lat-y]]]},
    properties:{
      name,
      type_bat:type,
      _height:heightM,
      _color:adminColor({type_bat:type}),
      _indicative:true
    }
  };
}

function indicativeBuildings(){
  // Maquette volontairement indicative pour visualiser le potentiel 3D.
  // Les emprises/positions exactes seront remplacées lorsqu'une donnée terrain ou SIG fiable sera disponible.
  return [
    rectangleFeature('Mairie de Gbéléban','government',-8.13182,9.58462,0.00024,0.00015,8),
    rectangleFeature('Centre de santé de Gbéléban','health',-8.13095,9.58425,0.00028,0.00016,8),
    rectangleFeature('École maternelle','education',-8.13272,9.58518,0.00026,0.00014,6),
    rectangleFeature('École primaire','education',-8.13325,9.58485,0.00034,0.00016,7),
    rectangleFeature('Collège / lycée moderne','education',-8.12995,9.58515,0.00042,0.00020,9),
    rectangleFeature('Équipement de sécurité','security',-8.13215,9.58372,0.00022,0.00014,6),
    rectangleFeature('Marché / équipement économique','market',-8.13055,9.58358,0.00038,0.00020,5)
  ];
}

function addBuildingsToMap(features,sourceLabel){
  const data={type:'FeatureCollection',features};
  map.addSource('admin-buildings',{type:'geojson',data});
  map.addLayer({
    id:'admin-buildings-3d',type:'fill-extrusion',source:'admin-buildings',
    paint:{
      'fill-extrusion-color':['coalesce',['get','_color'],'#056b3c'],
      'fill-extrusion-height':['coalesce',['to-number',['get','_height']],6],
      'fill-extrusion-base':0,
      'fill-extrusion-opacity':0.90
    }
  });
  map.addLayer({
    id:'admin-buildings-labels',type:'symbol',source:'admin-buildings',
    layout:{
      'text-field':['coalesce',['get','name'],['get','nom'],'Bâtiment public'],
      'text-size':12,
      'text-anchor':'bottom',
      'text-offset':[0,-0.6],
      'text-allow-overlap':false
    },
    paint:{'text-color':'#173d2f','text-halo-color':'#ffffff','text-halo-width':2}
  });
  map.on('click','admin-buildings-3d',e=>{
    const f=e.features?.[0];if(!f)return;
    const p=f.properties||{};
    const indicative=String(p._indicative)==='true';
    const html=`<div class="building-popup"><strong>${escapeHtml(p.name||p.nom||'Bâtiment public')}</strong><div>Type : ${escapeHtml(p.amenity||p.type_bat||p.office||'Équipement public')}</div><div>Hauteur 3D : ${escapeHtml(p._height||6)} m</div>${indicative?'<div class="building-indicative">Maquette indicative — position et emprise à confirmer.</div>':''}</div>`;
    new maplibregl.Popup({maxWidth:'320px'}).setLngLat(e.lngLat).setHTML(html).addTo(map);
  });
  map.on('mouseenter','admin-buildings-3d',()=>map.getCanvas().style.cursor='pointer');
  map.on('mouseleave','admin-buildings-3d',()=>map.getCanvas().style.cursor='');
  const help=document.querySelector('.websig-3d-help');
  if(help)help.textContent=sourceLabel;
}

async function loadAdministrativeBuildings(){
  const query=`[out:json][timeout:20];(
    way(around:3500,9.5846,-8.1318)["building"]["amenity"~"townhall|school|hospital|clinic|police|marketplace"];
    way(around:3500,9.5846,-8.1318)["building"]["office"="government"];
    way(around:3500,9.5846,-8.1318)["building"]["government"];
    way(around:3500,9.5846,-8.1318)["building"]["name"~"Mairie|Sous-préfecture|Préfecture|Gendarmerie|Police|École|EPP|Collège|Lycée|Hôpital|Centre de santé|Marché",i];
  );out tags geom;`;
  let osmFeatures=[];
  try{
    const r=await fetch('https://overpass-api.de/api/interpreter',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:'data='+encodeURIComponent(query)});
    if(!r.ok)throw new Error('Overpass indisponible');
    const json=await r.json();
    osmFeatures=(json.elements||[]).filter(el=>el.type==='way'&&Array.isArray(el.geometry)&&el.geometry.length>=4).map(el=>{
      const coords=el.geometry.map(p=>[p.lon,p.lat]);
      if(coords.length&&JSON.stringify(coords[0])!==JSON.stringify(coords[coords.length-1]))coords.push(coords[0]);
      const tags=el.tags||{};
      return {type:'Feature',geometry:{type:'Polygon',coordinates:[coords]},properties:{...tags,_height:estimatedHeight(tags),_color:adminColor(tags),nom:tags.name||'Bâtiment public',_indicative:false}};
    });
  }catch(err){
    osmFeatures=[];
  }

  if(osmFeatures.length>=3){
    addBuildingsToMap(osmFeatures,'Bâtiments publics détectés dans les données ouvertes. Les hauteurs absentes sont estimées.');
  }else{
    addBuildingsToMap(indicativeBuildings(),'Maquette 3D indicative pour visualiser les principaux équipements. Les positions et emprises exactes seront affinées avec des données SIG ou terrain.');
  }
}

function set3D(enabled){
  is3D=enabled;
  map.easeTo({pitch:enabled?52:0,bearing:enabled?-18:0,zoom:enabled?15:14,duration:700});
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
      ['admin-buildings-3d','admin-buildings-labels'].forEach(id=>{
        if(map.getLayer(id))map.setLayoutProperty(id,'visibility',adminToggle.checked?'visible':'none');
      });
    });
  }
  const btn=document.getElementById('toggle-3d');
  if(btn){
    btn.classList.add('active');
    btn.setAttribute('aria-pressed','true');
    btn.addEventListener('click',()=>set3D(!is3D));
  }
});
